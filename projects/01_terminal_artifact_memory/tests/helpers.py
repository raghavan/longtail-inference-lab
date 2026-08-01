"""Helpers for unmistakably synthetic, non-measured fixtures."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from artifact_memory.sanitize import SANITIZER_REVISION, sanitize_artifact, sha256_file
from artifact_memory.transfer import (
    DENIED_CLOUD_DATA,
    DISTILLATION_DRAFT_SCHEMA_VERSION,
    DISTILLER_ALLOWED_FIELDS,
    DISTILLER_PROMPT_REVISION,
    DISTILLER_PROMPT_SHA256,
    DISTILLER_TRANSMISSION_CLASSIFICATION,
    PROTOCOL_REVISION,
    STUDENT_HF_REVISION,
    STUDENT_LICENSE,
    STUDENT_MEMORY_PROMPT_SHA256,
    STUDENT_MODEL_ID,
    STUDENT_MODEL_SHA256,
    STUDENT_PROMPT_REVISION,
    STUDENT_QUANTIZATION,
    STUDENT_SYSTEM_PROMPT_SHA256,
    STUDENT_TRANSMISSION_CLASSIFICATION,
    TEACHER_ALLOWED_DATA,
    TEACHER_MODEL_ID,
    TEACHER_PROMPT_REVISION,
    TEACHER_PROMPT_SHA256,
    TEACHER_TRANSMISSION_CLASSIFICATION,
    prepare_distillation_request,
)

FIXTURE_SHA = "a" * 64
FIXTURE_REVISION = "b" * 40
FIXTURE_CONTAINER_DIGEST = "sha256:" + FIXTURE_SHA


def role_fixture() -> dict[str, Any]:
    return {
        "teacher": {
            "role": "cloud_teacher",
            "model_id": TEACHER_MODEL_ID,
            "provider_runtime_or_operator_adapter": "synthetic-operator-teacher-adapter",
            "task_role": "memory_build_solver",
            "may_score_student_evaluation": False,
            "prompt": {
                "revision": TEACHER_PROMPT_REVISION,
                "sha256": TEACHER_PROMPT_SHA256,
            },
        },
        "distiller": {
            "role": "cloud_distiller",
            "model_id": TEACHER_MODEL_ID,
            "provider_runtime_or_operator_adapter": "synthetic-operator-distiller-adapter",
            "task_role": "sanitized_evidence_distiller",
            "input_scope": "sanitized_evidence_only",
            "prompt": {
                "revision": DISTILLER_PROMPT_REVISION,
                "sha256": DISTILLER_PROMPT_SHA256,
            },
        },
        "student": {
            "role": "local_student",
            "model_id": STUDENT_MODEL_ID,
            "hugging_face_revision": STUDENT_HF_REVISION,
            "sha256": STUDENT_MODEL_SHA256,
            "quantization": STUDENT_QUANTIZATION,
            "license": STUDENT_LICENSE,
            "provider_runtime_or_operator_adapter": "llama.cpp@synthetic-revision",
            "task_role": "held_out_evaluation_solver",
            "sole_evaluation_model": True,
            "prompt": {
                "revision": STUDENT_PROMPT_REVISION,
                "system_sha256": STUDENT_SYSTEM_PROMPT_SHA256,
                "memory_sha256": STUDENT_MEMORY_PROMPT_SHA256,
            },
        },
    }


def transmission_fixture() -> dict[str, Any]:
    return {
        "teacher": {
            "classification": TEACHER_TRANSMISSION_CLASSIFICATION,
            "allowed_data": list(TEACHER_ALLOWED_DATA),
        },
        "distiller": {
            "classification": DISTILLER_TRANSMISSION_CLASSIFICATION,
            "allowed_request_fields": list(DISTILLER_ALLOWED_FIELDS),
        },
        "student": {
            "classification": STUDENT_TRANSMISSION_CLASSIFICATION,
            "allowed_cloud_data": [],
        },
        "denied_for_all_cloud_roles": list(DENIED_CLOUD_DATA),
    }


def split_fixture() -> dict[str, Any]:
    return {
        "revision": "synthetic-split-v1",
        "memory_build_task_ids": ["synthetic-build-task"],
        "held_out_evaluation_task_ids": ["synthetic-held-out-task"],
    }


def run_environment_fixture() -> dict[str, Any]:
    return {
        "code_revision": FIXTURE_REVISION,
        "harbor_version": "fixture-harbor-v0",
        "docker_version": "fixture-docker-v0",
        "docker_compose_version": "fixture-compose-v0",
        "terminal_bench_version": "v0",
        "terminal_bench_revision": FIXTURE_REVISION,
        "registry_snapshot_sha256": FIXTURE_SHA,
        "task_instruction_sha256": FIXTURE_SHA,
        "task_container_digest": FIXTURE_CONTAINER_DIGEST,
        "terminus_version": "fixture-terminus-v0",
        "atif_schema_version": "fixture-atif-v0",
        "llama_cpp_revision": FIXTURE_REVISION,
        "student_model_sha256": STUDENT_MODEL_SHA256,
        "quantization": STUDENT_QUANTIZATION,
        "student_prompt_revision": STUDENT_PROMPT_REVISION,
        "teacher_prompt_revision": TEACHER_PROMPT_REVISION,
        "teacher_prompt_sha256": TEACHER_PROMPT_SHA256,
        "distiller_prompt_revision": DISTILLER_PROMPT_REVISION,
        "distiller_prompt_sha256": DISTILLER_PROMPT_SHA256,
        "student_system_prompt_sha256": STUDENT_SYSTEM_PROMPT_SHA256,
        "student_memory_prompt_sha256": STUDENT_MEMORY_PROMPT_SHA256,
        "retrieval_revision": "direct-markdown-lexical-v1",
        "sanitizer_revision": SANITIZER_REVISION,
        "python_lock_hash": FIXTURE_SHA,
        "operating_system": "synthetic fixture OS",
        "hardware_description": "synthetic fixture laptop",
        "gitleaks_version": "fixture-gitleaks-v0",
    }


def synthetic_manifest() -> dict[str, Any]:
    return {
        "schema_version": "teacher-student-paired-run-manifest-v3",
        "protocol_revision": PROTOCOL_REVISION,
        "data_classification": "synthetic_fixture_not_measured",
        "pair_id": "synthetic-fixture-pair",
        "memory_checkpoint": 1,
        "memory_contributions": 1,
        "baseline_memory_contributions": 1,
        "task": {
            "task_id": "synthetic-held-out-task",
            "task_name": "synthetic-held-out-task",
            "task_family": "environment_setup",
            "task_role": "held_out_student_evaluation",
            "executed_by_role": "local_student",
            "question_type": "structural",
            "retrieval_query": "configure package environment shell path",
            "expected_relevant_pages": ["fixture-environment-page"],
            "verifier_bundle_sha256": FIXTURE_SHA,
            "verifier_qualification_record_path": "synthetic-private-qualification.json",
            "verifier_qualification_record_sha256": FIXTURE_SHA,
        },
        "split": split_fixture(),
        "roles": role_fixture(),
        "data_transmission": transmission_fixture(),
        "run_environment": run_environment_fixture(),
        "controls": {
            "model": {
                "family": "Qwen",
                "parameters": "7B",
                "id": STUDENT_MODEL_ID,
                "hugging_face_revision": STUDENT_HF_REVISION,
                "sha256": STUDENT_MODEL_SHA256,
                "quantization": STUDENT_QUANTIZATION,
                "license": STUDENT_LICENSE,
                "context_size": 4096,
            },
            "runtime": {
                "name": "llama.cpp",
                "revision": FIXTURE_REVISION,
                "harbor_model": "openai/synthetic-fixture-model",
            },
            "prompt": {
                "revision": STUDENT_PROMPT_REVISION,
                "system_sha256": STUDENT_SYSTEM_PROMPT_SHA256,
                "memory_sha256": STUDENT_MEMORY_PROMPT_SHA256,
            },
            "decoding": {"temperature": 0, "seed": 7},
            "tool_permissions": ["terminal", "task-container-filesystem"],
            "execution_budget": {
                "max_turns": 3,
                "timeout_multiplier": 1.0,
                "n_attempts": 1,
            },
            "retrieval": {
                "revision": "direct-markdown-lexical-v1",
                "top_k": 2,
                "token_budget": 2000,
            },
            "enable_summarize": False,
        },
        "harbor": {
            "dataset": "synthetic/fixture@v0",
            "agent": "terminus-2",
            "environment": "docker",
            "n_concurrent": 1,
        },
        "llama_cpp": {
            "executable": "llama-server",
            "host": "localhost",
            "port": 8080,
        },
        "external": {
            "llama_api_base_env": "ARTIFACT_MEMORY_FIXTURE_API_BASE",
            "llama_api_key_env": "ARTIFACT_MEMORY_FIXTURE_API_KEY",
            "model_path_env": "ARTIFACT_MEMORY_FIXTURE_MODEL_PATH",
            "agent_api_key_env": "ARTIFACT_MEMORY_FIXTURE_AGENT_API_KEY",
        },
    }


def memory_page(page_id: str = "fixture-environment-page") -> str:
    return f"""---
