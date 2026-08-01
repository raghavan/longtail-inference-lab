"""Single-host, one-attempt execution ledger for the frozen measured sequence."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import stat
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Mapping, Sequence

from .preregistration import (
    FREEZE_PATH,
    PROJECT_ROOT,
    PreregistrationError,
    load_freeze,
    validate_landed_freeze_revision,
)
from .sanitize import sha256_file

LEDGER_SCHEMA = "terminal-artifact-memory-execution-ledger-v1"
LEDGER_ENV = "ARTIFACT_MEMORY_EXECUTION_LEDGER"
LEDGER_FILENAME = "execution-ledger.v1.json"
LOCK_FILENAME = ".execution-ledger.v1.lock"
ANCHOR_FILENAME = "terminal-artifact-memory-2026-08-01-ledger-anchor"
EXPERIMENT_ID = "2026-08-01-gpt56-qwen32k-teacher-student"


class ExecutionLedgerError(RuntimeError):
    """Raised when an attempt differs from the one frozen global sequence."""


def _sequence() -> list[dict[str, object]]:
    freeze = load_freeze()
    ordering = freeze.get("ordering")
    if not isinstance(ordering, Mapping):
        raise ExecutionLedgerError("freeze ordering is unavailable")
    phases = (
        ("M0", ordering.get("m0")),
        ("teacher", ordering.get("teacher_builds")),
        ("distiller", ordering.get("distillation_and_admission")),
        ("M2", ordering.get("m2")),
    )
    output: list[dict[str, object]] = []
    for phase, tasks in phases:
        if not isinstance(tasks, list) or not all(isinstance(task, str) for task in tasks):
            raise ExecutionLedgerError(f"freeze ordering is invalid for {phase}")
        output.extend(
            {
                "phase": phase,
                "task_id": task,
                "status": "pending",
                "attempt_count": 0,
                "artifact_sha256": None,
            }
            for task in tasks
        )
    return output


def _anchor_path() -> Path:
    completed = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode or not completed.stdout.strip():
        raise ExecutionLedgerError("Git common directory is unavailable for ledger anchoring")
    common = Path(completed.stdout.strip())
    if not common.is_absolute():
        common = (PROJECT_ROOT / common).resolve()
    return common / ANCHOR_FILENAME


def _path_identity(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()


def _write_all(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise ExecutionLedgerError("durable ledger write made no progress")
        view = view[written:]


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _create_anchor(path: Path) -> None:
    anchor = _anchor_path()
    identity = (_path_identity(path) + "\n").encode()
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(anchor, flags, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.getuid():
            raise ExecutionLedgerError("checkout-wide ledger anchor is not a user-owned file")
        os.fchmod(descriptor, 0o600)
        os.lseek(descriptor, 0, os.SEEK_SET)
        existing = os.read(descriptor, 4096)
        if existing and existing != identity:
            raise ExecutionLedgerError("another ledger path is already anchored for this checkout")
        if not existing:
            os.lseek(descriptor, 0, os.SEEK_SET)
            _write_all(descriptor, identity)
            os.ftruncate(descriptor, len(identity))
            os.fsync(descriptor)
            _fsync_directory(anchor.parent)
    finally:
        os.close(descriptor)


def ledger_path() -> Path:
    value = os.environ.get(LEDGER_ENV, "")
    path = Path(value)
    if not value or not path.is_absolute() or path.name != LEDGER_FILENAME:
        raise ExecutionLedgerError(
            f"{LEDGER_ENV} must be an absolute private path ending in {LEDGER_FILENAME}"
        )
    anchor = _anchor_path()
    try:
        anchored_identity = anchor.read_text().strip()
    except OSError as exc:
        raise ExecutionLedgerError("execution ledger has not been anchored after merge") from exc
    if anchored_identity != _path_identity(path):
        raise ExecutionLedgerError("execution ledger path differs from the checkout-wide anchor")
    return path


def initialize(path: Path) -> None:
    if not path.is_absolute() or path.name != LEDGER_FILENAME:
        raise ExecutionLedgerError(f"ledger path must end in {LEDGER_FILENAME}")
    revision = validate_landed_freeze_revision()
    _create_anchor(path)
    document = {
        "schema_version": LEDGER_SCHEMA,
        "experiment_id": EXPERIMENT_ID,
        "freeze_sha256": sha256_file(FREEZE_PATH),
        "code_revision": revision,
        "next_index": 0,
        "attempts": _sequence(),
    }
    lock_descriptor = _open_lock(path)
    try:
        try:
            os.lstat(path)
        except FileNotFoundError:
            pass
        else:
            raise ExecutionLedgerError("refusing to replace an existing execution ledger")
        _atomic_commit(path, document)
    finally:
        os.close(lock_descriptor)


def _open_lock(path: Path) -> int:
    lock_path = path.parent / LOCK_FILENAME
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or metadata.st_nlink != 1
    ):
        os.close(descriptor)
        raise ExecutionLedgerError("execution ledger lock is not a sole-owned regular file")
    os.fchmod(descriptor, 0o600)
    fcntl.flock(descriptor, fcntl.LOCK_EX)
    return descriptor


def _read_locked(path: Path) -> tuple[int, dict[str, object]]:
    lock_descriptor = _open_lock(path)
    try:
        flags = os.O_RDONLY | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or metadata.st_nlink != 1
                or metadata.st_mode & 0o077
            ):
                raise ExecutionLedgerError("execution ledger is not a sole-owned mode-0600 file")
            chunks: list[bytes] = []
            while chunk := os.read(descriptor, 1024 * 1024):
                chunks.append(chunk)
        finally:
            os.close(descriptor)
        value = json.loads(b"".join(chunks))
        if not isinstance(value, dict):
            raise ExecutionLedgerError("execution ledger must be an object")
        return lock_descriptor, value
    except Exception:
        os.close(lock_descriptor)
        raise


def _validate(document: Mapping[str, object]) -> tuple[list[dict[str, object]], int]:
    revision = validate_landed_freeze_revision()
    exact = {
        "schema_version": LEDGER_SCHEMA,
        "experiment_id": EXPERIMENT_ID,
        "freeze_sha256": sha256_file(FREEZE_PATH),
        "code_revision": revision,
    }
    for field, expected in exact.items():
        if document.get(field) != expected:
            raise ExecutionLedgerError(f"execution ledger {field} mismatch")
    attempts = document.get("attempts")
    next_index = document.get("next_index")
    if not isinstance(attempts, list) or type(next_index) is not int:
        raise ExecutionLedgerError("execution ledger attempt state is malformed")
    expected_attempts = _sequence()
    if len(attempts) != len(expected_attempts) or not (0 <= next_index <= len(attempts)):
        raise ExecutionLedgerError("execution ledger sequence length or index mismatch")
    normalized: list[dict[str, object]] = []
    for actual, expected in zip(attempts, expected_attempts, strict=True):
        if not isinstance(actual, dict) or {
            "phase": actual.get("phase"),
            "task_id": actual.get("task_id"),
        } != {
            "phase": expected["phase"],
            "task_id": expected["task_id"],
        }:
            raise ExecutionLedgerError("execution ledger ordering differs from the freeze")
        if set(actual) != {
            "phase",
            "task_id",
            "status",
            "attempt_count",
            "artifact_sha256",
        }:
            raise ExecutionLedgerError("execution ledger attempt fields differ from the contract")
        status_value = actual.get("status")
        state = (actual.get("attempt_count"), actual.get("artifact_sha256"))
        if status_value == "pending" and state != (0, None):
            raise ExecutionLedgerError("pending ledger attempt must be unused and unhashed")
        if status_value == "started" and state != (1, None):
            raise ExecutionLedgerError("started ledger attempt must have one use and no artifact")
        if status_value == "complete" and (
            actual.get("attempt_count") != 1
            or not isinstance(actual.get("artifact_sha256"), str)
            or len(str(actual["artifact_sha256"])) != 64
            or any(ch not in "0123456789abcdef" for ch in str(actual["artifact_sha256"]))
        ):
            raise ExecutionLedgerError("complete ledger attempt requires one use and SHA-256")
        if status_value not in {"pending", "started", "complete"}:
            raise ExecutionLedgerError("execution ledger status is invalid")
        normalized.append(actual)
    if any(item.get("status") != "complete" for item in normalized[:next_index]):
        raise ExecutionLedgerError("execution ledger prefix is not complete")
    if any(item.get("status") != "pending" for item in normalized[next_index + 1 :]):
        raise ExecutionLedgerError("execution ledger future attempts are not pending")
    return normalized, next_index


def _atomic_commit(path: Path, document: Mapping[str, object]) -> None:
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode()
    temp = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temp, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        _write_all(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    try:
        os.replace(temp, path)
        _fsync_directory(path.parent)
    finally:
        temp.unlink(missing_ok=True)


def reserve_attempt(phase: str, task_id: str) -> None:
    path = ledger_path()
    lock_descriptor, document = _read_locked(path)
    try:
        attempts, next_index = _validate(document)
        if next_index >= len(attempts):
            raise ExecutionLedgerError("all frozen attempts are already complete")
        attempt = attempts[next_index]
        if attempt.get("phase") != phase or attempt.get("task_id") != task_id:
            raise ExecutionLedgerError(
                f"next frozen attempt is {attempt.get('phase')}:{attempt.get('task_id')}"
            )
        if attempt.get("status") != "pending" or attempt.get("attempt_count") != 0:
            raise ExecutionLedgerError("frozen attempt was already started; retries are forbidden")
        attempt["status"] = "started"
        attempt["attempt_count"] = 1
        _atomic_commit(path, document)
    finally:
        os.close(lock_descriptor)


def complete_attempt(phase: str, task_id: str, artifact_sha256: str) -> None:
    if len(artifact_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in artifact_sha256):
        raise ExecutionLedgerError("completion artifact hash must be SHA-256")
    path = ledger_path()
    lock_descriptor, document = _read_locked(path)
    try:
        attempts, next_index = _validate(document)
        if next_index >= len(attempts):
            raise ExecutionLedgerError("all frozen attempts are already complete")
        attempt = attempts[next_index]
        if (
            attempt.get("phase") != phase
            or attempt.get("task_id") != task_id
            or attempt.get("status") != "started"
            or attempt.get("attempt_count") != 1
        ):
            raise ExecutionLedgerError("completion does not match the sole in-progress attempt")
        attempt["status"] = "complete"
        attempt["artifact_sha256"] = artifact_sha256
        document["next_index"] = next_index + 1
        _atomic_commit(path, document)
    finally:
        os.close(lock_descriptor)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the frozen one-attempt execution ledger.")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("initialize")
    init.add_argument("--path", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "initialize":
        initialize(args.path)
        print(args.path)
        return 0
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ExecutionLedgerError, PreregistrationError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
