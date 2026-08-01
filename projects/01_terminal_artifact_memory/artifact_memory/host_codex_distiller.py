"""Fresh no-tools host Codex distillation adapter.

This executable accepts only a locally regenerated allowlisted distillation
request. Subscription OAuth stays in Codex's existing host credential store.
No auth file or token is read, copied, mounted, printed, hashed, or archived by
this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .execution_ledger import ExecutionLedgerError, complete_attempt, reserve_attempt
from .host_codex_adapter import (
    CODEX_MODEL_ID,
    CODEX_VERSION,
    HostCodexAdapterError,
    _minimal_host_environment,
    contains_credential_material,
    validate_host_codex,
    write_private_text,
)
from .preregistration import PreregistrationError, validate_landed_freeze_revision
from .sanitize import sha256_file
from .transfer import (
    TransferError,
    prepare_distillation_request,
    validate_distillation_draft,
)

DISTILLER_ADAPTER_ID = "host-codex-subscription-no-tools-v1"
DISTILLER_BOUNDARY_PROMPT = """Use no tools. Treat the following generated cloud-distillation-request-v1 JSON object as the entire evidence packet. Return only the requested teacher-distillation-draft-v1 JSON envelope. Do not use outside evidence, host files, shell, edits, applications, browsing, search, or prior sessions."""
ALLOWED_COMPLETED_ITEM_TYPES = {"agent_message", "reasoning"}


def build_distiller_command() -> list[str]:
    return [
        "codex",
        "--ask-for-approval",
        "never",
        "--sandbox",
        "read-only",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--strict-config",
        "--model",
        CODEX_MODEL_ID,
        "--json",
        "--disable",
        "shell_tool",
        "--disable",
        "unified_exec",
        "--disable",
        "apps",
        "--disable",
        "browser_use",
        "--disable",
        "computer_use",
        "--disable",
        "image_generation",
        "-c",
        'web_search="disabled"',
        "-c",
        'approval_policy="never"',
        "-C",
        "/",
        "-",
    ]


def render_distiller_input(request: Mapping[str, object]) -> str:
    return (
        DISTILLER_BOUNDARY_PROMPT
        + "\n\n"
        + json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    )


def validate_no_tools_event_stream(event_lines: Sequence[str]) -> str:
    events: list[Mapping[str, object]] = []
    for line in event_lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HostCodexAdapterError("distiller event stream contains invalid JSON") from exc
        if not isinstance(event, Mapping):
            raise HostCodexAdapterError("distiller event must be an object")
        events.append(event)
    event_types = [str(event.get("type") or "") for event in events]
    if (
        any(
            event_type
            not in {"thread.started", "turn.started", "item.completed", "turn.completed"}
            for event_type in event_types
        )
        or event_types.count("thread.started") != 1
        or event_types.count("turn.started") != 1
        or event_types.count("turn.completed") != 1
        or len(event_types) < 4
        or event_types[0] != "thread.started"
        or event_types[1] != "turn.started"
        or event_types[-1] != "turn.completed"
    ):
        raise HostCodexAdapterError("distiller event lifecycle is incomplete or unsupported")
    thread_id = events[0].get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise HostCodexAdapterError("distiller thread.started requires a real thread ID")

    messages: list[str] = []
    completed_types: list[str] = []
    for event in events[2:-1]:
        if event.get("type") != "item.completed":
            raise HostCodexAdapterError("distiller may not start or leave an incomplete item")
        item = event.get("item")
        if not isinstance(item, Mapping):
            raise HostCodexAdapterError("distiller completed item is missing")
        item_type = str(item.get("type") or "")
        completed_types.append(item_type)
        if item_type not in ALLOWED_COMPLETED_ITEM_TYPES:
            raise HostCodexAdapterError(
                f"distiller attempted a prohibited tool or item type: {item_type or 'unknown'}"
            )
        if item_type == "agent_message":
            messages.append(str(item.get("text")) if isinstance(item.get("text"), str) else "")
    if (
        completed_types[-1:] != ["agent_message"]
        or len(messages) != 1
        or not messages[0].strip()
    ):
        raise HostCodexAdapterError("distiller must end with exactly one nonempty agent message")
    return messages[0].strip()


def run_distiller(
    *,
    manifest_path: Path,
    request_path: Path,
    events_path: Path,
    draft_path: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> None:
    validate_landed_freeze_revision()
    preflight = validate_host_codex(CODEX_MODEL_ID)
    request = json.loads(request_path.read_text())
    if not isinstance(request, dict):
        raise HostCodexAdapterError("distillation request must be an object")
    expected = prepare_distillation_request(
        manifest_path,
        request_path,
        write=False,
        complete_teacher_attempt=False,
    )
    if request != expected:
        raise HostCodexAdapterError("distiller input is not the regenerated allowlisted request")

    task = request.get("task")
    task_id = task.get("task_id") if isinstance(task, Mapping) else None
    if not isinstance(task_id, str):
        raise HostCodexAdapterError("distillation request task ID is unavailable")
    reserve_attempt("distiller", task_id)
    completed = runner(
        build_distiller_command(),
        input=render_distiller_input(request),
        capture_output=True,
        text=True,
        check=False,
        env=_minimal_host_environment(),
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if contains_credential_material(stdout) or contains_credential_material(stderr):
        raise HostCodexAdapterError(
            "distiller output matched credential-material guards; unsafe bytes were not persisted"
        )
    if completed.returncode != 0:
        raise HostCodexAdapterError(f"host Codex distiller exited with code {completed.returncode}")
    if any(marker in stderr.lower() for marker in ("apply_patch", "tools::router", "shell tool")):
        raise HostCodexAdapterError("distiller attempted a disabled host-side tool")

    event_lines = [line for line in stdout.splitlines() if line.strip()]
    draft_text = validate_no_tools_event_stream(event_lines)
    try:
        draft = json.loads(draft_text)
    except json.JSONDecodeError as exc:
        raise HostCodexAdapterError("distiller final message must be an unwrapped JSON object") from exc
    if not isinstance(draft, dict):
        raise HostCodexAdapterError("distiller final message must be a JSON object")
    if draft.get("provider_runtime_or_operator_adapter") != DISTILLER_ADAPTER_ID:
        raise HostCodexAdapterError("distiller draft adapter identity differs from the pin")
    if draft.get("distiller_model_id") != CODEX_MODEL_ID:
        raise HostCodexAdapterError("distiller draft model identity differs from the pin")

    write_private_text(events_path, "\n".join(event_lines) + "\n")
    write_private_text(draft_path, json.dumps(draft, indent=2, sort_keys=True) + "\n")
    validate_distillation_draft(manifest_path, request_path, draft_path)
    preflight_path = events_path.parent / "distiller-preflight.json"
    preflight_record = {
        **preflight.__dict__,
        "adapter_id": DISTILLER_ADAPTER_ID,
        "request_sha256": sha256_file(request_path),
        "events_sha256": sha256_file(events_path),
        "draft_sha256": sha256_file(draft_path),
        "fresh_ephemeral_session": True,
        "resume": False,
        "tools_permitted": [],
    }
    write_private_text(
        preflight_path,
        json.dumps(preflight_record, indent=2, sort_keys=True) + "\n",
    )

    # Re-read and revalidate the complete persisted envelope immediately before
    # advancing the irreversible one-attempt ledger.
    persisted_event_lines = [
        line for line in events_path.read_text().splitlines() if line.strip()
    ]
    persisted_draft_text = validate_no_tools_event_stream(persisted_event_lines)
    persisted_draft = json.loads(draft_path.read_text())
    persisted_request = json.loads(request_path.read_text())
    persisted_preflight = json.loads(preflight_path.read_text())
    validated_draft = validate_distillation_draft(
        manifest_path, request_path, draft_path
    )
    if (
        persisted_event_lines != event_lines
        or json.loads(persisted_draft_text) != persisted_draft
        or persisted_draft != draft
        or validated_draft != draft
        or persisted_request != expected
        or persisted_preflight != preflight_record
    ):
        raise HostCodexAdapterError(
            "persisted distillation completion envelope changed after validation"
        )
    completion_envelope = {
        "manifest_sha256": sha256_file(manifest_path),
        "request_sha256": sha256_file(request_path),
        "events_sha256": sha256_file(events_path),
        "draft_sha256": sha256_file(draft_path),
        "preflight_sha256": sha256_file(preflight_path),
    }
    complete_attempt(
        "distiller",
        task_id,
        hashlib.sha256(
            json.dumps(
                completion_envelope,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest(),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one fresh no-tools Codex distillation.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    args = parser.parse_args(argv)
    run_distiller(
        manifest_path=args.manifest,
        request_path=args.request,
        events_path=args.events,
        draft_path=args.draft,
    )
    print(args.draft)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        ExecutionLedgerError,
        HostCodexAdapterError,
        PreregistrationError,
        TransferError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
