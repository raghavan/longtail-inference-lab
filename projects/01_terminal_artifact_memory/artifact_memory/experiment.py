"""Controlled paired M0/M2 orchestration across narrow external boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import Callable, Mapping, Sequence

try:
    from .execution_ledger import complete_attempt, reserve_attempt
    from .host_codex_adapter import contains_credential_material
    from .memory import (
        CONTAINER_DIGEST_RE,
        PLACEHOLDER_RE,
        RETRIEVAL_REVISION,
        MemoryState,
        MemoryStateError,
        RetrievalResult,
        memory_provenance_snapshot,
        observed_memory_state,
        render_retrieved_memory,
        retrieve,
        validate_memory_split,
    )
    from .preregistration import (
        EXPECTED_SPLIT_REVISION,
        PreregistrationError,
        TASK_FAMILIES,
        validate_student_manifest_against_freeze,
    )
    from .sanitize import SANITIZER_REVISION, sha256_file
    from .verifier_qualification import (
        VerifierQualificationError,
        validate_qualification_path,
    )
    from .transfer import (
        DISTILLER_PROMPT_REVISION,
        DISTILLER_PROMPT_SHA256,
        PROTOCOL_REVISION,
        STUDENT_HF_REVISION,
        STUDENT_LICENSE,
        STUDENT_MEMORY_PROMPT_SHA256,
        STUDENT_MODEL_ID,
        STUDENT_MODEL_SHA256,
        STUDENT_PROMPT_REVISION,
        STUDENT_QUANTIZATION,
        STUDENT_SYSTEM_PROMPT_SHA256,
        TEACHER_PROMPT_REVISION,
        TEACHER_PROMPT_SHA256,
        TransferError,
        validate_roles,
        validate_split,
        validate_transmission_policy,
    )
except ImportError:  # Allow `python artifact_memory/experiment.py` from the project directory.
    from execution_ledger import complete_attempt, reserve_attempt
    from host_codex_adapter import contains_credential_material
    from memory import (
        CONTAINER_DIGEST_RE,
        PLACEHOLDER_RE,
        RETRIEVAL_REVISION,
        MemoryState,
        MemoryStateError,
        RetrievalResult,
        memory_provenance_snapshot,
        observed_memory_state,
        render_retrieved_memory,
        retrieve,
        validate_memory_split,
    )
    from preregistration import (
        EXPECTED_SPLIT_REVISION,
        PreregistrationError,
        TASK_FAMILIES,
        validate_student_manifest_against_freeze,
    )
    from sanitize import SANITIZER_REVISION, sha256_file
    from verifier_qualification import (
        VerifierQualificationError,
        validate_qualification_path,
    )
    from transfer import (
        DISTILLER_PROMPT_REVISION,
        DISTILLER_PROMPT_SHA256,
        PROTOCOL_REVISION,
        STUDENT_HF_REVISION,
        STUDENT_LICENSE,
        STUDENT_MEMORY_PROMPT_SHA256,
        STUDENT_MODEL_ID,
        STUDENT_MODEL_SHA256,
        STUDENT_PROMPT_REVISION,
        STUDENT_QUANTIZATION,
        STUDENT_SYSTEM_PROMPT_SHA256,
        TEACHER_PROMPT_REVISION,
        TEACHER_PROMPT_SHA256,
        TransferError,
        validate_roles,
        validate_split,
        validate_transmission_policy,
    )

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATHS = {
    "system": PROJECT_ROOT / "prompts" / "system.v1.md",
    "memory": PROJECT_ROOT / "prompts" / "memory.v1.md",
}
LOCK_PATH = PROJECT_ROOT / "uv.lock"
MEASURED = "measured"
CONDITIONS = ("M0", "M2")
SCHEMA_VERSION = "teacher-student-paired-run-manifest-v2"
LEGACY_SCHEMA_VERSION = "paired-run-manifest-v1"
RESULT_SCHEMA_VERSION = "student-paired-result-v2"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
REVISION_RE = re.compile(r"[0-9a-f]{40}")
SAFE_NAME_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]{1,127}")
DEFAULT_AGENT_API_KEY_ENV = "OPENAI_API_KEY"

REQUIRED_RUN_ENVIRONMENT = (
    "code_revision",
    "harbor_version",
    "docker_version",
    "terminal_bench_version",
    "terminal_bench_revision",
    "registry_snapshot_sha256",
    "task_instruction_sha256",
    "task_container_digest",
    "terminus_version",
    "atif_schema_version",
    "llama_cpp_revision",
    "student_model_sha256",
    "quantization",
    "student_prompt_revision",
    "teacher_prompt_revision",
    "teacher_prompt_sha256",
    "distiller_prompt_revision",
    "distiller_prompt_sha256",
    "student_system_prompt_sha256",
    "student_memory_prompt_sha256",
    "retrieval_revision",
    "sanitizer_revision",
    "python_lock_hash",
    "operating_system",
    "hardware_description",
    "gitleaks_version",
)


class ManifestError(ValueError):
    """Raised when a run would violate provenance or fixed-control rules."""


class PrerequisiteError(RuntimeError):
    """Raised when a pinned external platform boundary is unavailable."""


Runner = Callable[..., subprocess.CompletedProcess[str]]


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ManifestError(f"{name} must be an object")
    return value


def _missing(mapping: Mapping[str, object], fields: Sequence[str]) -> list[str]:
    return [field for field in fields if mapping.get(field) in (None, "", [], {})]


def _find_placeholders(value: object, path: str = "manifest") -> list[str]:
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


def load_manifest(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("run manifest must be readable JSON") from exc
    if not isinstance(value, dict):
        raise ManifestError("run manifest must be a JSON object")
    return value


def validate_manifest(manifest: Mapping[str, object]) -> None:
    if manifest.get("schema_version") == LEGACY_SCHEMA_VERSION:
        raise ManifestError(
            "legacy paired-run-manifest-v1 is not valid for teacher-student measurement; "
            "use the v2 template (the halted 16K pilot remains an immutable historical record)"
        )
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ManifestError(f"schema_version must be {SCHEMA_VERSION}")
    expected_top_level = {
        "schema_version",
        "protocol_revision",
        "data_classification",
        "pair_id",
        "memory_checkpoint",
        "memory_contributions",
        "baseline_memory_contributions",
        "task",
        "split",
        "roles",
        "data_transmission",
        "run_environment",
        "controls",
        "harbor",
        "llama_cpp",
        "external",
    }
    if set(manifest) != expected_top_level:
        raise ManifestError(
            "v2 manifest fields must match the auditable role contract; unexpected or missing: "
            + ", ".join(sorted(set(manifest) ^ expected_top_level))
        )
    if manifest.get("protocol_revision") != PROTOCOL_REVISION:
        raise ManifestError(f"protocol_revision must be {PROTOCOL_REVISION}")
    classification = manifest.get("data_classification")
    if classification not in {MEASURED, "development", "synthetic_fixture_not_measured"}:
        raise ManifestError("data_classification must explicitly identify measured or non-measured data")
    for field in (
        "pair_id",
        "memory_checkpoint",
        "memory_contributions",
        "baseline_memory_contributions",
        "task",
    ):
        if manifest.get(field) in (None, ""):
            raise ManifestError(f"missing required manifest field: {field}")
    for field in ("memory_checkpoint", "memory_contributions", "baseline_memory_contributions"):
        if not isinstance(manifest[field], int) or int(manifest[field]) < 0:
            raise ManifestError(f"{field} must be a non-negative integer")
    if manifest["baseline_memory_contributions"] > manifest["memory_contributions"]:
        raise ManifestError("baseline_memory_contributions cannot exceed memory_contributions")

    task = _mapping(manifest["task"], "task")
    missing_task = _missing(
        task,
        (
            "task_id",
            "task_name",
            "task_family",
            "task_role",
            "executed_by_role",
            "question_type",
            "retrieval_query",
            "verifier_bundle_sha256",
            "verifier_qualification_record_path",
            "verifier_qualification_record_sha256",
        ),
    )
    if missing_task:
        raise ManifestError("incomplete task controls: " + ", ".join(missing_task))
    expected_task_fields = {
        "task_id",
        "task_name",
        "task_family",
        "task_role",
        "executed_by_role",
        "question_type",
        "retrieval_query",
        "expected_relevant_pages",
        "verifier_bundle_sha256",
        "verifier_qualification_record_path",
        "verifier_qualification_record_sha256",
    }
    if set(task) != expected_task_fields:
        raise ManifestError(
            "evaluation task fields must match the auditable contract; unexpected or missing: "
            + ", ".join(sorted(set(task) ^ expected_task_fields))
        )
    if task.get("task_family") not in {"environment_setup", *TASK_FAMILIES.values()}:
        raise ManifestError("task_family is not supported by the frozen structural pilot")
    if task.get("executed_by_role") != "local_student":
        raise ManifestError("held-out evaluation tasks must be executed only by the local_student")
    try:
        validate_split(
            manifest.get("split"), task, expected_task_role="held_out_student_evaluation"
        )
        validate_roles(manifest.get("roles"))
        validate_transmission_policy(manifest.get("data_transmission"))
    except TransferError as exc:
        raise ManifestError(str(exc)) from exc
    if task.get("question_type") not in {"exact", "structural", "novel"}:
        raise ManifestError("question_type must be exact, structural, or novel")
    if "expected_relevant_pages" not in task or not isinstance(task.get("expected_relevant_pages"), list):
        raise ManifestError("expected_relevant_pages must be an explicit list")
    for field in ("verifier_bundle_sha256", "verifier_qualification_record_sha256"):
        if not SHA256_RE.fullmatch(str(task.get(field, ""))):
            raise ManifestError(f"task.{field} must be a SHA-256 digest")

    controls = _mapping(manifest.get("controls"), "controls")
    model = _mapping(controls.get("model"), "controls.model")
    runtime = _mapping(controls.get("runtime"), "controls.runtime")
    decoding = _mapping(controls.get("decoding"), "controls.decoding")
    prompt = _mapping(controls.get("prompt"), "controls.prompt")
    budget = _mapping(controls.get("execution_budget"), "controls.execution_budget")
    retrieval_config = _mapping(controls.get("retrieval"), "controls.retrieval")
    if _missing(
        model,
        (
            "family",
            "parameters",
            "id",
            "hugging_face_revision",
            "sha256",
            "quantization",
            "license",
            "context_size",
        ),
    ):
        raise ManifestError("student model controls are incomplete")
    exact_student = {
        "family": "Qwen",
        "parameters": "7B",
        "id": STUDENT_MODEL_ID,
        "hugging_face_revision": STUDENT_HF_REVISION,
        "sha256": STUDENT_MODEL_SHA256,
        "quantization": STUDENT_QUANTIZATION,
        "license": STUDENT_LICENSE,
    }
    for field, expected in exact_student.items():
        if model.get(field) != expected:
            raise ManifestError(f"student model {field} does not match the exact approved pin")
    if not isinstance(model.get("context_size"), int) or int(model["context_size"]) < 1:
        raise ManifestError("student context_size must be a positive preregistered integer")
    if runtime.get("name") != "llama.cpp":
        raise ManifestError("runtime control must be llama.cpp")
    if _missing(runtime, ("name", "revision", "harbor_model")):
        raise ManifestError("runtime controls are incomplete")
    if decoding.get("temperature") != 0 or not isinstance(decoding.get("seed"), int):
        raise ManifestError("temperature must be 0 and seed must be an integer")
    if _missing(prompt, ("revision", "system_sha256", "memory_sha256")):
        raise ManifestError("student prompt controls are incomplete")
    if (
        prompt.get("revision") != STUDENT_PROMPT_REVISION
        or prompt.get("system_sha256") != STUDENT_SYSTEM_PROMPT_SHA256
        or prompt.get("memory_sha256") != STUDENT_MEMORY_PROMPT_SHA256
    ):
        raise ManifestError("student prompt revision or hashes do not match the pinned role contract")
    if _missing(budget, ("max_turns", "timeout_multiplier", "n_attempts")):
        raise ManifestError("execution budget controls are incomplete")
    if budget.get("n_attempts") != 1:
        raise ManifestError("paired pilot trials require exactly one attempt per condition")
    if _missing(retrieval_config, ("revision", "top_k", "token_budget")):
        raise ManifestError("retrieval controls are incomplete")
    if retrieval_config.get("revision") != RETRIEVAL_REVISION:
        raise ManifestError("retrieval revision does not match this implementation")
    if not isinstance(retrieval_config.get("top_k"), int) or int(retrieval_config["top_k"]) < 1:
        raise ManifestError("retrieval top_k must be positive")
    if not isinstance(retrieval_config.get("token_budget"), int) or int(retrieval_config["token_budget"]) < 1:
        raise ManifestError("retrieval token_budget must be positive")
    permissions = controls.get("tool_permissions")
    if not isinstance(permissions, list) or not permissions:
        raise ManifestError("tool_permissions must be an explicit non-empty list")

    harbor = _mapping(manifest.get("harbor"), "harbor")
    if harbor.get("agent") != "terminus-2" or harbor.get("environment") != "docker":
        raise ManifestError("Harbor must use Terminus-2 in Docker")
    sources = [bool(harbor.get("dataset")), bool(harbor.get("dataset_path_env"))]
    if sum(sources) != 1:
        raise ManifestError("configure exactly one Harbor dataset or dataset_path_env")
    if harbor.get("n_concurrent") != 1:
        raise ManifestError("paired laptop pilot requires n_concurrent=1")
    extra_instruction_env = harbor.get("extra_instruction_path_env")
    if extra_instruction_env is not None and (
        not isinstance(extra_instruction_env, str)
        or not SAFE_NAME_RE.fullmatch(extra_instruction_env)
    ):
        raise ManifestError("harbor.extra_instruction_path_env must name a local environment variable")

    external = _mapping(manifest.get("external"), "external")
    for field in ("llama_api_base_env", "llama_api_key_env", "model_path_env"):
        if not isinstance(external.get(field), str) or not SAFE_NAME_RE.fullmatch(str(external[field])):
            raise ManifestError(f"external.{field} must name a local environment variable")
    agent_api_key_env = external.get("agent_api_key_env", DEFAULT_AGENT_API_KEY_ENV)
    if not isinstance(agent_api_key_env, str) or not SAFE_NAME_RE.fullmatch(agent_api_key_env):
        raise ManifestError("external.agent_api_key_env must name a local environment variable")

    run_environment = _mapping(manifest.get("run_environment"), "run_environment")
    if classification == MEASURED:
        missing_provenance = _missing(run_environment, REQUIRED_RUN_ENVIRONMENT)
        if missing_provenance:
            raise ManifestError(
                "incomplete measured-run provenance: " + ", ".join(missing_provenance)
            )
        placeholders = _find_placeholders(manifest)
        if placeholders:
            raise ManifestError(
                "measured-run manifest contains unresolved placeholders: " + ", ".join(placeholders)
            )
        if not REVISION_RE.fullmatch(str(run_environment["code_revision"])):
            raise ManifestError("measured code_revision must be a full Git revision")
        if not CONTAINER_DIGEST_RE.fullmatch(str(run_environment["task_container_digest"])):
            raise ManifestError(
                "measured task_container_digest must be an immutable sha256:<64 hex> digest"
            )
        if not REVISION_RE.fullmatch(str(run_environment["terminal_bench_revision"])):
            raise ManifestError("measured terminal_bench_revision must be a full Git revision")
        for field in (
            "student_model_sha256",
            "python_lock_hash",
            "registry_snapshot_sha256",
            "task_instruction_sha256",
        ):
            if not SHA256_RE.fullmatch(str(run_environment[field])):
                raise ManifestError(f"measured {field} must be a SHA-256 digest")
        dataset = harbor.get("dataset")
        if dataset:
            if "@" not in str(dataset):
                raise ManifestError("measured registered datasets must include a pinned version")
            dataset_version = str(dataset).rsplit("@", 1)[1]
            if dataset_version != run_environment["terminal_bench_version"]:
                raise ManifestError("registered dataset pin disagrees with terminal_bench_version")
        if run_environment["sanitizer_revision"] != SANITIZER_REVISION:
            raise ManifestError("sanitizer revision does not match this implementation")

    if run_environment:
        cross_checks = {
            "student_model_sha256": model.get("sha256"),
            "quantization": model.get("quantization"),
            "llama_cpp_revision": runtime.get("revision"),
            "student_prompt_revision": prompt.get("revision"),
            "retrieval_revision": retrieval_config.get("revision"),
            "teacher_prompt_revision": TEACHER_PROMPT_REVISION,
            "teacher_prompt_sha256": TEACHER_PROMPT_SHA256,
            "distiller_prompt_revision": DISTILLER_PROMPT_REVISION,
            "distiller_prompt_sha256": DISTILLER_PROMPT_SHA256,
            "student_system_prompt_sha256": STUDENT_SYSTEM_PROMPT_SHA256,
            "student_memory_prompt_sha256": STUDENT_MEMORY_PROMPT_SHA256,
        }
        for field, control_value in cross_checks.items():
            if run_environment.get(field) != control_value:
                raise ManifestError(f"run_environment.{field} disagrees with fixed controls")

    try:
        validate_student_manifest_against_freeze(manifest)
    except PreregistrationError as exc:
        raise ManifestError(str(exc)) from exc


def verified_memory_state(
    manifest: Mapping[str, object],
    wiki_dir: Path,
    index_path: Path,
    *,
    condition: str | None = None,
) -> MemoryState:
    """Check the condition-specific declared state against the admitted wiki.

    A staged baseline may run before memory construction. Its manifest still
    preregisters the later checkpoint, while baseline_memory_contributions
    records the pages actually allowed to exist during M0 execution.
    """

    try:
        state = observed_memory_state(wiki_dir, index_path)
        validate_memory_split(index_path, _mapping(manifest["split"], "split"))
    except MemoryStateError as exc:
        raise ManifestError(f"admitted memory state is not verifiable: {exc}") from exc
    expected = int(
        manifest["baseline_memory_contributions"]
        if condition == "M0"
        else manifest["memory_contributions"]
    )
    if expected != state.admitted_pages:
        label = "baseline_memory_contributions" if condition == "M0" else "memory_contributions"
        raise ManifestError(
            f"declared {label} ({expected}) disagrees with the admitted memory index "
            f"({state.admitted_pages} pages)"
        )
    if condition != "M0" and int(manifest["memory_checkpoint"]) != state.admitted_pages:
        raise ManifestError(
            f"declared memory_checkpoint ({manifest['memory_checkpoint']}) is not the verified "
            f"contribution count available in the admitted memory index ({state.admitted_pages})"
        )
    return state


def control_snapshot(manifest: Mapping[str, object]) -> dict[str, object]:
    harbor = deepcopy(dict(_mapping(manifest["harbor"], "harbor")))
    return {
        "protocol_revision": manifest["protocol_revision"],
        "task": deepcopy(dict(_mapping(manifest["task"], "task"))),
        "split": deepcopy(dict(_mapping(manifest["split"], "split"))),
        "roles": deepcopy(dict(_mapping(manifest["roles"], "roles"))),
        "data_transmission": deepcopy(
            dict(_mapping(manifest["data_transmission"], "data_transmission"))
        ),
        "run_environment": deepcopy(dict(_mapping(manifest["run_environment"], "run_environment"))),
        "controls": deepcopy(dict(_mapping(manifest["controls"], "controls"))),
        "harbor": harbor,
        "memory_checkpoint": manifest["memory_checkpoint"],
        "baseline_memory_contributions": manifest["baseline_memory_contributions"],
    }


def assert_control_equivalence(m0: Mapping[str, object], m2: Mapping[str, object]) -> None:
    if m0.get("memory_condition") != "M0" or m2.get("memory_condition") != "M2":
        raise ManifestError("paired results must contain M0 and M2 in order")
    left = m0.get("control_snapshot")
    right = m2.get("control_snapshot")
    if left != right or m0.get("control_digest") != m2.get("control_digest"):
        raise ManifestError("M0 and M2 differ in a fixed control")


def _resolved_env(manifest: Mapping[str, object], field: str) -> str:
    external = _mapping(manifest["external"], "external")
    variable = str(external[field])
    value = os.environ.get(variable)
    if not value:
        raise PrerequisiteError(f"required local environment variable is unset: {variable}")
    return value


def build_llama_command(manifest: Mapping[str, object]) -> list[str]:
    controls = _mapping(manifest["controls"], "controls")
    model = _mapping(controls["model"], "controls.model")
    llama = _mapping(manifest.get("llama_cpp"), "llama_cpp")
    executable = str(llama.get("executable", "llama-server"))
    return [
        executable,
        "--model",
        _resolved_env(manifest, "model_path_env"),
        "--ctx-size",
        str(model["context_size"]),
        "--host",
        str(llama.get("host", "127.0.0.1")),
        "--port",
        str(llama.get("port", 8080)),
    ]


def harbor_environment(manifest: Mapping[str, object]) -> dict[str, str]:
    """Resolve the ephemeral child-process environment for one Harbor trial.

    The loopback endpoint credential is forwarded only through this process
    environment, never through argv, manifests, run records, or logs.
    """

    external = _mapping(manifest["external"], "external")
    variable = str(external.get("agent_api_key_env", DEFAULT_AGENT_API_KEY_ENV))
    if not SAFE_NAME_RE.fullmatch(variable):
        raise ManifestError("external.agent_api_key_env must name a local environment variable")
    source_variable = str(external["llama_api_key_env"])
    resolved_value = _resolved_env(manifest, "llama_api_key_env")
    environment = dict(os.environ)
    if source_variable != variable:
        environment.pop(source_variable, None)
    environment[variable] = resolved_value
    return environment


def non_harbor_environment(manifest: Mapping[str, object]) -> dict[str, str]:
    external = _mapping(manifest["external"], "external")
    environment = dict(os.environ)
    environment.pop(str(external["llama_api_key_env"]), None)
    environment.pop(str(external.get("agent_api_key_env", DEFAULT_AGENT_API_KEY_ENV)), None)
    return environment


def build_harbor_command(
    manifest: Mapping[str, object],
    *,
    condition: str,
    jobs_dir: Path,
    skill_dir: Path,
) -> list[str]:
    if condition not in CONDITIONS:
        raise ManifestError(f"unsupported memory condition: {condition}")
    harbor = _mapping(manifest["harbor"], "harbor")
    controls = _mapping(manifest["controls"], "controls")
    runtime = _mapping(controls["runtime"], "controls.runtime")
    decoding = _mapping(controls["decoding"], "controls.decoding")
    budget = _mapping(controls["execution_budget"], "controls.execution_budget")
    task = _mapping(manifest["task"], "task")
    command = ["harbor", "run"]
    if harbor.get("dataset"):
        command.extend(["--dataset", str(harbor["dataset"])])
    else:
        dataset_path = os.environ.get(str(harbor["dataset_path_env"]))
        if not dataset_path:
            raise PrerequisiteError(
                f"required local environment variable is unset: {harbor['dataset_path_env']}"
            )
        command.extend(["--path", dataset_path])
    command.extend(
        [
            "--include-task-name",
            str(task["task_name"]),
            "--agent",
            str(harbor["agent"]),
            "--model",
            str(runtime["harbor_model"]),
            "--env",
            str(harbor["environment"]),
            "--n-concurrent",
            str(harbor["n_concurrent"]),
            "--n-attempts",
            str(budget["n_attempts"]),
            "--timeout-multiplier",
            str(budget["timeout_multiplier"]),
            "--job-name",
            f"{manifest['pair_id']}-{condition.lower()}",
            "--jobs-dir",
            str(jobs_dir),
            "--skill",
            str(skill_dir),
            "--agent-kwarg",
            f"api_base={_resolved_env(manifest, 'llama_api_base_env')}",
            "--agent-kwarg",
            f"temperature={decoding['temperature']}",
            "--agent-kwarg",
            f"max_turns={budget['max_turns']}",
            "--agent-kwarg",
            f"enable_summarize={str(bool(controls.get('enable_summarize', False))).lower()}",
            "--agent-kwarg",
            "llm_call_kwargs=" + json.dumps({"seed": decoding["seed"]}, separators=(",", ":")),
        ]
    )
    extra_instruction_env = harbor.get("extra_instruction_path_env")
    if extra_instruction_env:
        if not isinstance(extra_instruction_env, str) or not SAFE_NAME_RE.fullmatch(extra_instruction_env):
            raise ManifestError("harbor.extra_instruction_path_env must name a local environment variable")
        extra_instruction = os.environ.get(extra_instruction_env)
        if not extra_instruction:
            raise PrerequisiteError(
                f"required local environment variable is unset: {extra_instruction_env}"
            )
        command.extend(["--extra-instruction-path", extra_instruction])
    return command


def _run_version(command: list[str], runner: Runner, environment: Mapping[str, str]) -> str:
    completed = runner(command, capture_output=True, text=True, check=False, env=environment)
    if completed.returncode != 0:
        raise PrerequisiteError(f"command failed: {command[0]} {' '.join(command[1:])}")
    return (completed.stdout + "\n" + completed.stderr).strip()


def _require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise PrerequisiteError(f"required executable not found: {name}")


def _check_verifier_qualification(manifest: Mapping[str, object]) -> None:
    task = _mapping(manifest["task"], "task")
    run_environment = _mapping(manifest["run_environment"], "run_environment")
    try:
        validate_qualification_path(
            Path(str(task["verifier_qualification_record_path"])),
            expected_record_sha256=str(task["verifier_qualification_record_sha256"]),
            task_id=str(task["task_id"]),
            terminal_bench_revision=str(run_environment["terminal_bench_revision"]),
            task_instruction_sha256=str(run_environment["task_instruction_sha256"]),
            task_container_digest=str(run_environment["task_container_digest"]),
            verifier_bundle_sha256=str(task["verifier_bundle_sha256"]),
        )
    except VerifierQualificationError as exc:
        raise PrerequisiteError(f"held-out task verifier is ineligible: {exc}") from exc


def _check_local_task_pin(manifest: Mapping[str, object]) -> None:
    _check_verifier_qualification(manifest)
    harbor = _mapping(manifest["harbor"], "harbor")
    dataset_path_env = harbor.get("dataset_path_env")
    if not dataset_path_env:
        return
    dataset_path = os.environ.get(str(dataset_path_env))
    if not dataset_path:
        raise PrerequisiteError(
            f"required local environment variable is unset: {dataset_path_env}"
        )
    task = _mapping(manifest["task"], "task")
    root = Path(dataset_path)
    task_dir = root if (root / "task.toml").is_file() else root / str(task["task_name"])
    task_toml = task_dir / "task.toml"
    instruction = task_dir / "instruction.md"
    if not task_toml.is_file() or not instruction.is_file():
        raise PrerequisiteError("pinned local task is missing task.toml or instruction.md")
    try:
        metadata = tomllib.loads(task_toml.read_text())
        image = str(metadata["environment"]["docker_image"])
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise PrerequisiteError("pinned local task does not declare a readable Docker image") from exc
    run_environment = _mapping(manifest["run_environment"], "run_environment")
    expected_digest = str(run_environment["task_container_digest"])
    if not image.endswith("@" + expected_digest):
        raise PrerequisiteError("local task Docker image is not pinned to the measured digest")
    if sha256_file(instruction) != run_environment["task_instruction_sha256"]:
        raise PrerequisiteError("local task instruction hash does not match measured provenance")


def _check_local_endpoint(api_base: str, api_key: str) -> None:
    parsed = urllib.parse.urlparse(api_base)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise PrerequisiteError("llama.cpp endpoint must be an HTTP loopback address for laptop trials")
    root = api_base.rstrip("/")
    if root.endswith("/v1"):
        root = root[:-3]
    headers = {"Authorization": f"Bearer {api_key}"}
    for url in (root + "/health", api_base.rstrip("/") + "/models"):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                if not 200 <= response.status < 300:
                    raise PrerequisiteError(f"llama.cpp endpoint unhealthy: {url}")
        except (urllib.error.URLError, TimeoutError) as exc:
            raise PrerequisiteError(f"cannot reach pinned llama.cpp endpoint: {url}") from exc


def check_prerequisites(manifest: Mapping[str, object], runner: Runner = subprocess.run) -> dict[str, str]:
    validate_manifest(manifest)
    environment = non_harbor_environment(manifest)
    llama = _mapping(manifest.get("llama_cpp"), "llama_cpp")
    llama_executable = str(llama.get("executable", "llama-server"))
    for executable in ("git", "docker", "harbor", "gitleaks", llama_executable):
        _require_executable(executable)

    versions = {
        "docker": _run_version(
            [
                "docker",
                "version",
                "--format",
                "client={{.Client.Version}} server={{.Server.Version}} api={{.Server.APIVersion}}",
            ],
            runner,
            environment,
        ),
        "harbor": _run_version(["harbor", "--version"], runner, environment),
        "gitleaks": _run_version(["gitleaks", "version"], runner, environment),
        "llama_cpp": _run_version([llama_executable, "--version"], runner, environment),
    }
    docker_info = runner(
        ["docker", "info"], capture_output=True, text=True, check=False, env=environment
    )
    if docker_info.returncode != 0:
        raise PrerequisiteError("Docker daemon is not available")
    harbor_help = _run_version(["harbor", "run", "--help"], runner, environment)
    for flag in (
        "--dataset",
        "--path",
        "--include-task-name",
        "--agent-kwarg",
        "--skill",
        "--jobs-dir",
        "--job-name",
        "--extra-instruction-path",
    ):
        if flag not in harbor_help:
            raise PrerequisiteError(f"installed Harbor does not expose required flag: {flag}")

    run_environment = _mapping(manifest["run_environment"], "run_environment")
    expected = {
        "docker": str(run_environment.get("docker_version", "")),
        "harbor": str(run_environment.get("harbor_version", "")),
        "gitleaks": str(run_environment.get("gitleaks_version", "")),
        "llama_cpp": str(run_environment.get("llama_cpp_revision", "")),
    }
    if manifest["data_classification"] == MEASURED:
        for tool, pin in expected.items():
            if pin not in versions[tool]:
                raise PrerequisiteError(f"installed {tool} does not match measured-run pin")
        git_revision = _run_version(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"], runner, environment
        ).splitlines()[-1]
        if git_revision != run_environment["code_revision"]:
            raise PrerequisiteError("checked-out Git revision does not match measured-run provenance")
        git_status = runner(
            ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
        if git_status.returncode != 0 or git_status.stdout.strip():
            raise PrerequisiteError("measured runs require a clean tracked and untracked worktree")
        if sha256_file(LOCK_PATH) != run_environment["python_lock_hash"]:
            raise PrerequisiteError("uv.lock hash does not match measured-run provenance")
        _check_local_task_pin(manifest)
        controls = _mapping(manifest["controls"], "controls")
        prompt = _mapping(controls["prompt"], "controls.prompt")
        for name in ("system", "memory"):
            if sha256_file(PROMPT_PATHS[name]) != prompt[f"{name}_sha256"]:
                raise PrerequisiteError(f"{name} prompt hash does not match fixed controls")
        model_path = Path(_resolved_env(manifest, "model_path_env"))
        if (
            not model_path.is_file()
            or sha256_file(model_path) != run_environment["student_model_sha256"]
        ):
            raise PrerequisiteError("local student GGUF hash does not match measured-run provenance")

    _check_local_endpoint(
        _resolved_env(manifest, "llama_api_base_env"),
        _resolved_env(manifest, "llama_api_key_env"),
    )
    return versions


def _build_skill(
    destination: Path,
    retrieval: RetrievalResult,
    wiki_dir: Path,
) -> None:
    system_template = PROMPT_PATHS["system"].read_text()
    memory_template = PROMPT_PATHS["memory"].read_text()
    if system_template.count("{{MEMORY_BLOCK}}") != 1 or memory_template.count("{{MEMORY_PAGES}}") != 1:
        raise ManifestError("versioned prompts contain an invalid memory slot")
    memory_block = memory_template.replace(
        "{{MEMORY_PAGES}}", render_retrieved_memory(retrieval, wiki_dir)
    )
    rendered = system_template.replace("{{MEMORY_BLOCK}}", memory_block)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "SKILL.md").write_text(rendered)


def _empty_retrieval(query: str, top_k: int, token_budget: int) -> RetrievalResult:
    return RetrievalResult(
        revision=RETRIEVAL_REVISION,
        query_sha256=hashlib.sha256(query.encode()).hexdigest(),
        top_k=top_k,
        token_budget=token_budget,
        used_tokens=0,
        pages=(),
    )


def _extract_harbor_result(
    job_root: Path,
    trial_dir: Path,
    *,
    expected_atif_schema: str | None = None,
) -> tuple[bool, Path, Path, dict[str, int | float | None]]:
    rewards = sorted(job_root.glob("**/verifier/reward.txt"))
    trajectories = sorted(job_root.glob("**/agent/trajectory.json"))
    if len(rewards) != 1:
        raise RuntimeError("Harbor job must produce exactly one executable verifier reward")
    if len(trajectories) != 1:
        raise RuntimeError("Harbor Terminus-2 job must produce exactly one ATIF trajectory")
    try:
        reward = float(rewards[0].read_text().strip())
    except (OSError, ValueError) as exc:
        raise RuntimeError("Harbor verifier reward is unreadable") from exc
    passed = reward == 1.0
    try:
        trajectory = json.loads(trajectories[0].read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Harbor ATIF trajectory is unreadable") from exc
    if not isinstance(trajectory, Mapping):
        raise RuntimeError("Harbor ATIF trajectory must be a JSON object")
    if expected_atif_schema and trajectory.get("schema_version") != expected_atif_schema:
        raise RuntimeError("Harbor trajectory does not match the pinned ATIF schema")
    final_metrics = trajectory.get("final_metrics")
    metrics: dict[str, int | float | None] = {
        "prompt_tokens": None,
        "output_tokens": None,
        "total_steps": None,
    }
    if isinstance(final_metrics, Mapping):
        metrics = {
            "prompt_tokens": final_metrics.get("total_prompt_tokens"),
            "output_tokens": final_metrics.get("total_completion_tokens"),
            "total_steps": final_metrics.get("total_steps"),
        }
        if not all(value is None or isinstance(value, (int, float)) for value in metrics.values()):
            raise RuntimeError("Harbor ATIF final metrics contain invalid numeric fields")
    trajectory_destination = trial_dir / "trajectory.json"
    shutil.copy2(trajectories[0], trajectory_destination)
    verifier_destination = trial_dir / "verifier.json"
    verifier_destination.write_text(
        json.dumps(
            {
                "authoritative": "terminal-bench-executable",
                "passed": passed,
                "reward": reward,
                "reward_artifact_count": 1,
                "source_sha256": sha256_file(rewards[0]),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return passed, trajectory_destination, verifier_destination, metrics


def _wiki_bytes(wiki_dir: Path) -> int:
    return sum(path.stat().st_size for path in wiki_dir.glob("*.md") if path.is_file())


def _validate_student_completion(
    manifest: Mapping[str, object],
    condition: str,
    result_path: Path,
    trajectory_path: Path,
    verifier_path: Path,
    unsafe_audit_path: Path,
) -> str:
    validate_manifest(manifest)
    result = json.loads(result_path.read_text())
    verifier = json.loads(verifier_path.read_text())
    unsafe_audit = json.loads(unsafe_audit_path.read_text())
    task = _mapping(manifest["task"], "task")
    if (
        not isinstance(result, dict)
        or result.get("task_id") != task.get("task_id")
        or result.get("memory_condition") != condition
        or result.get("trajectory_sha256") != sha256_file(trajectory_path)
        or result.get("verifier_artifact_sha256") != sha256_file(verifier_path)
        or result.get("unsafe_error_audit") != unsafe_audit
        or result.get("unsafe_error_audit_sha256") != canonical_sha256(unsafe_audit)
        or result.get("unsafe_error") is not False
    ):
        raise RuntimeError("student completion artifact differs from manifest or local provenance")
    if (
        not isinstance(verifier, dict)
        or verifier.get("authoritative") != "terminal-bench-executable"
        or verifier.get("passed") != result.get("verifier_passed")
        or verifier.get("reward_artifact_count") != 1
    ):
        raise RuntimeError("student completion verifier artifact is not authoritative")
    if (
        not isinstance(unsafe_audit, dict)
        or unsafe_audit.get("schema_version") != "student-unsafe-error-audit-v1"
        or unsafe_audit.get("task_id") != task.get("task_id")
        or unsafe_audit.get("memory_condition") != condition
        or unsafe_audit.get("harbor_exit_zero") is not True
        or unsafe_audit.get("exception_artifact_count") != 0
        or unsafe_audit.get("credential_material_detected") is not False
        or unsafe_audit.get("reward_artifact_count") != 1
        or unsafe_audit.get("trajectory_artifact_count") != 1
        or unsafe_audit.get("unsafe_error") is not False
    ):
        raise RuntimeError("student completion unsafe-error audit is not clean and complete")
    return sha256_file(result_path)


def run_pair(
    manifest: Mapping[str, object],
    *,
    wiki_dir: Path,
    index_path: Path,
    runs_dir: Path,
    runner: Runner = subprocess.run,
    preflight: bool = True,
) -> Path:
    validate_manifest(manifest)
    if manifest["data_classification"] == MEASURED:
        raise ManifestError(
            "frozen measured sequence requires run-condition and the global execution ledger"
        )
    if manifest["data_classification"] == MEASURED and not preflight:
        raise ManifestError("measured runs cannot bypass prerequisite and verifier-qualification checks")
    if _find_placeholders(manifest):
        raise ManifestError("a runnable manifest cannot contain unresolved placeholders")
    if manifest["baseline_memory_contributions"] != manifest["memory_contributions"]:
        raise ManifestError(
            "run requires baseline_memory_contributions to equal memory_contributions; "
            "use run-condition for staged memory states"
        )
    memory_state = verified_memory_state(manifest, wiki_dir, index_path)
    if preflight:
        check_prerequisites(manifest, runner)
    trial_environment = harbor_environment(manifest)
    pair_dir = runs_dir / str(manifest["pair_id"])
    if pair_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing paired run: {pair_dir}")
    pair_dir.mkdir(parents=True)
    snapshot = control_snapshot(manifest)
    digest = canonical_sha256(snapshot)
    task = _mapping(manifest["task"], "task")
    controls = _mapping(manifest["controls"], "controls")
    retrieval_config = _mapping(controls["retrieval"], "controls.retrieval")
    query = str(task["retrieval_query"])

    results: list[dict[str, object]] = []
    for condition in CONDITIONS:
        trial_dir = pair_dir / condition
        trial_dir.mkdir()
        retrieval_result = (
            _empty_retrieval(query, int(retrieval_config["top_k"]), int(retrieval_config["token_budget"]))
            if condition == "M0"
            else retrieve(
                query,
                wiki_dir,
                top_k=int(retrieval_config["top_k"]),
                token_budget=int(retrieval_config["token_budget"]),
            )
        )
        retrieval_record = {
            **retrieval_result.to_dict(),
            "memory_condition": condition,
            "retrieval_performed": condition == "M2",
            "expected_relevant_pages": list(task["expected_relevant_pages"]),
        }
        (trial_dir / "retrieval.json").write_text(
            json.dumps(retrieval_record, indent=2, sort_keys=True) + "\n"
        )
        skill_dir = trial_dir / "retrieved-memory-skill"
        _build_skill(skill_dir, retrieval_result, wiki_dir)
        trial_manifest = {
            **deepcopy(dict(manifest)),
            "memory_condition": condition,
            "control_digest": digest,
            "control_snapshot": snapshot,
        }
        (trial_dir / "manifest.json").write_text(
            json.dumps(trial_manifest, indent=2, sort_keys=True) + "\n"
        )
        jobs_dir = trial_dir / "harbor-jobs"
        command = build_harbor_command(
            manifest, condition=condition, jobs_dir=jobs_dir, skill_dir=skill_dir
        )
        completed = runner(
            command,
            capture_output=True,
            text=True,
            check=False,
            env=trial_environment,
        )
        (trial_dir / "harbor-command.json").write_text(
            json.dumps(
                {
                    "argv": command,
                    "exit_code": completed.returncode,
                    "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
                    "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        if completed.returncode != 0:
            raise RuntimeError(f"Harbor failed for {condition}; inspect the local trial directory")
        passed, trajectory_path, verifier_path, trajectory_metrics = _extract_harbor_result(
            jobs_dir,
            trial_dir,
            expected_atif_schema=str(
                _mapping(manifest["run_environment"], "run_environment")["atif_schema_version"]
            ),
        )
        retrieved_ids = [page.page_id for page in retrieval_result.pages]
        expected = list(task["expected_relevant_pages"])
        result = {
            "schema_version": RESULT_SCHEMA_VERSION,
            "data_classification": manifest["data_classification"],
            "protocol_revision": PROTOCOL_REVISION,
            "split_revision": EXPECTED_SPLIT_REVISION,
            "unsafe_error": False,
            "task_role": "held_out_student_evaluation",
            "evaluation_actor_role": "local_student",
            "student_model_id": STUDENT_MODEL_ID,
            "student_model_sha256": STUDENT_MODEL_SHA256,
            "run_id": f"{manifest['pair_id']}-{condition.lower()}",
            "pair_id": manifest["pair_id"],
            "task_id": task["task_id"],
            "task_family": task["task_family"],
            "question_type": task["question_type"],
            "memory_checkpoint": manifest["memory_checkpoint"],
            "memory_contributions": manifest["memory_contributions"],
            "baseline_memory_contributions": manifest["baseline_memory_contributions"],
            "observed_memory_pages": memory_state.admitted_pages,
            "observed_memory_page_ids": list(memory_state.page_ids),
            "memory_provenance": memory_provenance_snapshot(index_path),
            "memory_condition": condition,
            "verifier_passed": passed,
            "verifier_authority": "terminal-bench-executable",
            "retrieved_page_ids": retrieved_ids,
            "expected_relevant_pages": expected,
            "retrieval_covered": bool(set(retrieved_ids) & set(expected)) if expected else None,
            "retrieval_revision": retrieval_result.revision,
            "retrieval_top_k": retrieval_result.top_k,
            "retrieval_token_budget": retrieval_result.token_budget,
            "wiki_bytes": _wiki_bytes(wiki_dir),
            "control_digest": digest,
            "control_snapshot": snapshot,
            "trajectory_sha256": sha256_file(trajectory_path),
            "verifier_artifact_sha256": sha256_file(verifier_path),
            "trajectory_bytes": trajectory_path.stat().st_size,
            "verifier_artifact_bytes": verifier_path.stat().st_size,
            **trajectory_metrics,
        }
        (trial_dir / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
        results.append(result)
    assert_control_equivalence(results[0], results[1])
    (pair_dir / "pair.json").write_text(
        json.dumps(
            {
                "pair_id": manifest["pair_id"],
                "control_digest": digest,
                "conditions": list(CONDITIONS),
                "result_paths": ["M0/result.json", "M2/result.json"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return pair_dir


def run_condition(
    manifest: Mapping[str, object],
    *,
    condition: str,
    wiki_dir: Path,
    index_path: Path,
    runs_dir: Path,
    runner: Runner = subprocess.run,
    preflight: bool = True,
) -> Path:
    """Run one stage of a preregistered pair without relabeling its memory state."""

    if condition not in CONDITIONS:
        raise ManifestError(f"unsupported memory condition: {condition}")
    validate_manifest(manifest)
    if manifest["data_classification"] == MEASURED and not preflight:
        raise ManifestError("measured runs cannot bypass prerequisite and verifier-qualification checks")
    if _find_placeholders(manifest):
        raise ManifestError("a runnable manifest cannot contain unresolved placeholders")
    memory_state = verified_memory_state(
        manifest, wiki_dir, index_path, condition=condition
    )
    if preflight:
        check_prerequisites(manifest, runner)
    trial_environment = harbor_environment(manifest)
    pair_dir = runs_dir / str(manifest["pair_id"])
    pair_dir.mkdir(parents=True, exist_ok=True)
    trial_dir = pair_dir / condition
    if trial_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing condition run: {trial_dir}")
    trial_dir.mkdir()

    snapshot = control_snapshot(manifest)
    digest = canonical_sha256(snapshot)
    task = _mapping(manifest["task"], "task")
    controls = _mapping(manifest["controls"], "controls")
    retrieval_config = _mapping(controls["retrieval"], "controls.retrieval")
    query = str(task["retrieval_query"])
    retrieval_started = time.monotonic()
    retrieval_result = (
        _empty_retrieval(
            query,
            int(retrieval_config["top_k"]),
            int(retrieval_config["token_budget"]),
        )
        if condition == "M0"
        else retrieve(
            query,
            wiki_dir,
            top_k=int(retrieval_config["top_k"]),
            token_budget=int(retrieval_config["token_budget"]),
        )
    )
    retrieval_seconds = time.monotonic() - retrieval_started
    retrieval_record = {
        **retrieval_result.to_dict(),
        "memory_condition": condition,
        "retrieval_performed": condition == "M2",
        "expected_relevant_pages": list(task["expected_relevant_pages"]),
        "retrieval_seconds": round(retrieval_seconds, 6),
    }
    (trial_dir / "retrieval.json").write_text(
        json.dumps(retrieval_record, indent=2, sort_keys=True) + "\n"
    )
    skill_dir = trial_dir / "retrieved-memory-skill"
    _build_skill(skill_dir, retrieval_result, wiki_dir)
    trial_manifest = {
        **deepcopy(dict(manifest)),
        "memory_condition": condition,
        "control_digest": digest,
        "control_snapshot": snapshot,
    }
    (trial_dir / "manifest.json").write_text(
        json.dumps(trial_manifest, indent=2, sort_keys=True) + "\n"
    )
    jobs_dir = trial_dir / "harbor-jobs"
    command = build_harbor_command(
        manifest, condition=condition, jobs_dir=jobs_dir, skill_dir=skill_dir
    )
    if manifest["data_classification"] == MEASURED:
        reserve_attempt(condition, str(task["task_id"]))
    started = time.monotonic()
    completed = runner(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=trial_environment,
    )
    latency_seconds = time.monotonic() - started
    (trial_dir / "harbor-command.json").write_text(
        json.dumps(
            {
                "argv": command,
                "exit_code": completed.returncode,
                "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
                "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    run_environment = _mapping(manifest["run_environment"], "run_environment")
    observed_reward_artifacts = len(list(jobs_dir.glob("**/verifier/reward.txt")))
    observed_trajectory_artifacts = len(list(jobs_dir.glob("**/agent/trajectory.json")))
    observed_exception_artifacts = len(list(jobs_dir.glob("**/exception.txt")))
    trajectory_paths = list(jobs_dir.glob("**/agent/trajectory.json"))
    credential_material_detected = contains_credential_material(
        completed.stdout
        + "\n"
        + completed.stderr
        + "\n"
        + "\n".join(path.read_text(errors="replace") for path in trajectory_paths)
    )
    unsafe_audit = {
        "schema_version": "student-unsafe-error-audit-v1",
        "task_id": task["task_id"],
        "memory_condition": condition,
        "harbor_exit_zero": completed.returncode == 0,
        "reward_artifact_count": observed_reward_artifacts,
        "trajectory_artifact_count": observed_trajectory_artifacts,
        "exception_artifact_count": observed_exception_artifacts,
        "credential_material_detected": credential_material_detected,
        "unsafe_error": (
            completed.returncode != 0
            or observed_reward_artifacts != 1
            or observed_trajectory_artifacts != 1
            or observed_exception_artifacts != 0
            or credential_material_detected
        ),
    }
    unsafe_audit_path = trial_dir / "unsafe-error-audit.json"
    unsafe_audit_path.write_text(json.dumps(unsafe_audit, indent=2, sort_keys=True) + "\n")
    if unsafe_audit["unsafe_error"]:
        status = {
            "schema_version": RESULT_SCHEMA_VERSION,
            "data_classification": manifest["data_classification"],
            "protocol_revision": PROTOCOL_REVISION,
            "split_revision": EXPECTED_SPLIT_REVISION,
            "attempt_status": (
                "unsafe"
                if credential_material_detected or observed_exception_artifacts != 0
                else "missing"
                if observed_reward_artifacts != 1 or observed_trajectory_artifacts != 1
                else "invalid"
            ),
            "verifier_passed": None,
            "unsafe_error": True,
            "unsafe_error_audit": unsafe_audit,
            "unsafe_error_audit_sha256": canonical_sha256(unsafe_audit),
            "task_role": "held_out_student_evaluation",
            "evaluation_actor_role": "local_student",
            "student_model_id": STUDENT_MODEL_ID,
            "student_model_sha256": STUDENT_MODEL_SHA256,
            "pair_id": manifest["pair_id"],
            "task_id": task["task_id"],
            "task_family": task["task_family"],
            "question_type": task["question_type"],
            "memory_checkpoint": manifest["memory_checkpoint"],
            "memory_contributions": manifest["memory_contributions"],
            "baseline_memory_contributions": manifest["baseline_memory_contributions"],
            "observed_memory_pages": memory_state.admitted_pages,
            "observed_memory_page_ids": list(memory_state.page_ids),
            "memory_provenance": memory_provenance_snapshot(index_path),
            "memory_condition": condition,
            "verifier_authority": "terminal-bench-executable",
            "retrieved_page_ids": [page.page_id for page in retrieval_result.pages],
            "expected_relevant_pages": list(task["expected_relevant_pages"]),
            "control_digest": digest,
            "control_snapshot": snapshot,
            "wiki_bytes": _wiki_bytes(wiki_dir),
        }
        (trial_dir / "result.json").write_text(
            json.dumps(status, indent=2, sort_keys=True) + "\n"
        )
        raise RuntimeError(
            f"Harbor attempt for {condition} is invalid or unsafe; inspect the local trial directory"
        )
    passed, trajectory_path, verifier_path, trajectory_metrics = _extract_harbor_result(
        jobs_dir,
        trial_dir,
        expected_atif_schema=str(run_environment["atif_schema_version"]),
    )
    retrieved_ids = [page.page_id for page in retrieval_result.pages]
    expected = list(task["expected_relevant_pages"])
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "data_classification": manifest["data_classification"],
        "protocol_revision": PROTOCOL_REVISION,
        "split_revision": EXPECTED_SPLIT_REVISION,
        "unsafe_error": unsafe_audit["unsafe_error"],
        "unsafe_error_audit": unsafe_audit,
        "unsafe_error_audit_sha256": canonical_sha256(unsafe_audit),
        "task_role": "held_out_student_evaluation",
        "evaluation_actor_role": "local_student",
        "student_model_id": STUDENT_MODEL_ID,
        "student_model_sha256": STUDENT_MODEL_SHA256,
        "run_id": f"{manifest['pair_id']}-{condition.lower()}",
        "pair_id": manifest["pair_id"],
        "task_id": task["task_id"],
        "task_family": task["task_family"],
        "question_type": task["question_type"],
        "memory_checkpoint": manifest["memory_checkpoint"],
        "memory_contributions": manifest["memory_contributions"],
        "baseline_memory_contributions": manifest["baseline_memory_contributions"],
        "observed_memory_pages": memory_state.admitted_pages,
        "observed_memory_page_ids": list(memory_state.page_ids),
        "memory_provenance": memory_provenance_snapshot(index_path),
        "memory_condition": condition,
        "verifier_passed": passed,
        "verifier_authority": "terminal-bench-executable",
        "retrieved_page_ids": retrieved_ids,
        "expected_relevant_pages": expected,
        "retrieval_covered": bool(set(retrieved_ids) & set(expected)) if expected else None,
        "retrieval_revision": retrieval_result.revision,
        "retrieval_top_k": retrieval_result.top_k,
        "retrieval_token_budget": retrieval_result.token_budget,
        "retrieval_seconds": round(retrieval_seconds, 6),
        "wiki_bytes": _wiki_bytes(wiki_dir),
        "latency_seconds": round(latency_seconds, 6),
        "control_digest": digest,
        "control_snapshot": snapshot,
        "trajectory_sha256": sha256_file(trajectory_path),
        "verifier_artifact_sha256": sha256_file(verifier_path),
        "trajectory_bytes": trajectory_path.stat().st_size,
        "verifier_artifact_bytes": verifier_path.stat().st_size,
        **trajectory_metrics,
    }
    (trial_dir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )

    other = "M2" if condition == "M0" else "M0"
    other_result_path = pair_dir / other / "result.json"
    if other_result_path.is_file():
        other_result = json.loads(other_result_path.read_text())
        m0, m2 = (result, other_result) if condition == "M0" else (other_result, result)
        assert_control_equivalence(m0, m2)
        (pair_dir / "pair.json").write_text(
            json.dumps(
                {
                    "pair_id": manifest["pair_id"],
                    "control_digest": digest,
                    "conditions": list(CONDITIONS),
                    "result_paths": ["M0/result.json", "M2/result.json"],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    if manifest["data_classification"] == MEASURED:
        completion_sha256 = _validate_student_completion(
            manifest,
            condition,
            trial_dir / "result.json",
            trajectory_path,
            verifier_path,
            unsafe_audit_path,
        )
        complete_attempt(condition, str(task["task_id"]), completion_sha256)
    return trial_dir


def plan_pair(manifest: Mapping[str, object], wiki_dir: Path, index_path: Path) -> dict[str, object]:
    validate_manifest(manifest)
    memory_state = verified_memory_state(manifest, wiki_dir, index_path)
    task = _mapping(manifest["task"], "task")
    controls = _mapping(manifest["controls"], "controls")
    retrieval_config = _mapping(controls["retrieval"], "controls.retrieval")
    m2 = retrieve(
        str(task["retrieval_query"]),
        wiki_dir,
        top_k=int(retrieval_config["top_k"]),
        token_budget=int(retrieval_config["token_budget"]),
    )
    return {
        "data_classification": manifest["data_classification"],
        "pair_id": manifest["pair_id"],
        "control_digest": canonical_sha256(control_snapshot(manifest)),
        "observed_memory_pages": memory_state.admitted_pages,
        "observed_memory_page_ids": list(memory_state.page_ids),
        "m0_retrieved_pages": [],
        "m2_retrieved_pages": [page.page_id for page in m2.pages],
        "note": "plan only; not a measured result",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run controlled Harbor M0/M2 trials.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in (
        "validate",
        "check-prereqs",
        "llama-command",
        "plan",
        "run",
        "run-condition",
    ):
        command = subparsers.add_parser(name)
        command.add_argument("--manifest", type=Path, required=True)
        if name in {"plan", "run", "run-condition"}:
            command.add_argument("--wiki-dir", type=Path, required=True)
            command.add_argument("--memory-index", type=Path, required=True)
        if name in {"run", "run-condition"}:
            command.add_argument("--runs-dir", type=Path, required=True)
        if name == "run-condition":
            command.add_argument("--condition", choices=CONDITIONS, required=True)
    args = parser.parse_args(argv)
    manifest = load_manifest(args.manifest)

    if args.command == "validate":
        validate_manifest(manifest)
        print("Manifest is structurally valid. Measured provenance was not inferred or filled.")
        return 0
    if args.command == "check-prereqs":
        versions = check_prerequisites(manifest)
        print(json.dumps(versions, indent=2, sort_keys=True))
        return 0
    if args.command == "llama-command":
        validate_manifest(manifest)
        print(shlex.join(build_llama_command(manifest)))
        return 0
    if args.command == "plan":
        print(
            json.dumps(
                plan_pair(manifest, args.wiki_dir, args.memory_index), indent=2, sort_keys=True
            )
        )
        return 0
    if args.command == "run-condition":
        trial_dir = run_condition(
            manifest,
            condition=args.condition,
            wiki_dir=args.wiki_dir,
            index_path=args.memory_index,
            runs_dir=args.runs_dir,
        )
        print(trial_dir)
        return 0
    pair_dir = run_pair(
        manifest,
        wiki_dir=args.wiki_dir,
        index_path=args.memory_index,
        runs_dir=args.runs_dir,
    )
    print(pair_dir)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ManifestError, PrerequisiteError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
