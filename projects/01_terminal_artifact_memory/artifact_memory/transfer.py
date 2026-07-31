"""Auditable cloud-teacher/local-student transfer boundary.

This module does not call a cloud API.  It validates operator-supplied execution
provenance and emits the only packet that may be sent to the cloud distiller.
Raw trajectories and detailed scanner reports remain in ignored local storage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

try:
    from .sanitize import SANITIZER_REVISION, inspect_unsafe, sha256_file
    from .verifier_qualification import (
        VerifierQualificationError,
        validate_qualification_path,
    )
except ImportError:  # Allow direct execution from the project directory.
    from sanitize import SANITIZER_REVISION, inspect_unsafe, sha256_file
    from verifier_qualification import (
        VerifierQualificationError,
        validate_qualification_path,
    )

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEACHER_PROMPT_PATH = PROJECT_ROOT / "prompts" / "teacher.v1.md"
DISTILLER_PROMPT_PATH = PROJECT_ROOT / "prompts" / "distillation.v1.md"
STUDENT_SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "system.v1.md"
STUDENT_MEMORY_PROMPT_PATH = PROJECT_ROOT / "prompts" / "memory.v1.md"

PROTOCOL_REVISION = "teacher-student-transfer-v1"
VERIFIER_ELIGIBILITY_INVARIANT = (
    "Do not claim success; the executable verifier alone determines whether the run is "
    "eligible for local sanitization and later distillation."
)
BUILD_SCHEMA_VERSION = "teacher-memory-build-manifest-v1"
DISTILLATION_REQUEST_SCHEMA_VERSION = "cloud-distillation-request-v1"
DISTILLATION_DRAFT_SCHEMA_VERSION = "teacher-distillation-draft-v1"
APPROVAL_SCHEMA_VERSION = "external-human-approval-v1"

TEACHER_MODEL_ID = "gpt-5.6-sol"
STUDENT_MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
STUDENT_HF_REVISION = "13fb94bfda8c8cf22497dc57b78f391a9acb426a"
STUDENT_MODEL_SHA256 = "509287f78cb4d4cf6b3843734733b914b2c158e43e22a7f4bf5e963800894d3c"
STUDENT_QUANTIZATION = "GGUF-Q4_K_M"
STUDENT_LICENSE = "Apache-2.0"

TEACHER_PROMPT_REVISION = "teacher-v1"
TEACHER_PROMPT_SHA256 = "5a1c448ea3655b09c468a708f42c68dc3a9469f5bb72e8fdaa751fd1ab2b930b"
DISTILLER_PROMPT_REVISION = "distillation-v1"
DISTILLER_PROMPT_SHA256 = "506cabdb4e3fc24bc102708c293fcfb424be0340d6fc0cdc7d0bc6fef330de52"
STUDENT_PROMPT_REVISION = "system-v1+memory-v1"
STUDENT_SYSTEM_PROMPT_SHA256 = "7c21baeb6445e013972bdd6bbb941d2b367cb6b5d2e9a9b0e4c8bbef1bb5b015"
STUDENT_MEMORY_PROMPT_SHA256 = "a274f71dc6aae550995c6ce801fc15d9420bce50e82ccd66ead93631697abd6d"

TEACHER_TRANSMISSION_CLASSIFICATION = "cloud-public-benchmark-execution-v1"
DISTILLER_TRANSMISSION_CLASSIFICATION = "cloud-sanitized-evidence-allowlisted-v1"
STUDENT_TRANSMISSION_CLASSIFICATION = "local-only-student-evaluation-v1"

TEACHER_ALLOWED_DATA = (
    "preregistered public memory-build task identifiers and instructions",
    "the versioned cloud-teacher prompt",
    "task-visible observations inside the isolated public benchmark environment",
    "teacher-selected tool inputs and tool outputs required to solve the public task",
)
DISTILLER_ALLOWED_FIELDS = (
    "schema_version",
    "data_transmission_classification",
    "recipient_role",
    "recipient_model_id",
    "operator_adapter",
    "build_id",
    "task.task_id",
    "task.task_role",
    "task.split_revision",
    "task.public_instruction",
    "task.public_instruction_sha256",
    "prompt.revision",
    "prompt.sha256",
    "prompt.content",
    "source_evidence[].evidence_id",
    "source_evidence[].sha256",
    "source_evidence[].media_type",
    "source_evidence[].content",
    "gate_attestations.executable_verifier_passed",
    "gate_attestations.verifier_authority",
    "gate_attestations.sanitizer_revision",
    "gate_attestations.sanitizer_passed",
    "teacher_provenance.model_id",
    "teacher_provenance.operator_adapter",
    "teacher_provenance.prompt_revision",
    "teacher_provenance.prompt_sha256",
    "teacher_provenance.trajectory_sha256",
    "teacher_provenance.verifier_artifact_sha256",
    "source_evidence_sha256",
    "transmission_inventory.allowed_fields",
    "transmission_inventory.denied_classes",
)
DENIED_CLOUD_DATA = (
    "raw private trajectories or trajectory file contents uploaded after execution",
    "credentials, secrets, authentication material, or environment-variable values",
    "private paths, hostnames, repository names, machine identifiers, or infrastructure details",
    "hidden tests, verifier internals, detailed verifier output, or reference solutions",
    "canary values or canary metadata",
    "detailed Gitleaks or scanner output, findings, matched values, or blocked-term lists",
    "unrelated session, conversation, prompt, or terminal content",
)

SAFE_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
REVISION_RE = re.compile(r"[0-9a-f]{40}")
UTC_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
EVIDENCE_CITATION_RE = re.compile(r"\[evidence:([a-z0-9][a-z0-9._-]{2,127})\]")
DISTILLED_HEADINGS = (
    "# ",
    "## Problem pattern",
    "## Observable symptoms",
    "## Environment assumptions",
    "## Diagnostic sequence",
    "## Verified resolution",
    "## Supporting evidence",
    "## Limitations",
)
PLACEHOLDER_RE = re.compile(
    r"\b(?:REQUIRED|TBD)(?:_[A-Z0-9_]*)?\b|(?i:\b(?:CHANGEME|PLACEHOLDER)(?:_[A-Za-z0-9_]*)?\b)"
)

REQUIRED_BUILD_ENVIRONMENT = (
    "code_revision",
    "harbor_version",
    "docker_version",
    "terminal_bench_version",
    "terminal_bench_revision",
    "registry_snapshot_sha256",
    "task_container_digest",
    "terminus_version",
    "atif_schema_version",
    "python_lock_hash",
    "operating_system",
    "hardware_description",
    "gitleaks_version",
    "teacher_prompt_revision",
    "teacher_prompt_sha256",
    "distiller_prompt_revision",
    "distiller_prompt_sha256",
    "student_prompt_revision",
    "student_system_prompt_sha256",
    "student_memory_prompt_sha256",
    "student_model_sha256",
    "sanitizer_revision",
)


class TransferError(ValueError):
    """Raised when role, split, disclosure, or transfer provenance is invalid."""


@dataclass(frozen=True)
class BuildEvidence:
    manifest: Mapping[str, object]
    manifest_sha256: str
    instruction_path: Path
    trajectory_path: Path
    verifier_path: Path
    sanitized_path: Path
    sanitizer_report_path: Path


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def load_json_object(path: Path, name: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise TransferError(f"{name} must be readable JSON") from exc
    if not isinstance(value, dict):
        raise TransferError(f"{name} must be a JSON object")
    return value


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TransferError(f"{name} must be an object")
    return value


def _exact_keys(value: Mapping[str, object], expected: set[str], name: str) -> None:
    actual = set(value)
    if actual != expected:
        raise TransferError(
            f"{name} fields must match the auditable contract; unexpected or missing: "
            + ", ".join(sorted(actual ^ expected))
        )


def _strings(value: object, name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TransferError(f"{name} must be an explicit list of strings")
    return list(value)


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


def validate_split(split: object, task: object, *, expected_task_role: str) -> None:
    split_map = _mapping(split, "split")
    _exact_keys(
        split_map,
        {"revision", "memory_build_task_ids", "held_out_evaluation_task_ids"},
        "split",
    )
    task_map = _mapping(task, "task")
    revision = split_map.get("revision")
    if not isinstance(revision, str) or not SAFE_ID_RE.fullmatch(revision):
        raise TransferError("split.revision must be a safe identifier")
    build_ids = _strings(split_map.get("memory_build_task_ids"), "split.memory_build_task_ids")
    evaluation_ids = _strings(
        split_map.get("held_out_evaluation_task_ids"), "split.held_out_evaluation_task_ids"
    )
    if not build_ids or not evaluation_ids:
        raise TransferError("the memory-build and held-out evaluation split lists must be non-empty")
    if not all(SAFE_ID_RE.fullmatch(item) for item in (*build_ids, *evaluation_ids)):
        raise TransferError("task split identifiers must use the safe public identifier format")
    if len(build_ids) != len(set(build_ids)) or len(evaluation_ids) != len(set(evaluation_ids)):
        raise TransferError("task split lists must not contain duplicates")
    overlap = sorted(set(build_ids) & set(evaluation_ids))
    if overlap:
        raise TransferError("memory-build and held-out evaluation tasks overlap: " + ", ".join(overlap))
    task_id = task_map.get("task_id")
    if task_map.get("task_role") != expected_task_role:
        raise TransferError(f"task.task_role must be {expected_task_role}")
    permitted = build_ids if expected_task_role == "memory_build" else evaluation_ids
    if task_id not in permitted:
        raise TransferError(f"task {task_id!r} is not preregistered for {expected_task_role}")


def validate_roles(roles: object) -> None:
    role_map = _mapping(roles, "roles")
    _exact_keys(role_map, {"teacher", "distiller", "student"}, "roles")
    teacher = _mapping(role_map.get("teacher"), "roles.teacher")
    distiller = _mapping(role_map.get("distiller"), "roles.distiller")
    student = _mapping(role_map.get("student"), "roles.student")

    _exact_keys(
        teacher,
        {
            "role",
            "model_id",
            "provider_runtime_or_operator_adapter",
            "task_role",
            "may_score_student_evaluation",
            "prompt",
        },
        "roles.teacher",
    )
    _exact_keys(
        distiller,
        {
            "role",
            "model_id",
            "provider_runtime_or_operator_adapter",
            "task_role",
            "input_scope",
            "prompt",
        },
        "roles.distiller",
    )
    _exact_keys(
        student,
        {
            "role",
            "model_id",
            "hugging_face_revision",
            "sha256",
            "quantization",
            "license",
            "provider_runtime_or_operator_adapter",
            "task_role",
            "sole_evaluation_model",
            "prompt",
        },
        "roles.student",
    )
    expected = (
        (teacher, "cloud_teacher", TEACHER_MODEL_ID, "memory_build_solver"),
        (distiller, "cloud_distiller", TEACHER_MODEL_ID, "sanitized_evidence_distiller"),
        (student, "local_student", STUDENT_MODEL_ID, "held_out_evaluation_solver"),
    )
    for record, role, model_id, task_role in expected:
        if record.get("role") != role or record.get("model_id") != model_id:
            raise TransferError(f"{role} must use the exact pinned model identity")
        if record.get("task_role") != task_role:
            raise TransferError(f"{role} has the wrong task role")
        adapter = record.get("provider_runtime_or_operator_adapter")
        if not isinstance(adapter, str) or not adapter:
            raise TransferError(f"{role} requires a provider/runtime or operator adapter record")

    if teacher.get("may_score_student_evaluation") is not False:
        raise TransferError("cloud teacher must be prohibited from scoring student evaluation")
    if distiller.get("input_scope") != "sanitized_evidence_only":
        raise TransferError("cloud distiller input_scope must be sanitized_evidence_only")
    if student.get("sole_evaluation_model") is not True:
        raise TransferError("local student must be the sole evaluation model")
    if student.get("hugging_face_revision") != STUDENT_HF_REVISION:
        raise TransferError("local student Hugging Face revision does not match the pin")
    if student.get("sha256") != STUDENT_MODEL_SHA256:
        raise TransferError("local student SHA-256 does not match the pin")
    if student.get("quantization") != STUDENT_QUANTIZATION:
        raise TransferError("local student quantization does not match the pin")
    if student.get("license") != STUDENT_LICENSE:
        raise TransferError("local student license must be Apache-2.0")

    prompt_expectations = (
        (teacher, TEACHER_PROMPT_REVISION, TEACHER_PROMPT_SHA256, ("sha256",)),
        (distiller, DISTILLER_PROMPT_REVISION, DISTILLER_PROMPT_SHA256, ("sha256",)),
        (
            student,
            STUDENT_PROMPT_REVISION,
            "",
            ("system_sha256", "memory_sha256"),
        ),
    )
    for record, revision, digest, hash_fields in prompt_expectations:
        prompt = _mapping(record.get("prompt"), f"{record['role']} prompt")
        _exact_keys(prompt, {"revision", *hash_fields}, f"{record['role']} prompt")
        if prompt.get("revision") != revision:
            raise TransferError(f"{record['role']} prompt revision does not match the pin")
        if len(hash_fields) == 1 and prompt.get(hash_fields[0]) != digest:
            raise TransferError(f"{record['role']} prompt hash does not match the pin")
        if len(hash_fields) == 2 and (
            prompt.get("system_sha256") != STUDENT_SYSTEM_PROMPT_SHA256
            or prompt.get("memory_sha256") != STUDENT_MEMORY_PROMPT_SHA256
        ):
            raise TransferError("local student prompt hashes do not match the pins")


def validate_transmission_policy(policy: object) -> None:
    policy_map = _mapping(policy, "data_transmission")
    _exact_keys(
        policy_map,
        {"teacher", "distiller", "student", "denied_for_all_cloud_roles"},
        "data_transmission",
    )
    teacher = _mapping(policy_map.get("teacher"), "data_transmission.teacher")
    distiller = _mapping(policy_map.get("distiller"), "data_transmission.distiller")
    student = _mapping(policy_map.get("student"), "data_transmission.student")
    _exact_keys(teacher, {"classification", "allowed_data"}, "data_transmission.teacher")
    _exact_keys(
        distiller,
        {"classification", "allowed_request_fields"},
        "data_transmission.distiller",
    )
    _exact_keys(student, {"classification", "allowed_cloud_data"}, "data_transmission.student")
    denied = _strings(policy_map.get("denied_for_all_cloud_roles"), "denied cloud classes")
    if teacher.get("classification") != TEACHER_TRANSMISSION_CLASSIFICATION:
        raise TransferError("teacher data-transmission classification is not pinned")
    if _strings(teacher.get("allowed_data"), "teacher allowed data") != list(TEACHER_ALLOWED_DATA):
        raise TransferError("teacher cloud-transmission inventory must match the explicit allowlist")
    if distiller.get("classification") != DISTILLER_TRANSMISSION_CLASSIFICATION:
        raise TransferError("distiller data-transmission classification is not pinned")
    if _strings(distiller.get("allowed_request_fields"), "distiller allowed fields") != list(
        DISTILLER_ALLOWED_FIELDS
    ):
        raise TransferError("distiller request fields must match the explicit allowlist")
    if student.get("classification") != STUDENT_TRANSMISSION_CLASSIFICATION:
        raise TransferError("student data-transmission classification must be local-only")
    if _strings(student.get("allowed_cloud_data"), "student allowed cloud data"):
        raise TransferError("the student evaluation role may transmit no data to cloud roles")
    if denied != list(DENIED_CLOUD_DATA):
        raise TransferError("denied cloud-transmission classes must match the explicit deny list")


def _validate_run_environment(environment: object, *, measured: bool) -> None:
    run_environment = _mapping(environment, "run_environment")
    missing = [field for field in REQUIRED_BUILD_ENVIRONMENT if not run_environment.get(field)]
    if missing:
        raise TransferError("incomplete role provenance: " + ", ".join(missing))
    exact = {
        "teacher_prompt_revision": TEACHER_PROMPT_REVISION,
        "teacher_prompt_sha256": TEACHER_PROMPT_SHA256,
        "distiller_prompt_revision": DISTILLER_PROMPT_REVISION,
        "distiller_prompt_sha256": DISTILLER_PROMPT_SHA256,
        "student_prompt_revision": STUDENT_PROMPT_REVISION,
        "student_system_prompt_sha256": STUDENT_SYSTEM_PROMPT_SHA256,
        "student_memory_prompt_sha256": STUDENT_MEMORY_PROMPT_SHA256,
        "student_model_sha256": STUDENT_MODEL_SHA256,
        "sanitizer_revision": SANITIZER_REVISION,
    }
    for field, value in exact.items():
        if run_environment.get(field) != value:
            raise TransferError(f"run_environment.{field} does not match the pinned role provenance")
    if measured:
        if not REVISION_RE.fullmatch(str(run_environment["code_revision"])):
            raise TransferError("measured code_revision must be a full Git revision")
        if not REVISION_RE.fullmatch(str(run_environment["terminal_bench_revision"])):
            raise TransferError("measured terminal_bench_revision must be a full Git revision")
        for field in (
            "registry_snapshot_sha256",
            "python_lock_hash",
            "teacher_prompt_sha256",
            "distiller_prompt_sha256",
            "student_system_prompt_sha256",
            "student_memory_prompt_sha256",
            "student_model_sha256",
        ):
            if not SHA256_RE.fullmatch(str(run_environment[field])):
                raise TransferError(f"measured {field} must be a SHA-256 digest")


def validate_build_manifest(manifest: Mapping[str, object]) -> None:
    _exact_keys(
        manifest,
        {
            "schema_version",
            "protocol_revision",
            "data_classification",
            "build_id",
            "task",
            "split",
            "roles",
            "data_transmission",
            "run_environment",
            "execution",
            "sanitization",
        },
        "teacher memory-build manifest",
    )
    if manifest.get("schema_version") != BUILD_SCHEMA_VERSION:
        raise TransferError(f"schema_version must be {BUILD_SCHEMA_VERSION}")
    if manifest.get("protocol_revision") != PROTOCOL_REVISION:
        raise TransferError(f"protocol_revision must be {PROTOCOL_REVISION}")
    classification = manifest.get("data_classification")
    if classification not in {"measured", "development", "synthetic_fixture_not_measured"}:
        raise TransferError("build data classification must be explicit")
    build_id = manifest.get("build_id")
    if not isinstance(build_id, str) or not SAFE_ID_RE.fullmatch(build_id):
        raise TransferError("build_id must be a safe identifier")
    validate_roles(manifest.get("roles"))
    validate_transmission_policy(manifest.get("data_transmission"))
    task = _mapping(manifest.get("task"), "task")
    _exact_keys(
        task,
        {
            "task_id",
            "task_name",
            "task_family",
            "task_role",
            "executed_by_role",
            "public_instruction_path",
            "public_instruction_sha256",
            "public_instruction_classification",
            "verifier_bundle_sha256",
            "verifier_qualification_record_path",
            "verifier_qualification_record_sha256",
        },
        "teacher memory-build task",
    )
    validate_split(manifest.get("split"), task, expected_task_role="memory_build")
    if task.get("executed_by_role") != "cloud_teacher":
        raise TransferError("memory-build tasks must be executed only by the cloud_teacher role")
    if task.get("public_instruction_classification") != "public-benchmark-instruction":
        raise TransferError("memory-build instruction must be classified as public benchmark data")
    for field in (
        "public_instruction_sha256",
        "verifier_bundle_sha256",
        "verifier_qualification_record_sha256",
    ):
        if not SHA256_RE.fullmatch(str(task.get(field, ""))):
            raise TransferError(f"task.{field} must be SHA-256")
    if not task.get("verifier_qualification_record_path"):
        raise TransferError("task.verifier_qualification_record_path is required")

    execution = _mapping(manifest.get("execution"), "execution")
    _exact_keys(
        execution,
        {
            "executed_by_role",
            "model_id",
            "operator_record_id",
            "trajectory_path",
            "trajectory_sha256",
            "verifier_artifact_path",
            "verifier_artifact_sha256",
            "started_at",
            "finished_at",
        },
        "teacher execution",
    )
    for field in (
        "operator_record_id",
        "trajectory_path",
        "trajectory_sha256",
        "verifier_artifact_path",
        "verifier_artifact_sha256",
        "started_at",
        "finished_at",
    ):
        if not execution.get(field):
            raise TransferError(f"execution.{field} is required")
    if execution.get("executed_by_role") != "cloud_teacher":
        raise TransferError("execution provenance must identify the cloud_teacher")
    if execution.get("model_id") != TEACHER_MODEL_ID:
        raise TransferError("teacher execution model does not match the exact pin")
    if not SHA256_RE.fullmatch(str(execution["trajectory_sha256"])) or not SHA256_RE.fullmatch(
        str(execution["verifier_artifact_sha256"])
    ):
        raise TransferError("teacher execution artifact hashes must be SHA-256")
    if not UTC_RE.fullmatch(str(execution["started_at"])) or not UTC_RE.fullmatch(
        str(execution["finished_at"])
    ):
        raise TransferError("teacher execution timestamps must be explicit UTC seconds")

    sanitization = _mapping(manifest.get("sanitization"), "sanitization")
    _exact_keys(
        sanitization,
        {"sanitized_artifact_path", "sanitizer_report_path", "sanitizer_revision"},
        "sanitization",
    )
    for field in ("sanitized_artifact_path", "sanitizer_report_path"):
        if not sanitization.get(field):
            raise TransferError(f"sanitization.{field} is required")
    if sanitization.get("sanitizer_revision") != SANITIZER_REVISION:
        raise TransferError("build sanitizer revision does not match this implementation")
    _validate_run_environment(manifest.get("run_environment"), measured=classification == "measured")
    if classification == "measured":
        placeholders = _find_placeholders(manifest)
        if placeholders:
            raise TransferError(
                "measured build manifest contains unresolved placeholders: " + ", ".join(placeholders)
            )


def _validate_sanitizer_report(report: Mapping[str, object]) -> None:
    canary = _mapping(report.get("canary"), "sanitizer canary")
    allowlist = _mapping(report.get("allowlist"), "sanitizer allowlist")
    residual = _mapping(report.get("residual_scan"), "sanitizer residual scan")
    gitleaks = _mapping(report.get("gitleaks"), "Gitleaks result")
    required = {
        "sanitizer accepted artifact": report.get("accepted_for_human_review") is True,
        "no blocking classes": report.get("blocking_classes") == [],
        "all canaries detected": canary.get("all_detected") is True,
        "all canaries removed": canary.get("removal_verified") is True,
        "allowlist passed": allowlist.get("passed") is True,
        "residual scan passed": residual.get("passed") is True,
        "Gitleaks source scan completed": gitleaks.get("source_scan_completed") is True,
        "Gitleaks clean": gitleaks.get("clean") is True,
        "Gitleaks no unresolved findings": gitleaks.get("findings_count") == 0,
    }
    failed = [name for name, passed in required.items() if not passed]
    if failed:
        raise TransferError("memory safety gate failed before distillation: " + ", ".join(failed))


def validate_build_evidence(manifest_path: Path) -> BuildEvidence:
    manifest = load_json_object(manifest_path, "teacher memory-build manifest")
    validate_build_manifest(manifest)
    task = _mapping(manifest["task"], "task")
    execution = _mapping(manifest["execution"], "execution")
    sanitization = _mapping(manifest["sanitization"], "sanitization")
    paths = {
        "instruction": Path(str(task["public_instruction_path"])),
        "trajectory": Path(str(execution["trajectory_path"])),
        "verifier": Path(str(execution["verifier_artifact_path"])),
        "sanitized": Path(str(sanitization["sanitized_artifact_path"])),
        "report": Path(str(sanitization["sanitizer_report_path"])),
    }
    if not all(path.is_file() for path in paths.values()):
        raise TransferError("build instruction, trajectory, verifier, sanitized artifact, and report must exist")
    if sha256_file(paths["instruction"]) != task["public_instruction_sha256"]:
        raise TransferError("public task instruction hash mismatch")
    run_environment = _mapping(manifest["run_environment"], "run_environment")
    try:
        validate_qualification_path(
            Path(str(task["verifier_qualification_record_path"])),
            expected_record_sha256=str(task["verifier_qualification_record_sha256"]),
            task_id=str(task["task_id"]),
            terminal_bench_revision=str(run_environment["terminal_bench_revision"]),
            task_instruction_sha256=str(task["public_instruction_sha256"]),
            task_container_digest=str(run_environment["task_container_digest"]),
            verifier_bundle_sha256=str(task["verifier_bundle_sha256"]),
        )
    except VerifierQualificationError as exc:
        raise TransferError(f"teacher task verifier is ineligible: {exc}") from exc
    if sha256_file(paths["trajectory"]) != execution["trajectory_sha256"]:
        raise TransferError("teacher trajectory hash mismatch")
    if sha256_file(paths["verifier"]) != execution["verifier_artifact_sha256"]:
        raise TransferError("teacher verifier artifact hash mismatch")

    # Single eligibility authority: never substitute model confidence, narrative,
    # apparent tool exits, or distillation quality for this executable result.
    verifier = load_json_object(paths["verifier"], "teacher executable-verifier artifact")
    if (
        verifier.get("authoritative") != "terminal-bench-executable"
        or verifier.get("passed") is not True
        or type(verifier.get("reward")) is not float
        or verifier.get("reward") != 1.0
        or type(verifier.get("reward_artifact_count")) is not int
        or verifier.get("reward_artifact_count") != 1
        or not SHA256_RE.fullmatch(str(verifier.get("source_sha256", "")))
    ):
        raise TransferError(
            "teacher memory build is ineligible because exactly one pinned executable-verifier "
            "pass was not established"
        )
    report = load_json_object(paths["report"], "local sanitizer report")
    _validate_sanitizer_report(report)
    if report.get("sanitizer_revision") != SANITIZER_REVISION:
        raise TransferError("sanitizer report revision mismatch")
    if report.get("artifact_id") != manifest["build_id"]:
        raise TransferError("sanitizer artifact identifier does not match build_id")
    if report.get("input_sha256") != execution["trajectory_sha256"]:
        raise TransferError("sanitization did not consume the teacher trajectory")
    sanitized_sha256 = sha256_file(paths["sanitized"])
    if report.get("output_sha256") != sanitized_sha256:
        raise TransferError("sanitized evidence hash does not match the sanitizer report")
    unsafe = inspect_unsafe(paths["sanitized"].read_text())
    if unsafe:
        raise TransferError("sanitized evidence still contains unsafe classes: " + ", ".join(unsafe))
    return BuildEvidence(
        manifest=manifest,
        manifest_sha256=sha256_file(manifest_path),
        instruction_path=paths["instruction"],
        trajectory_path=paths["trajectory"],
        verifier_path=paths["verifier"],
        sanitized_path=paths["sanitized"],
        sanitizer_report_path=paths["report"],
    )


def prepare_distillation_request(
    manifest_path: Path, output_path: Path, *, write: bool = True
) -> dict[str, object]:
    """Build the complete, field-allowlisted packet that an operator may upload."""

    evidence = validate_build_evidence(manifest_path)
    manifest = evidence.manifest
    task = _mapping(manifest["task"], "task")
    split = _mapping(manifest["split"], "split")
    roles = _mapping(manifest["roles"], "roles")
    teacher = _mapping(roles["teacher"], "roles.teacher")
    distiller = _mapping(roles["distiller"], "roles.distiller")
    execution = _mapping(manifest["execution"], "execution")
    sanitized_sha256 = sha256_file(evidence.sanitized_path)
    packet: dict[str, object] = {
        "schema_version": DISTILLATION_REQUEST_SCHEMA_VERSION,
        "data_transmission_classification": DISTILLER_TRANSMISSION_CLASSIFICATION,
        "recipient_role": "cloud_distiller",
        "recipient_model_id": TEACHER_MODEL_ID,
        "operator_adapter": distiller["provider_runtime_or_operator_adapter"],
        "build_id": manifest["build_id"],
        "task": {
            "task_id": task["task_id"],
            "task_role": "memory_build",
            "split_revision": split["revision"],
            "public_instruction": evidence.instruction_path.read_text(),
            "public_instruction_sha256": task["public_instruction_sha256"],
        },
        "prompt": {
            "revision": DISTILLER_PROMPT_REVISION,
            "sha256": DISTILLER_PROMPT_SHA256,
            "content": DISTILLER_PROMPT_PATH.read_text(),
        },
        "source_evidence": [
            {
                "evidence_id": f"{manifest['build_id']}-sanitized-evidence",
                "sha256": sanitized_sha256,
                "media_type": "text/plain; charset=utf-8",
                "content": evidence.sanitized_path.read_text(),
            }
        ],
        "gate_attestations": {
            "executable_verifier_passed": True,
            "verifier_authority": "terminal-bench-executable",
            "sanitizer_revision": SANITIZER_REVISION,
            "sanitizer_passed": True,
        },
        "teacher_provenance": {
            "model_id": TEACHER_MODEL_ID,
            "operator_adapter": teacher["provider_runtime_or_operator_adapter"],
            "prompt_revision": TEACHER_PROMPT_REVISION,
            "prompt_sha256": TEACHER_PROMPT_SHA256,
            "trajectory_sha256": execution["trajectory_sha256"],
            "verifier_artifact_sha256": execution["verifier_artifact_sha256"],
        },
        "source_evidence_sha256": [sanitized_sha256],
        "transmission_inventory": {
            "allowed_fields": list(DISTILLER_ALLOWED_FIELDS),
            "denied_classes": list(DENIED_CLOUD_DATA),
        },
    }
    if write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    return packet


def _validate_markdown_draft(body: str, evidence_ids: Sequence[str]) -> None:
    if body.startswith("---"):
        raise TransferError("distillation Markdown must not contain frontmatter")
    headings = [line for line in body.splitlines() if line.startswith("#")]
    if len(headings) != len(DISTILLED_HEADINGS):
        raise TransferError("distillation Markdown does not have the fixed heading structure")
    if not headings[0].startswith("# ") or not headings[0][2:].strip():
        raise TransferError("distillation Markdown title is missing")
    if tuple(headings[1:]) != DISTILLED_HEADINGS[1:]:
        raise TransferError("distillation Markdown headings are missing, reordered, or injected")
    sections: dict[str, list[str]] = {}
    current = ""
    for line in body.splitlines()[1:]:
        if line.startswith("## "):
            current = line[3:].strip().lower().replace(" ", "_")
            sections[current] = []
        elif current and line.strip():
            sections[current].append(line)
    for name, lines in sections.items():
        if name == "problem_pattern":
            if len(lines) != 1 or lines[0].startswith("-"):
                raise TransferError("distillation problem pattern must be one line")
        elif not lines or not all(line.startswith("- ") and len(line) > 2 for line in lines):
            raise TransferError(f"distillation {name} must contain single-line bullets")
    allowed = set(evidence_ids)
    expected_support = [f"- [evidence:{identifier}]" for identifier in evidence_ids]
    if sections.get("supporting_evidence") != expected_support:
        raise TransferError("distillation must list every supplied sanitized evidence identifier")
    for line in sections.get("verified_resolution", []):
        citations = EVIDENCE_CITATION_RE.findall(line)
        if not citations or not set(citations) <= allowed:
            raise TransferError("every resolution must cite supplied sanitized evidence")
    if set(EVIDENCE_CITATION_RE.findall(body)) - allowed:
        raise TransferError("distillation Markdown cites unknown evidence")


def validate_distillation_draft(
    manifest_path: Path, request_path: Path, draft_path: Path
) -> dict[str, object]:
    evidence = validate_build_evidence(manifest_path)
    request = load_json_object(request_path, "cloud distillation request")
    expected_request = prepare_distillation_request(manifest_path, request_path, write=False)
    if request != expected_request:
        raise TransferError("distillation request is not the locally regenerated allowlisted packet")
    draft = load_json_object(draft_path, "teacher distillation draft")
    _exact_keys(
        draft,
        {
            "schema_version",
            "build_id",
            "task_id",
            "task_role",
            "split_revision",
            "distiller_role",
            "distiller_model_id",
            "provider_runtime_or_operator_adapter",
            "prompt_revision",
            "prompt_sha256",
            "distillation_request_sha256",
            "source_evidence_sha256",
            "sanitizer_revision",
            "evidence_ids",
            "markdown_body",
        },
        "teacher distillation draft",
    )
    if draft.get("schema_version") != DISTILLATION_DRAFT_SCHEMA_VERSION:
        raise TransferError(f"distillation draft schema must be {DISTILLATION_DRAFT_SCHEMA_VERSION}")
    manifest = evidence.manifest
    roles = _mapping(manifest["roles"], "roles")
    distiller = _mapping(roles["distiller"], "roles.distiller")
    task = _mapping(manifest["task"], "task")
    split = _mapping(manifest["split"], "split")
    exact = {
        "build_id": manifest["build_id"],
        "task_id": task["task_id"],
        "task_role": "memory_build",
        "split_revision": split["revision"],
        "distiller_role": "cloud_distiller",
        "distiller_model_id": TEACHER_MODEL_ID,
        "provider_runtime_or_operator_adapter": distiller[
            "provider_runtime_or_operator_adapter"
        ],
        "prompt_revision": DISTILLER_PROMPT_REVISION,
        "prompt_sha256": DISTILLER_PROMPT_SHA256,
        "distillation_request_sha256": sha256_file(request_path),
        "sanitizer_revision": SANITIZER_REVISION,
    }
    for field, value in exact.items():
        if draft.get(field) != value:
            raise TransferError(f"distillation draft {field} does not match source provenance")
    expected_hashes = [sha256_file(evidence.sanitized_path)]
    if draft.get("source_evidence_sha256") != expected_hashes:
        raise TransferError("distillation draft source evidence hashes do not match sanitized evidence")
    evidence_ids = draft.get("evidence_ids")
    if not isinstance(evidence_ids, list) or not evidence_ids or not all(
        isinstance(item, str) and SAFE_ID_RE.fullmatch(item) for item in evidence_ids
    ):
        raise TransferError("distillation draft evidence_ids must be safe identifiers")
    body = draft.get("markdown_body")
    if not isinstance(body, str) or not body.strip():
        raise TransferError("distillation draft must contain a compact Markdown body")
    unsafe = inspect_unsafe(body)
    if unsafe:
        raise TransferError("distillation draft contains unsafe classes: " + ", ".join(unsafe))
    _validate_markdown_draft(body, evidence_ids)
    return draft


def validate_approval_record(
    approval_path: Path,
    *,
    manifest: Mapping[str, object],
    request_path: Path,
    draft_path: Path,
    sanitized_sha256: str,
    page_id: str,
) -> Mapping[str, object]:
    approval = load_json_object(approval_path, "external human approval record")
    _exact_keys(
        approval,
        {
            "schema_version",
            "approved",
            "external_human",
            "reviewer_id",
            "reviewed_at",
            "scope",
        },
        "external human approval",
    )
    if approval.get("schema_version") != APPROVAL_SCHEMA_VERSION:
        raise TransferError(f"approval schema must be {APPROVAL_SCHEMA_VERSION}")
    if approval.get("approved") is not True or approval.get("external_human") is not True:
        raise TransferError("explicit external human approval is required before admission")
    reviewer = approval.get("reviewer_id")
    reviewed_at = approval.get("reviewed_at")
    if not isinstance(reviewer, str) or not SAFE_ID_RE.fullmatch(reviewer):
        raise TransferError("approval reviewer_id must be a safe external identity")
    if not isinstance(reviewed_at, str) or not UTC_RE.fullmatch(reviewed_at):
        raise TransferError("approval reviewed_at must be an explicit UTC timestamp")
    task = _mapping(manifest["task"], "task")
    scope = _mapping(approval.get("scope"), "approval scope")
    _exact_keys(
        scope,
        {
            "build_id",
            "task_id",
            "page_id",
            "distillation_request_sha256",
            "distillation_draft_sha256",
            "sanitized_evidence_sha256",
            "source_evidence_sha256",
        },
        "external human approval scope",
    )
    expected = {
        "build_id": manifest["build_id"],
        "task_id": task["task_id"],
        "page_id": page_id,
        "distillation_request_sha256": sha256_file(request_path),
        "distillation_draft_sha256": sha256_file(draft_path),
        "sanitized_evidence_sha256": sanitized_sha256,
    }
    for field, value in expected.items():
        if scope.get(field) != value:
            raise TransferError(f"external human approval does not cover {field}")
    if scope.get("source_evidence_sha256") != [sanitized_sha256]:
        raise TransferError("external human approval does not cover all source evidence hashes")
    return approval


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the teacher/student transfer boundary.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-build")
    validate.add_argument("--manifest", type=Path, required=True)
    prepare = subparsers.add_parser("prepare-distillation")
    prepare.add_argument("--manifest", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    draft = subparsers.add_parser("validate-draft")
    draft.add_argument("--manifest", type=Path, required=True)
    draft.add_argument("--request", type=Path, required=True)
    draft.add_argument("--draft", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "validate-build":
        validate_build_evidence(args.manifest)
        print("Teacher memory-build provenance and local sanitizer gates are valid.")
        return 0
    if args.command == "prepare-distillation":
        prepare_distillation_request(args.manifest, args.output)
        print(args.output)
        return 0
    validate_distillation_draft(args.manifest, args.request, args.draft)
    print("Cloud distillation draft is provenance-linked to sanitized evidence.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TransferError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
