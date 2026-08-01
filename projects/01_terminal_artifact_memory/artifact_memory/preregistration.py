"""Immutable preregistration and private-qualification consistency checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence

from .sanitize import sha256_file
from .verifier_qualification import validate_qualification_path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FREEZE_PATH = PROJECT_ROOT / "manifests" / "preregistration-freeze-2026-08-01.v1.json"
ATTESTATIONS_PATH = (
    PROJECT_ROOT / "manifests" / "verifier-qualification-attestations-2026-08-01.v1.json"
)
FREEZE_SCHEMA = "terminal-artifact-memory-preregistration-freeze-v1"
EXPECTED_SPLIT_REVISION = "gpt56-qwen32k-qualified-transfer-v1"
EXPECTED_TEACHER_ADAPTER = "host-codex-subscription-task-mcp-v1"
EXPECTED_DISTILLER_ADAPTER = "host-codex-subscription-no-tools-v1"
PLACEHOLDER_RE = re.compile(
    r"\b(?:REQUIRED|TBD)(?:_[A-Z0-9_]*)?\b|(?i:\b(?:CHANGEME|PLACEHOLDER)(?:_[A-Za-z0-9_]*)?\b)"
)
TASK_FAMILIES = {
    "configure-git-webserver": "server_configuration",
    "polyglot-rust-c": "source_build",
    "pytorch-model-cli": "model_execution",
}
DEVELOPMENT_TEACHER_TASK_IDS = {"hello-world"}
DEVELOPMENT_TASK_ENVIRONMENT_NAMES = {"hello-world": frozenset({"PATH"})}
TEACHER_AUTHORIZATION_SCHEMA = "measured-teacher-execution-authorization-v1"


class PreregistrationError(ValueError):
    """Raised when a measured record differs from the landed freeze."""


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _load(path: Path, name: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise PreregistrationError(f"{name} is not readable JSON") from exc
    if not isinstance(value, dict):
        raise PreregistrationError(f"{name} must be an object")
    return value


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise PreregistrationError(f"{name} must be an object")
    return value


def _find_placeholders(value: object, path: str = "record") -> list[str]:
    findings: list[str] = []
    if isinstance(value, str) and PLACEHOLDER_RE.search(value):
        findings.append(path)
    elif isinstance(value, Mapping):
        for key, child in value.items():
            findings.extend(_find_placeholders(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_find_placeholders(child, f"{path}[{index}]"))
    return findings


def load_freeze() -> dict[str, object]:
    freeze = _load(FREEZE_PATH, "preregistration freeze")
    if freeze.get("schema_version") != FREEZE_SCHEMA:
        raise PreregistrationError(f"freeze schema must be {FREEZE_SCHEMA}")
    if freeze.get("split_revision") != EXPECTED_SPLIT_REVISION:
        raise PreregistrationError("freeze split revision mismatch")
    placeholders = _find_placeholders(freeze, "freeze")
    if placeholders:
        raise PreregistrationError("freeze contains unresolved markers: " + ", ".join(placeholders))
    return freeze


def _attestations_by_task() -> dict[str, Mapping[str, object]]:
    value = _load(ATTESTATIONS_PATH, "qualification attestations")
    tasks = value.get("tasks")
    if not isinstance(tasks, list):
        raise PreregistrationError("qualification attestations tasks must be a list")
    output: dict[str, Mapping[str, object]] = {}
    for item in tasks:
        record = _mapping(item, "qualification task attestation")
        task_id = str(record.get("task_id", ""))
        if not task_id or task_id in output:
            raise PreregistrationError("qualification task attestations must have unique task IDs")
        if record.get("all_controls_passed") is not True:
            raise PreregistrationError(f"qualification attestation is not eligible: {task_id}")
        output[task_id] = record
    return output


def validate_public_freeze() -> None:
    freeze = load_freeze()
    prompts = _mapping(freeze["prompts"], "freeze prompts")
    expected_files = {
        "teacher_sha256": PROJECT_ROOT / "prompts" / "teacher.v1.md",
        "distiller_sha256": PROJECT_ROOT / "prompts" / "distillation.v1.md",
        "student_system_sha256": PROJECT_ROOT / "prompts" / "system.v1.md",
        "student_memory_sha256": PROJECT_ROOT / "prompts" / "memory.v1.md",
    }
    for field, path in expected_files.items():
        if prompts.get(field) != sha256_file(path):
            raise PreregistrationError(f"freeze {field} does not match {path.name}")
    memory = _mapping(freeze["memory_controls"], "freeze memory controls")
    if memory.get("retrieval_config_sha256") != sha256_file(
        PROJECT_ROOT / "config" / "retrieval.v1.json"
    ):
        raise PreregistrationError("freeze retrieval config hash mismatch")
    tools = _mapping(freeze["tool_pins"], "freeze tool pins")
    if tools.get("python_lock_sha256") != sha256_file(PROJECT_ROOT / "uv.lock"):
        raise PreregistrationError("freeze uv.lock hash mismatch")
    roles = _mapping(freeze["roles"], "freeze roles")
    teacher_role = _mapping(roles["teacher"], "freeze teacher role")
    distiller_role = _mapping(roles["distiller"], "freeze distiller role")
    adapter_attestation_path = PROJECT_ROOT / str(
        teacher_role.get("qualification_attestation", "")
    )
    if teacher_role.get("qualification_attestation_sha256") != sha256_file(
        adapter_attestation_path
    ):
        raise PreregistrationError("freeze adapter qualification attestation hash mismatch")
    source_inventories = (
        _mapping(teacher_role.get("implementation_sha256"), "teacher implementation hashes"),
        _mapping(distiller_role.get("implementation_sha256"), "distiller implementation hashes"),
    )
    for inventory in source_inventories:
        for relative_path, expected_sha256 in inventory.items():
            source_path = PROJECT_ROOT / str(relative_path)
            if expected_sha256 != sha256_file(source_path):
                raise PreregistrationError(
                    f"freeze implementation hash mismatch: {relative_path}"
                )
    attempt_budget = _mapping(freeze["attempt_budget"], "freeze attempt budget")
    if attempt_budget.get("global_execution_ledger_implementation_sha256") != sha256_file(
        PROJECT_ROOT / "artifact_memory" / "execution_ledger.py"
    ):
        raise PreregistrationError("freeze execution ledger implementation hash mismatch")

    split = _mapping(freeze["split"], "freeze split")
    build = split.get("memory_build_task_ids")
    held_out = split.get("held_out_evaluation_task_ids")
    development = split.get("development_context_task_ids")
    if not all(isinstance(value, list) and value for value in (build, held_out, development)):
        raise PreregistrationError("freeze task splits must be nonempty lists")
    if set(build) & set(held_out) or set(build) & set(development) or set(held_out) & set(development):
        raise PreregistrationError("freeze build, held-out, and development tasks must be disjoint")
    attestations = _attestations_by_task()
    if set(attestations) != set(build) | set(held_out):
        raise PreregistrationError("qualification attestations do not exactly cover measured tasks")
    roles = _mapping(freeze["roles"], "freeze roles")
    teacher = _mapping(roles["teacher"], "freeze teacher role")
    inventory = _mapping(
        teacher.get("task_environment_variable_names"),
        "freeze teacher environment inventory",
    )
    if set(inventory) != set(build):
        raise PreregistrationError("teacher environment inventory must cover exact build tasks")
    for task_id, names in inventory.items():
        if (
            not isinstance(names, list)
            or not names
            or not all(isinstance(name, str) and name for name in names)
            or names != sorted(set(names))
        ):
            raise PreregistrationError(
                f"teacher environment inventory is invalid for {task_id}"
            )


def teacher_environment_names(task_id: str) -> frozenset[str]:
    if task_id in DEVELOPMENT_TASK_ENVIRONMENT_NAMES:
        return DEVELOPMENT_TASK_ENVIRONMENT_NAMES[task_id]
    freeze = load_freeze()
    roles = _mapping(freeze["roles"], "freeze roles")
    teacher = _mapping(roles["teacher"], "freeze teacher role")
    inventory = _mapping(
        teacher.get("task_environment_variable_names"),
        "freeze teacher environment inventory",
    )
    names = inventory.get(task_id)
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise PreregistrationError("task has no frozen environment-name inventory")
    return frozenset(names)


def validate_landed_freeze_revision() -> str:
    current_revision = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    status = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    code_revision = current_revision.stdout.strip()
    if current_revision.returncode or not re.fullmatch(r"[0-9a-f]{40}", code_revision):
        raise PreregistrationError("measured execution requires a full checked-out revision")
    if status.returncode or status.stdout.strip():
        raise PreregistrationError("measured execution requires a clean worktree")
    fetched = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "fetch", "--quiet", "--no-tags", "origin", "main"],
        capture_output=True,
        text=True,
        check=False,
    )
    if fetched.returncode:
        raise PreregistrationError("measured gate could not freshly fetch origin/main")
    landed_revision = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "origin/main", "FETCH_HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if (
        landed_revision.returncode
        or landed_revision.stdout.splitlines() != [code_revision, code_revision]
    ):
        raise PreregistrationError(
            "measured revision must equal freshly fetched origin/main and FETCH_HEAD"
        )
    freeze_relative = FREEZE_PATH.relative_to(PROJECT_ROOT.parent.parent).as_posix()
    parent_has_freeze = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "cat-file", "-e", f"{code_revision}^1:{freeze_relative}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if parent_has_freeze.returncode == 0:
        raise PreregistrationError(
            "measured revision is not the landed commit that introduced this freeze"
        )
    return code_revision


def validate_private_qualification_records(records_dir: Path) -> None:
    validate_public_freeze()
    freeze = load_freeze()
    task_source = _mapping(freeze["task_source"], "freeze task source")
    revision = str(task_source["terminal_bench_revision"])
    for task_id, attestation in sorted(_attestations_by_task().items()):
        path = records_dir / f"{task_id}.qualification.json"
        validate_qualification_path(
            path,
            expected_record_sha256=str(attestation["private_qualification_record_sha256"]),
            task_id=task_id,
            terminal_bench_revision=revision,
            task_instruction_sha256=str(attestation["public_instruction_sha256"]),
            task_container_digest=str(attestation["task_container_digest"]),
            verifier_bundle_sha256=str(attestation["verifier_bundle_sha256"]),
        )


def _validate_roles(manifest: Mapping[str, object]) -> None:
    roles = _mapping(manifest.get("roles"), "roles")
    teacher = _mapping(roles.get("teacher"), "roles.teacher")
    distiller = _mapping(roles.get("distiller"), "roles.distiller")
    if teacher.get("provider_runtime_or_operator_adapter") != EXPECTED_TEACHER_ADAPTER:
        raise PreregistrationError("measured teacher adapter differs from the freeze")
    if distiller.get("provider_runtime_or_operator_adapter") != EXPECTED_DISTILLER_ADAPTER:
        raise PreregistrationError("measured distiller adapter differs from the freeze")


def _validate_split(manifest: Mapping[str, object]) -> None:
    freeze = load_freeze()
    frozen_split = _mapping(freeze["split"], "freeze split")
    split = _mapping(manifest.get("split"), "manifest split")
    expected = {
        "revision": EXPECTED_SPLIT_REVISION,
        "memory_build_task_ids": frozen_split["memory_build_task_ids"],
        "held_out_evaluation_task_ids": frozen_split["held_out_evaluation_task_ids"],
    }
    if dict(split) != expected:
        raise PreregistrationError("measured task split differs from the immutable freeze")


def _validate_task_pins(manifest: Mapping[str, object], *, expected_role: str) -> None:
    task = _mapping(manifest.get("task"), "task")
    task_id = str(task.get("task_id", ""))
    attestation = _attestations_by_task().get(task_id)
    if attestation is None or attestation.get("task_role") != expected_role:
        raise PreregistrationError(f"task {task_id!r} is not frozen for {expected_role}")
    run_environment = _mapping(manifest.get("run_environment"), "run_environment")
    instruction_hash = (
        task.get("public_instruction_sha256")
        if expected_role == "memory_build"
        else run_environment.get("task_instruction_sha256")
    )
    exact = {
        "instruction": (instruction_hash, attestation["public_instruction_sha256"]),
        "container": (
            run_environment.get("task_container_digest"),
            attestation["task_container_digest"],
        ),
        "verifier": (task.get("verifier_bundle_sha256"), attestation["verifier_bundle_sha256"]),
        "qualification": (
            task.get("verifier_qualification_record_sha256"),
            attestation["private_qualification_record_sha256"],
        ),
    }
    for field, (actual, expected) in exact.items():
        if actual != expected:
            raise PreregistrationError(f"measured task {field} pin differs from the freeze")


def validate_teacher_execution_authorization(
    path: Path,
    *,
    task_id: str,
) -> dict[str, object]:
    validate_public_freeze()
    authorization = _load(path, "measured teacher authorization")
    expected_fields = {
        "schema_version",
        "preregistration_pr_merged",
        "preregistration_freeze_sha256",
        "code_revision",
        "task_id",
        "public_instruction_sha256",
        "effective_instruction_sha256",
        "task_container_digest",
        "verifier_bundle_sha256",
        "qualification_record_path",
        "qualification_record_sha256",
    }
    if set(authorization) != expected_fields:
        raise PreregistrationError("measured teacher authorization fields differ from the contract")
    if authorization.get("schema_version") != TEACHER_AUTHORIZATION_SCHEMA:
        raise PreregistrationError("measured teacher authorization schema mismatch")
    if authorization.get("preregistration_pr_merged") is not True:
        raise PreregistrationError("preregistration PR must be merged before measured teacher execution")
    if authorization.get("preregistration_freeze_sha256") != sha256_file(FREEZE_PATH):
        raise PreregistrationError("measured teacher authorization freeze hash mismatch")
    if authorization.get("task_id") != task_id:
        raise PreregistrationError("measured teacher authorization task mismatch")
    attestation = _attestations_by_task().get(task_id)
    if attestation is None or attestation.get("task_role") != "memory_build":
        raise PreregistrationError("measured teacher task is not frozen for memory build")
    exact = {
        "public_instruction_sha256": attestation["public_instruction_sha256"],
        "task_container_digest": attestation["task_container_digest"],
        "verifier_bundle_sha256": attestation["verifier_bundle_sha256"],
        "qualification_record_sha256": attestation["private_qualification_record_sha256"],
    }
    for field, expected in exact.items():
        if authorization.get(field) != expected:
            raise PreregistrationError(f"measured teacher authorization {field} mismatch")
    qualification_path = Path(str(authorization["qualification_record_path"]))
    freeze = load_freeze()
    task_source = _mapping(freeze["task_source"], "freeze task source")
    validate_qualification_path(
        qualification_path,
        expected_record_sha256=str(attestation["private_qualification_record_sha256"]),
        task_id=task_id,
        terminal_bench_revision=str(task_source["terminal_bench_revision"]),
        task_instruction_sha256=str(attestation["public_instruction_sha256"]),
        task_container_digest=str(attestation["task_container_digest"]),
        verifier_bundle_sha256=str(attestation["verifier_bundle_sha256"]),
    )
    code_revision = str(authorization.get("code_revision", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", code_revision):
        raise PreregistrationError("measured teacher authorization requires a full code revision")
    if validate_landed_freeze_revision() != code_revision:
        raise PreregistrationError(
            "measured teacher authorization revision differs from the landed freeze revision"
        )
    effective_instruction_sha256 = str(authorization.get("effective_instruction_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", effective_instruction_sha256):
        raise PreregistrationError("measured teacher effective instruction hash must be SHA-256")
    return {
        "schema_version": TEACHER_AUTHORIZATION_SCHEMA,
        "task_id": task_id,
        "code_revision": code_revision,
        "preregistration_freeze_sha256": authorization["preregistration_freeze_sha256"],
        "qualification_record_sha256": authorization["qualification_record_sha256"],
        "effective_instruction_sha256": effective_instruction_sha256,
        "task_container_digest": authorization["task_container_digest"],
    }


def validate_student_manifest_against_freeze(manifest: Mapping[str, object]) -> None:
    if manifest.get("data_classification") != "measured":
        return
    validate_public_freeze()
    _validate_roles(manifest)
    _validate_split(manifest)
    _validate_task_pins(manifest, expected_role="held_out_student_evaluation")
    task = _mapping(manifest["task"], "task")
    task_id = str(task["task_id"])
    if task.get("task_family") != TASK_FAMILIES.get(task_id):
        raise PreregistrationError("held-out structural family differs from the freeze")
    controls = _mapping(manifest["controls"], "controls")
    model = _mapping(controls["model"], "controls.model")
    budget = _mapping(controls["execution_budget"], "controls.execution_budget")
    retrieval = _mapping(controls["retrieval"], "controls.retrieval")
    exact = {
        "context size": (model.get("context_size"), 32768),
        "turn budget": (budget.get("max_turns"), 24),
        "attempt budget": (budget.get("n_attempts"), 1),
        "summarization": (controls.get("enable_summarize"), False),
        "retrieval top K": (retrieval.get("top_k"), 3),
        "retrieval token budget": (retrieval.get("token_budget"), 1800),
        "memory checkpoint": (manifest.get("memory_checkpoint"), 3),
        "memory contributions": (manifest.get("memory_contributions"), 3),
        "baseline contributions": (manifest.get("baseline_memory_contributions"), 0),
    }
    for field, (actual, expected) in exact.items():
        if actual != expected:
            raise PreregistrationError(f"measured {field} differs from the freeze")
    validate_landed_freeze_revision()


def validate_build_manifest_against_freeze(manifest: Mapping[str, object]) -> None:
    if manifest.get("data_classification") != "measured":
        return
    validate_public_freeze()
    _validate_roles(manifest)
    _validate_split(manifest)
    _validate_task_pins(manifest, expected_role="memory_build")
    validate_landed_freeze_revision()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate immutable preregistration controls.")
    parser.add_argument("--private-qualification-records", type=Path)
    args = parser.parse_args(argv)
    validate_public_freeze()
    if args.private_qualification_records:
        validate_private_qualification_records(args.private_qualification_records)
    print("Preregistration freeze is consistent; no measured execution was performed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PreregistrationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
