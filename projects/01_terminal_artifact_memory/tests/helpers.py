"""Helpers for unmistakably synthetic, non-measured fixtures."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from artifact_memory.sanitize import SANITIZER_REVISION, sanitize_artifact, sha256_file

FIXTURE_SHA = "a" * 64
FIXTURE_REVISION = "b" * 40


def synthetic_manifest() -> dict[str, Any]:
    return {
        "schema_version": "paired-run-manifest-v1",
        "data_classification": "synthetic_fixture_not_measured",
        "pair_id": "synthetic-fixture-pair",
        "memory_checkpoint": 1,
        "memory_contributions": 1,
        "baseline_memory_contributions": 1,
        "task": {
            "task_id": "synthetic-fixture-task",
            "task_name": "synthetic-fixture-task",
            "task_family": "environment_setup",
            "question_type": "structural",
            "retrieval_query": "configure package environment shell path",
            "expected_relevant_pages": ["fixture-environment-page"],
        },
        "run_environment": {
            "code_revision": FIXTURE_REVISION,
            "harbor_version": "fixture-harbor-v0",
            "docker_version": "fixture-docker-v0",
            "terminal_bench_version": "v0",
            "terminal_bench_revision": FIXTURE_REVISION,
            "registry_snapshot_sha256": FIXTURE_SHA,
            "task_instruction_sha256": FIXTURE_SHA,
            "task_container_digest": "sha256:" + FIXTURE_SHA,
            "terminus_version": "fixture-terminus-v0",
            "atif_schema_version": "fixture-atif-v0",
            "llama_cpp_revision": FIXTURE_REVISION,
            "model_sha256": FIXTURE_SHA,
            "quantization": "GGUF-Q4_K_M",
            "prompt_revision": "system-v1+memory-v1",
            "retrieval_revision": "direct-markdown-lexical-v1",
            "sanitizer_revision": SANITIZER_REVISION,
            "python_lock_hash": FIXTURE_SHA,
            "operating_system": "synthetic fixture OS",
            "hardware_description": "synthetic fixture laptop",
            "gitleaks_version": "fixture-gitleaks-v0",
        },
        "controls": {
            "model": {
                "family": "Qwen fixture",
                "parameters": "7B",
                "id": "synthetic-qwen-7b",
                "sha256": FIXTURE_SHA,
                "quantization": "GGUF-Q4_K_M",
                "context_size": 4096,
            },
            "runtime": {
                "name": "llama.cpp",
                "revision": FIXTURE_REVISION,
                "harbor_model": "openai/synthetic-fixture-model",
            },
            "prompt": {
                "revision": "system-v1+memory-v1",
                "system_sha256": FIXTURE_SHA,
                "memory_sha256": FIXTURE_SHA,
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


def admission_fixture(root: Path) -> tuple[Path, Path, Path]:
    canary = "SYNTHETIC-FIXTURE-CANARY"
    raw = root / "raw-fixture.txt"
    sanitized = root / "sanitized-fixture.txt"
    report = root / "sanitizer-fixture.json"
    raw.write_text(f"Synthetic fixture evidence. {canary}\n")
    sanitize_artifact(
        raw,
        sanitized,
        report,
        artifact_id="fixture-artifact",
        canaries=[canary],
        gitleaks_runner=clean_gitleaks,
    )
    verifier = root / "verifier-fixture.txt"
    verifier.write_text("1\n")
    provenance = {
        "artifact_id": "fixture-artifact",
        "run_id": "fixture-run",
        "task_id": "fixture-task",
        "task_family": "environment_setup",
        "code_revision": FIXTURE_REVISION,
        "harbor_version": "fixture-harbor-v0",
        "docker_version": "fixture-docker-v0",
        "terminal_bench_version": "fixture-task-v0",
        "terminal_bench_revision": FIXTURE_REVISION,
        "registry_snapshot_sha256": FIXTURE_SHA,
        "task_instruction_sha256": FIXTURE_SHA,
        "task_container_digest": "sha256:" + FIXTURE_SHA,
        "terminus_version": "fixture-terminus-v0",
        "atif_schema_version": "fixture-atif-v0",
        "llama_cpp_revision": FIXTURE_REVISION,
        "model_sha256": FIXTURE_SHA,
        "quantization": "GGUF-Q4_K_M",
        "prompt_revision": "system-v1+memory-v1",
        "retrieval_revision": "direct-markdown-lexical-v1",
        "sanitizer_revision": SANITIZER_REVISION,
        "python_lock_hash": FIXTURE_SHA,
        "operating_system": "synthetic fixture OS",
        "hardware_description": "synthetic fixture laptop",
        "trajectory_sha256": sha256_file(raw),
        "verifier_artifact_sha256": sha256_file(verifier),
        "sanitized_artifact_sha256": sha256_file(sanitized),
        "gitleaks_version": "fixture-gitleaks-v0",
    }
    request = {
        "page_id": "fixture-environment-page",
        "sanitized_artifact_path": str(sanitized),
        "sanitizer_report_path": str(report),
        "verifier_artifact_path": str(verifier),
        "provenance": provenance,
        "verifier": {
            "passed": True,
            "authoritative": "terminal-bench-executable",
        },
        "human_review": {
            "approved": True,
            "reviewer_id": "fixture-reviewer",
            "reviewed_at": "2026-01-01T00:00:00Z",
            "approval_scope_sha256": sha256_file(sanitized),
        },
        "evidence_ids": ["fixture-evidence"],
        "summary": {
            "title": "Synthetic fixture environment setup",
            "problem_pattern": "A package environment needs a shell path configured.",
            "observable_symptoms": ["Fixture command is unavailable."],
            "environment_assumptions": ["Synthetic fixture shell."],
            "diagnostic_sequence": ["Inspect the fixture path."],
            "verified_resolution": [
                {
                    "claim": "Configure the fixture package path.",
                    "evidence_ids": ["fixture-evidence"],
                }
            ],
            "limitations": ["Applies only to synthetic fixtures."],
        },
    }
    request_path = root / "admission-fixture.json"
    request_path.write_text(json.dumps(request, indent=2))
    return request_path, sanitized, report


def result_fixture(
    pair_id: str,
    m0_passed: bool,
    m2_passed: bool,
    *,
    task_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = synthetic_manifest()
    manifest["pair_id"] = pair_id
    manifest["task"]["task_id"] = task_id or pair_id
    snapshot = {
        "task": copy.deepcopy(manifest["task"]),
        "run_environment": copy.deepcopy(manifest["run_environment"]),
        "controls": copy.deepcopy(manifest["controls"]),
        "harbor": copy.deepcopy(manifest["harbor"]),
        "memory_checkpoint": 1,
    }
    digest = hashlib.sha256(
        json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    def build(condition: str, passed: bool) -> dict[str, Any]:
        return {
            "schema_version": "paired-result-v1",
            "data_classification": "synthetic_fixture_not_measured",
            "run_id": f"{pair_id}-{condition.lower()}",
            "pair_id": pair_id,
            "task_id": task_id or pair_id,
            "task_family": "environment_setup",
            "question_type": "structural",
            "memory_checkpoint": 1,
            "memory_contributions": 1,
            "baseline_memory_contributions": 1,
            "observed_memory_pages": 1,
            "observed_memory_page_ids": ["fixture-environment-page"],
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