page_id: {page_id}
task_family: environment_setup
artifact_id: fixture-artifact
run_id: fixture-run
status: current
---
# Synthetic fixture environment setup

## Problem pattern

A package environment needs a shell path configured.

## Observable symptoms

- Fixture command is unavailable.

## Environment assumptions

- Synthetic fixture shell.

## Diagnostic sequence

- Inspect fixture path.

## Verified resolution

- Configure the fixture package path. ([evidence:fixture-evidence])

## Supporting evidence

- [evidence:fixture-evidence]

## Limitations

- Applies only to synthetic fixtures.
"""


def clean_gitleaks(_target: Path, _report: Path) -> dict[str, object]:
    return {
        "clean": True,
        "exit_code": 0,
        "findings_count": 0,
        "command_interface": "synthetic-fixture-stub",
    }


def qualification_fixture(task_instruction_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": "verifier-qualification-v1",
        "data_classification": "development_only_not_measured",
        "pins": {
            "task_id": "synthetic-build-task",
            "terminal_bench_revision": FIXTURE_REVISION,
            "task_instruction_sha256": task_instruction_sha256,
            "task_container_digest": FIXTURE_CONTAINER_DIGEST,
            "verifier_bundle_sha256": FIXTURE_SHA,
        },
        "public_requirement_classes": ["fixture-build", "fixture-path"],
        "known_good_positive_control": {"attempts": 2, "accepted": 2},
        "targeted_negative_controls": [
            {
                "control_id": "broken-build",
                "public_requirement_class": "fixture-build",
                "attempts": 1,
                "accepted": 0,
            },
            {
                "control_id": "broken-path",
                "public_requirement_class": "fixture-path",
                "attempts": 1,
                "accepted": 0,
            },
        ],
        "clean_container_determinism": {
            "runs": 3,
            "consistent": True,
            "distinct_reward_values": [1.0],
        },
        "reward_and_test_isolation": {
            "tamper_attempts": 2,
            "tamper_accepts": 0,
            "isolated": True,
        },
        "eligible": True,
    }


def _build_run_environment() -> dict[str, Any]:
    value = run_environment_fixture()
    value.pop("task_instruction_sha256")
    value.pop("llama_cpp_revision")
    value.pop("quantization")
    value.pop("retrieval_revision")
    return value


def admission_fixture(root: Path) -> tuple[Path, Path, Path]:
    instruction = root / "public-instruction.md"
    instruction.write_text("Configure the synthetic public package environment.\n")
    instruction_sha = sha256_file(instruction)
    qualification_path = root / "verifier-qualification.json"
    qualification_path.write_text(json.dumps(qualification_fixture(instruction_sha), indent=2) + "\n")

    canary = "SYNTHETIC-FIXTURE-CANARY"
    raw = root / "raw-fixture.txt"
    sanitized = root / "sanitized-fixture.txt"
    report = root / "sanitizer-fixture.json"
    raw.write_text(f"Synthetic fixture evidence. {canary}\n")
    sanitize_artifact(
        raw,
        sanitized,
        report,
        artifact_id="fixture-build",
        canaries=[canary],
        gitleaks_runner=clean_gitleaks,
    )
    verifier = root / "verifier-fixture.json"
    verifier.write_text(
        json.dumps(
            {
                "authoritative": "terminal-bench-executable",
                "passed": True,
                "reward": 1.0,
                "reward_artifact_count": 1,
                "source_sha256": FIXTURE_SHA,
            }
        )
        + "\n"
    )
    build = {
        "schema_version": "teacher-memory-build-manifest-v2",
        "protocol_revision": PROTOCOL_REVISION,
        "data_classification": "synthetic_fixture_not_measured",
        "build_id": "fixture-build",
        "task": {
            "task_id": "synthetic-build-task",
            "task_name": "synthetic-build-task",
            "task_family": "environment_setup",
            "task_role": "memory_build",
            "executed_by_role": "cloud_teacher",
            "public_instruction_path": str(instruction),
            "public_instruction_sha256": instruction_sha,
            "public_instruction_classification": "public-benchmark-instruction",
            "verifier_bundle_sha256": FIXTURE_SHA,
            "verifier_qualification_record_path": str(qualification_path),
            "verifier_qualification_record_sha256": sha256_file(qualification_path),
        },
        "split": split_fixture(),
        "roles": role_fixture(),
        "data_transmission": transmission_fixture(),
        "run_environment": _build_run_environment(),
        "execution": {
            "executed_by_role": "cloud_teacher",
            "model_id": TEACHER_MODEL_ID,
            "operator_record_id": "fixture-teacher-run",
            "trajectory_path": str(raw),
            "trajectory_sha256": sha256_file(raw),
            "verifier_artifact_path": str(verifier),
            "verifier_artifact_sha256": sha256_file(verifier),
            "started_at": "2026-01-01T00:00:00Z",
            "finished_at": "2026-01-01T00:01:00Z",
        },
        "sanitization": {
            "sanitized_artifact_path": str(sanitized),
            "sanitizer_report_path": str(report),
            "sanitizer_revision": SANITIZER_REVISION,
        },
    }
    build_path = root / "teacher-build.json"
    build_path.write_text(json.dumps(build, indent=2) + "\n")
    request_packet_path = root / "distillation-request.json"
    prepare_distillation_request(build_path, request_packet_path)
    draft = {
        "schema_version": DISTILLATION_DRAFT_SCHEMA_VERSION,
        "build_id": "fixture-build",
        "task_id": "synthetic-build-task",
        "task_role": "memory_build",
        "split_revision": "synthetic-split-v1",
        "distiller_role": "cloud_distiller",
        "distiller_model_id": TEACHER_MODEL_ID,
        "provider_runtime_or_operator_adapter": "synthetic-operator-distiller-adapter",
        "prompt_revision": DISTILLER_PROMPT_REVISION,
        "prompt_sha256": DISTILLER_PROMPT_SHA256,
        "distillation_request_sha256": sha256_file(request_packet_path),
        "source_evidence_sha256": [sha256_file(sanitized)],
        "sanitizer_revision": SANITIZER_REVISION,
        "evidence_ids": ["fixture-build-sanitized-evidence"],
        "markdown_body": """# Synthetic fixture environment setup

