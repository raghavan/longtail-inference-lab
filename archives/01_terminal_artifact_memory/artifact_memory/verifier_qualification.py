"""Bounded qualification checks for pinned task-specific executable verifiers.

Terminal Bench/Harbor supplies verifier semantics.  This module validates a
private, development-only qualification summary; it never reads verifier source,
hidden tests, reference solutions, or detailed mutation output.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping

try:
    from .sanitize import sha256_file
except ImportError:  # Allow direct execution from the project directory.
    from sanitize import sha256_file

QUALIFICATION_SCHEMA_VERSION = "verifier-qualification-v1"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
SAFE_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
TOP_LEVEL_KEYS = {
    "schema_version",
    "data_classification",
    "pins",
    "public_requirement_classes",
    "known_good_positive_control",
    "targeted_negative_controls",
    "clean_container_determinism",
    "reward_and_test_isolation",
    "eligible",
}
PROHIBITED_DETAIL_KEYS = {
    "argv",
    "command",
    "detailed_output",
    "hidden_test",
    "hidden_tests",
    "local_path",
    "mutation_patch",
    "reference_solution",
    "scanner_output",
    "solution",
    "verifier_implementation",
    "verifier_source",
}


class VerifierQualificationError(ValueError):
    """Raised when a task verifier is not eligible for measured use."""


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise VerifierQualificationError(f"{name} must be an object")
    return value


def _load(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise VerifierQualificationError("private verifier qualification record is unreadable") from exc
    if not isinstance(value, dict):
        raise VerifierQualificationError("private verifier qualification record must be an object")
    return value


def _exact_keys(value: Mapping[str, object], expected: set[str], name: str) -> None:
    actual = set(value)
    if actual != expected:
        raise VerifierQualificationError(
            f"{name} fields must match the compact schema; unexpected or missing: "
            + ", ".join(sorted(actual ^ expected))
        )


def _reject_details(value: object) -> None:
    if isinstance(value, Mapping):
        prohibited = sorted(str(key) for key in value if str(key) in PROHIBITED_DETAIL_KEYS)
        if prohibited:
            raise VerifierQualificationError(
                "qualification record contains prohibited verifier detail fields: "
                + ", ".join(prohibited)
            )
        for child in value.values():
            _reject_details(child)
    elif isinstance(value, list):
        for child in value:
            _reject_details(child)


def validate_qualification_record(
    record: Mapping[str, object],
    *,
    task_id: str,
    terminal_bench_revision: str,
    task_instruction_sha256: str,
    task_container_digest: str,
    verifier_bundle_sha256: str,
) -> None:
    """Require positive, mutation, determinism, and isolation qualification."""

    _reject_details(record)
    _exact_keys(record, TOP_LEVEL_KEYS, "qualification record")
    if record.get("schema_version") != QUALIFICATION_SCHEMA_VERSION:
        raise VerifierQualificationError(
            f"qualification schema must be {QUALIFICATION_SCHEMA_VERSION}"
        )
    if record.get("data_classification") != "development_only_not_measured":
        raise VerifierQualificationError("verifier qualification runs must be development-only")
    pins = _mapping(record.get("pins"), "qualification pins")
    expected_pins = {
        "task_id": task_id,
        "terminal_bench_revision": terminal_bench_revision,
        "task_instruction_sha256": task_instruction_sha256,
        "task_container_digest": task_container_digest,
        "verifier_bundle_sha256": verifier_bundle_sha256,
    }
    _exact_keys(pins, set(expected_pins), "qualification pins")
    for field, expected in expected_pins.items():
        if pins.get(field) != expected:
            raise VerifierQualificationError(f"qualification {field} does not match task provenance")
    for field in ("task_instruction_sha256", "verifier_bundle_sha256"):
        if not SHA256_RE.fullmatch(str(pins.get(field, ""))):
            raise VerifierQualificationError(f"qualification {field} must be SHA-256")

    requirement_classes = record.get("public_requirement_classes")
    if not isinstance(requirement_classes, list) or not requirement_classes or not all(
        isinstance(item, str) and SAFE_ID_RE.fullmatch(item) for item in requirement_classes
    ):
        raise VerifierQualificationError(
            "qualification must list safe public requirement classes"
        )
    if len(requirement_classes) != len(set(requirement_classes)):
        raise VerifierQualificationError("public requirement classes must be unique")

    positive = _mapping(record.get("known_good_positive_control"), "known-good control")
    _exact_keys(positive, {"attempts", "accepted"}, "known-good control")
    attempts = positive.get("attempts")
    accepted = positive.get("accepted")
    if type(attempts) is not int or attempts < 1 or type(accepted) is not int or accepted != attempts:
        raise VerifierQualificationError("verifier rejected a known-good positive control")

    negatives = record.get("targeted_negative_controls")
    if not isinstance(negatives, list) or not negatives:
        raise VerifierQualificationError("targeted plausible-negative controls are required")
    covered: set[str] = set()
    for value in negatives:
        control = _mapping(value, "targeted negative control")
        _exact_keys(
            control,
            {"control_id", "public_requirement_class", "attempts", "accepted"},
            "targeted negative control",
        )
        control_id = control.get("control_id")
        requirement_class = control.get("public_requirement_class")
        attempts = control.get("attempts")
        accepted = control.get("accepted")
        if not isinstance(control_id, str) or not SAFE_ID_RE.fullmatch(control_id):
            raise VerifierQualificationError("targeted negative control_id must be safe")
        if requirement_class not in requirement_classes:
            raise VerifierQualificationError(
                "targeted negative control names an unknown public requirement class"
            )
        if type(attempts) is not int or attempts < 1 or type(accepted) is not int or accepted != 0:
            raise VerifierQualificationError(
                "verifier accepted a targeted broken control; task is ineligible"
            )
        covered.add(str(requirement_class))
    missing = sorted(set(requirement_classes) - covered)
    if missing:
        raise VerifierQualificationError(
            "targeted negative controls do not cover public requirement classes: "
            + ", ".join(missing)
        )

    determinism = _mapping(record.get("clean_container_determinism"), "determinism checks")
    _exact_keys(
        determinism,
        {"runs", "consistent", "distinct_reward_values"},
        "determinism checks",
    )
    clean_runs = determinism.get("runs")
    if (
        type(clean_runs) is not int
        or clean_runs < 2
        or determinism.get("consistent") is not True
        or determinism.get("distinct_reward_values") != [1.0]
    ):
        raise VerifierQualificationError(
            "verifier qualification is nondeterministic across repeated clean containers"
        )

    isolation = _mapping(record.get("reward_and_test_isolation"), "isolation checks")
    _exact_keys(
        isolation,
        {"tamper_attempts", "tamper_accepts", "isolated"},
        "isolation checks",
    )
    tamper_attempts = isolation.get("tamper_attempts")
    if (
        isolation.get("isolated") is not True
        or type(tamper_attempts) is not int
        or tamper_attempts < 1
        or type(isolation.get("tamper_accepts")) is not int
        or isolation.get("tamper_accepts") != 0
    ):
        raise VerifierQualificationError(
            "verifier reward/test transport could not demonstrate bounded tamper resistance"
        )
    if record.get("eligible") is not True:
        raise VerifierQualificationError("qualification record marks the task ineligible")


def validate_qualification_path(
    path: Path,
    *,
    expected_record_sha256: str,
    task_id: str,
    terminal_bench_revision: str,
    task_instruction_sha256: str,
    task_container_digest: str,
    verifier_bundle_sha256: str,
) -> Mapping[str, object]:
    if not path.is_file():
        raise VerifierQualificationError("private verifier qualification record is missing")
    if not SHA256_RE.fullmatch(expected_record_sha256) or sha256_file(path) != expected_record_sha256:
        raise VerifierQualificationError("verifier qualification record hash mismatch")
    record = _load(path)
    validate_qualification_record(
        record,
        task_id=task_id,
        terminal_bench_revision=terminal_bench_revision,
        task_instruction_sha256=task_instruction_sha256,
        task_container_digest=task_container_digest,
        verifier_bundle_sha256=verifier_bundle_sha256,
    )
    return record