## Problem pattern

A package environment needs a shell path configured.

## Observable symptoms

- Fixture command is unavailable.

## Environment assumptions

- Synthetic fixture shell.

## Diagnostic sequence

- Inspect the fixture path.

## Verified resolution

- Configure the fixture package path. ([evidence:fixture-build-sanitized-evidence])

## Supporting evidence

- [evidence:fixture-build-sanitized-evidence]

## Limitations

- Applies only to synthetic fixtures.""",
    }
    draft_path = root / "distillation-draft.json"
    draft_path.write_text(json.dumps(draft, indent=2) + "\n")
    approval = {
        "schema_version": "external-human-approval-v1",
        "approved": True,
        "external_human": True,
        "reviewer_id": "fixture-reviewer",
        "reviewed_at": "2026-01-01T00:02:00Z",
        "scope": {
            "build_id": "fixture-build",
            "task_id": "synthetic-build-task",
            "page_id": "fixture-environment-page",
            "distillation_request_sha256": sha256_file(request_packet_path),
            "distillation_draft_sha256": sha256_file(draft_path),
            "sanitized_evidence_sha256": sha256_file(sanitized),
            "source_evidence_sha256": [sha256_file(sanitized)],
        },
    }
    approval_path = root / "approval.json"
    approval_path.write_text(json.dumps(approval, indent=2) + "\n")
    admission = {
        "schema_version": "teacher-memory-admission-v2",
        "page_id": "fixture-environment-page",
        "build_manifest_path": str(build_path),
        "distillation_request_path": str(request_packet_path),
        "distillation_draft_path": str(draft_path),
        "approval_record_path": str(approval_path),
    }
    admission_path = root / "admission-fixture.json"
    admission_path.write_text(json.dumps(admission, indent=2) + "\n")
    return admission_path, sanitized, report


def result_fixture(
    pair_id: str,
    m0_passed: bool,
    m2_passed: bool,
    *,
    task_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = synthetic_manifest()
    manifest["pair_id"] = pair_id
    manifest["task"]["task_id"] = task_id or "synthetic-held-out-task"
    manifest["split"]["held_out_evaluation_task_ids"] = [
        task_id or "synthetic-held-out-task"
    ]
    snapshot = {
        "protocol_revision": manifest["protocol_revision"],
        "task": copy.deepcopy(manifest["task"]),
        "split": copy.deepcopy(manifest["split"]),
        "roles": copy.deepcopy(manifest["roles"]),
        "data_transmission": copy.deepcopy(manifest["data_transmission"]),
        "run_environment": copy.deepcopy(manifest["run_environment"]),
        "controls": copy.deepcopy(manifest["controls"]),
        "harbor": copy.deepcopy(manifest["harbor"]),
        "memory_checkpoint": 1,
        "baseline_memory_contributions": 1,
    }
    digest = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    memory_provenance = [
        {
            "page_id": "fixture-environment-page",
            "task_role": "memory_build",
            "teacher_model_id": TEACHER_MODEL_ID,
            "distiller_model_id": TEACHER_MODEL_ID,
            "student_model_id": STUDENT_MODEL_ID,
            "student_model_sha256": STUDENT_MODEL_SHA256,
            "source_evidence_sha256": [FIXTURE_SHA],
            "sanitizer_revision": SANITIZER_REVISION,
            "approval_record_sha256": FIXTURE_SHA,
        }
    ]

    def build(condition: str, passed: bool) -> dict[str, Any]:
        return {
            "schema_version": "student-paired-result-v2",
            "data_classification": "synthetic_fixture_not_measured",
            "protocol_revision": PROTOCOL_REVISION,
            "task_role": "held_out_student_evaluation",
            "evaluation_actor_role": "local_student",
            "student_model_id": STUDENT_MODEL_ID,
            "student_model_sha256": STUDENT_MODEL_SHA256,
            "run_id": f"{pair_id}-{condition.lower()}",
            "pair_id": pair_id,
            "task_id": task_id or "synthetic-held-out-task",
            "task_family": "environment_setup",
            "question_type": "structural",
            "memory_checkpoint": 1,
            "memory_contributions": 1,
            "baseline_memory_contributions": 1,
            "observed_memory_pages": 1,
            "observed_memory_page_ids": ["fixture-environment-page"],
            "memory_provenance": copy.deepcopy(memory_provenance),
            "memory_condition": condition,
            "verifier_passed": passed,
            "verifier_authority": "terminal-bench-executable",
            "retrieved_page_ids": [] if condition == "M0" else ["fixture-environment-page"],
            "expected_relevant_pages": ["fixture-environment-page"],
            "wiki_bytes": 1000,
            "control_digest": digest,
            "control_snapshot": copy.deepcopy(snapshot),
            "learned_judge_passed": not passed,
            "judge_probability": 1.0 if not passed else 0.0,
        }

    return build("M0", m0_passed), build("M2", m2_passed)
