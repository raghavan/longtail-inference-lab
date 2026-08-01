"""Paired verifier-authoritative result analysis for the pilot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Iterable, Mapping, Sequence

try:
    from .experiment import (
        CONDITIONS,
        MEASURED,
        RESULT_SCHEMA_VERSION,
        ManifestError,
        assert_control_equivalence,
    )
    from .preregistration import EXPECTED_SPLIT_REVISION, load_freeze
    from .transfer import STUDENT_MODEL_ID, STUDENT_MODEL_SHA256
except ImportError:  # Allow `python artifact_memory/analyze.py` from the project directory.
    from experiment import (
        CONDITIONS,
        MEASURED,
        RESULT_SCHEMA_VERSION,
        ManifestError,
        assert_control_equivalence,
    )
    from preregistration import EXPECTED_SPLIT_REVISION, load_freeze
    from transfer import STUDENT_MODEL_ID, STUDENT_MODEL_SHA256


class AnalysisError(ValueError):
    """Raised when paired results are incomplete or could misstate evidence."""


@dataclass(frozen=True)
class Pair:
    m0: Mapping[str, object]
    m2: Mapping[str, object]

    @property
    def transfer(self) -> str:
        if self.m0["verifier_passed"] is None or self.m2["verifier_passed"] is None:
            return "ineligible_pair"
        outcomes = (self.m0["verifier_passed"], self.m2["verifier_passed"])
        return {
            (False, True): "positive_transfer",
            (True, False): "negative_transfer",
            (True, True): "stable_success",
            (False, False): "unresolved_task",
        }[outcomes]  # type: ignore[index]


@dataclass(frozen=True)
class Discovery:
    results: list[dict[str, object]]
    skipped: list[str]


def discover_results(runs_dir: Path) -> Discovery:
    """Collect paired result records, refusing to silently shrink the corpus."""

    results: list[dict[str, object]] = []
    skipped: list[str] = []
    owned = {
        path
        for condition in CONDITIONS
        for path in runs_dir.glob(f"*/{condition}/result.json")
    }
    for path in sorted(owned):
        location = path.relative_to(runs_dir).as_posix()
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise AnalysisError(f"unreadable result record under the run tree: {location}") from exc
        if isinstance(value, dict) and value.get("schema_version") == RESULT_SCHEMA_VERSION:
            results.append(value)
            continue
        skipped.append(location)
    return Discovery(results, skipped)


def _validate_result(result: Mapping[str, object]) -> None:
    required = (
        "data_classification",
        "protocol_revision",
        "task_role",
        "evaluation_actor_role",
        "student_model_id",
        "student_model_sha256",
        "pair_id",
        "task_id",
        "task_family",
        "question_type",
        "memory_checkpoint",
        "memory_contributions",
        "baseline_memory_contributions",
        "observed_memory_pages",
        "observed_memory_page_ids",
        "memory_provenance",
        "memory_condition",
        "verifier_passed",
        "verifier_authority",
        "retrieved_page_ids",
        "expected_relevant_pages",
        "control_digest",
        "control_snapshot",
        "wiki_bytes",
    )
    missing = [field for field in required if field not in result]
    if missing:
        raise AnalysisError("incomplete result: " + ", ".join(missing))
    prohibited_teacher_outcomes = (
        "teacher_score",
        "teacher_outcome",
        "teacher_verifier_passed",
        "distiller_score",
        "model_confidence_score",
    )
    present = [field for field in prohibited_teacher_outcomes if field in result]
    if present:
        raise AnalysisError(
            "teacher/distiller/model scores are provenance, never student efficacy outcomes: "
            + ", ".join(present)
        )
    if (
        result["task_role"] != "held_out_student_evaluation"
        or result["evaluation_actor_role"] != "local_student"
        or result["student_model_id"] != STUDENT_MODEL_ID
        or result["student_model_sha256"] != STUDENT_MODEL_SHA256
    ):
        raise AnalysisError("paired efficacy scoring is restricted to the exact local student")
    attempt_status = result.get("attempt_status", "valid")
    if attempt_status not in {"valid", "invalid", "missing", "unsafe"}:
        raise AnalysisError("attempt_status is not recognized")
    if attempt_status == "valid" and not isinstance(result["verifier_passed"], bool):
        raise AnalysisError("valid verifier_passed must be an authoritative boolean")
    if attempt_status != "valid" and result["verifier_passed"] is not None:
        raise AnalysisError("invalid or unsafe attempts cannot claim a verifier outcome")
    audit = result.get("unsafe_error_audit")
    if result.get("data_classification") == MEASURED or audit is not None:
        if not isinstance(audit, Mapping):
            raise AnalysisError("result lacks an unsafe-error audit")
        if result.get("unsafe_error") is not audit.get("unsafe_error"):
            raise AnalysisError("result and unsafe-error audit disagree")
        if attempt_status == "valid" and audit.get("unsafe_error") is not False:
            raise AnalysisError("valid attempts cannot carry an unsafe error")
        if attempt_status != "valid" and audit.get("unsafe_error") is not True:
            raise AnalysisError("non-scorable attempts must carry an unsafe error")
    if result["verifier_authority"] != "terminal-bench-executable":
        raise AnalysisError("only the Terminal Bench executable verifier may score a result")
    if result["memory_condition"] not in {"M0", "M2"}:
        raise AnalysisError("pilot analysis accepts only M0 and M2")
    expected_pages = (
        result["baseline_memory_contributions"]
        if result["memory_condition"] == "M0"
        else result["memory_contributions"]
    )
    if expected_pages != result["observed_memory_pages"]:
        raise AnalysisError(
            "condition-specific memory contributions disagree with the observed admitted memory index"
        )
    if not isinstance(result["retrieved_page_ids"], list) or not isinstance(
        result["expected_relevant_pages"], list
    ):
        raise AnalysisError("retrieval records must contain explicit page lists")
    provenance = result["memory_provenance"]
    if not isinstance(provenance, list) or len(provenance) != result["observed_memory_pages"]:
        raise AnalysisError("memory provenance must account for every observed admitted page")
    page_ids: list[object] = []
    for entry in provenance:
        if not isinstance(entry, Mapping):
            raise AnalysisError("memory provenance entries must be objects")
        required_provenance = (
            "page_id",
            "task_role",
            "teacher_model_id",
            "distiller_model_id",
            "student_model_id",
            "student_model_sha256",
            "source_evidence_sha256",
            "sanitizer_revision",
            "approval_record_sha256",
        )
        missing_provenance = [field for field in required_provenance if not entry.get(field)]
        if missing_provenance:
            raise AnalysisError("incomplete memory provenance: " + ", ".join(missing_provenance))
        if (
            entry["task_role"] != "memory_build"
            or entry["teacher_model_id"] != "gpt-5.6-sol"
            or entry["distiller_model_id"] != "gpt-5.6-sol"
            or entry["student_model_id"] != STUDENT_MODEL_ID
            or entry["student_model_sha256"] != STUDENT_MODEL_SHA256
        ):
            raise AnalysisError("memory provenance conflates teacher, distiller, or student roles")
        page_ids.append(entry["page_id"])
    if sorted(str(value) for value in page_ids) != sorted(
        str(value) for value in result.get("observed_memory_page_ids", [])
    ):
        raise AnalysisError("memory provenance page IDs disagree with observed memory")


def pair_results(
    results: Iterable[Mapping[str, object]], *, allow_non_measured: bool = False
) -> list[Pair]:
    grouped: dict[tuple[object, object], dict[str, Mapping[str, object]]] = defaultdict(dict)
    classifications: set[object] = set()
    for result in results:
        _validate_result(result)
        classifications.add(result["data_classification"])
        key = (result["pair_id"], result["memory_checkpoint"])
        condition = str(result["memory_condition"])
        if condition in grouped[key]:
            raise AnalysisError(f"duplicate {condition} result for pair {key[0]}")
        grouped[key][condition] = result
    if not grouped:
        raise AnalysisError("no paired pilot results found")
    if not allow_non_measured and classifications != {MEASURED}:
        raise AnalysisError(
            "non-measured data refused; use the explicit development flag only for fixture smoke"
        )

    pairs: list[Pair] = []
    for key in sorted(grouped, key=lambda item: (int(item[1]), str(item[0]))):
        conditions = grouped[key]
        if set(conditions) != {"M0", "M2"}:
            raise AnalysisError(f"pair {key[0]} is missing M0 or M2")
        m0, m2 = conditions["M0"], conditions["M2"]
        try:
            assert_control_equivalence(m0, m2)
        except ManifestError as exc:
            raise AnalysisError(str(exc)) from exc
        for field in (
            "task_id",
            "task_family",
            "question_type",
            "memory_checkpoint",
            "memory_contributions",
            "baseline_memory_contributions",
            "data_classification",
        ):
            if m0[field] != m2[field]:
                raise AnalysisError(f"paired result differs in {field}")
        if m0["retrieved_page_ids"]:
            raise AnalysisError("M0 must contain no retrieved memory")
        pairs.append(Pair(m0, m2))
    return pairs


def _validate_frozen_pairs(pairs: Sequence[Pair], skipped: Sequence[str]) -> bool:
    frozen_flags = [
        pair.m0.get("data_classification") == MEASURED
        and pair.m2.get("data_classification") == MEASURED
        and pair.m0.get("split_revision") == EXPECTED_SPLIT_REVISION
        and pair.m2.get("split_revision") == EXPECTED_SPLIT_REVISION
        for pair in pairs
    ]
    if not any(frozen_flags):
        return False
    if not all(frozen_flags):
        raise AnalysisError("frozen and non-frozen pairs cannot share one analysis")
    if skipped:
        raise AnalysisError("frozen analysis refuses skipped or malformed result files")

    freeze = load_freeze()
    split = freeze.get("split")
    thresholds = freeze.get("thresholds")
    denominators = freeze.get("analysis_denominators")
    if not all(isinstance(value, Mapping) for value in (split, thresholds, denominators)):
        raise AnalysisError("frozen analysis controls are malformed")
    expected_tasks = list(split["held_out_evaluation_task_ids"])  # type: ignore[index]
    observed_tasks = [str(pair.m0["task_id"]) for pair in pairs]
    if (
        len(pairs) != 3
        or set(observed_tasks) != set(expected_tasks)
        or len(set(observed_tasks)) != 3
    ):
        raise AnalysisError("frozen analysis requires the exact three held-out pairs")
    success_thresholds = thresholds.get("success")
    if not isinstance(success_thresholds, Mapping) or {
        "complete_valid_pairs_required": success_thresholds.get("complete_valid_pairs_required"),
        "minimum_positive_transfers": success_thresholds.get("minimum_positive_transfers"),
        "minimum_pass_rate_lift": success_thresholds.get("minimum_pass_rate_lift"),
        "maximum_negative_transfers": success_thresholds.get("maximum_negative_transfers"),
        "maximum_unsafe_errors": success_thresholds.get("maximum_unsafe_errors"),
        "required_retrieval_coverage": success_thresholds.get("required_retrieval_coverage"),
    } != {
        "complete_valid_pairs_required": 3,
        "minimum_positive_transfers": 1,
        "minimum_pass_rate_lift": 1 / 3,
        "maximum_negative_transfers": 0,
        "maximum_unsafe_errors": 0,
        "required_retrieval_coverage": 1.0,
    }:
        raise AnalysisError("frozen success threshold contract differs from preregistration")
    if (
        denominators.get("m0_pass_rate") != 3
        or denominators.get("m2_pass_rate") != 3
        or denominators.get("transfer_classification") != 3
        or denominators.get("student_condition_attempts") != 6
        or denominators.get("unsafe_error_audit") != 6
    ):
        raise AnalysisError("frozen denominator contract is not exactly 3/3/3/6/6")
    page_mapping = split.get("page_mapping")
    if not isinstance(page_mapping, list):
        raise AnalysisError("frozen page mapping is unavailable")
    expected_pages = {
        str(item["held_out_task_id"]): [str(item["page_id"])]
        for item in page_mapping
        if isinstance(item, Mapping)
    }
    for pair in pairs:
        task_id = str(pair.m0["task_id"])
        for condition, result in (("M0", pair.m0), ("M2", pair.m2)):
            audit = result.get("unsafe_error_audit")
            if not isinstance(audit, Mapping) or {
                "schema_version": audit.get("schema_version"),
                "task_id": audit.get("task_id"),
                "memory_condition": audit.get("memory_condition"),
                "harbor_exit_zero": audit.get("harbor_exit_zero"),
                "reward_artifact_count": audit.get("reward_artifact_count"),
                "trajectory_artifact_count": audit.get("trajectory_artifact_count"),
                "exception_artifact_count": audit.get("exception_artifact_count"),
                "credential_material_detected": audit.get("credential_material_detected"),
                "unsafe_error": audit.get("unsafe_error"),
            } != {
                "schema_version": "student-unsafe-error-audit-v1",
                "task_id": task_id,
                "memory_condition": condition,
                "harbor_exit_zero": audit.get("harbor_exit_zero"),
                "reward_artifact_count": audit.get("reward_artifact_count"),
                "trajectory_artifact_count": audit.get("trajectory_artifact_count"),
                "exception_artifact_count": audit.get("exception_artifact_count"),
                "credential_material_detected": audit.get("credential_material_detected"),
                "unsafe_error": audit.get("unsafe_error"),
            }:
                raise AnalysisError("frozen unsafe-error audit artifact is incomplete")
            if not all(
                isinstance(audit.get(field), expected_type)
                for field, expected_type in (
                    ("harbor_exit_zero", bool),
                    ("reward_artifact_count", int),
                    ("trajectory_artifact_count", int),
                    ("exception_artifact_count", int),
                    ("credential_material_detected", bool),
                    ("unsafe_error", bool),
                )
            ):
                raise AnalysisError("frozen unsafe-error audit has invalid field types")
            audit_sha256 = hashlib.sha256(
                json.dumps(audit, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            if result.get("unsafe_error_audit_sha256") != audit_sha256:
                raise AnalysisError("frozen unsafe-error audit hash mismatch")
        if (
            pair.m0.get("memory_checkpoint") != 3
            or pair.m2.get("memory_checkpoint") != 3
            or pair.m0.get("expected_relevant_pages") != expected_pages.get(task_id)
            or pair.m2.get("expected_relevant_pages") != expected_pages.get(task_id)
        ):
            raise AnalysisError("frozen pair checkpoint, unsafe audit, or page mapping differs")
    return True


def _rate(passed: int, total: int) -> str:
    return "N/A" if total == 0 else f"{passed / total:.3f}"


def _counts(pairs: Iterable[Pair]) -> dict[str, int]:
    counts = {
        "positive_transfer": 0,
        "negative_transfer": 0,
        "stable_success": 0,
        "unresolved_task": 0,
        "ineligible_pair": 0,
    }
    for pair in pairs:
        counts[pair.transfer] += 1
    return counts


def _retrieval_coverage(pairs: Iterable[Pair]) -> tuple[int, int]:
    covered = 0
    relevant = 0
    for pair in pairs:
        expected = set(pair.m2["expected_relevant_pages"])  # type: ignore[arg-type]
        if not expected:
            continue
        relevant += 1
        retrieved = set(pair.m2["retrieved_page_ids"])  # type: ignore[arg-type]
        covered += bool(expected & retrieved)
    return covered, relevant


def _pair_rows(pairs: Sequence[Pair]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for pair in pairs:
        expected = set(pair.m2["expected_relevant_pages"])  # type: ignore[arg-type]
        retrieved = list(pair.m2["retrieved_page_ids"])  # type: ignore[arg-type]
        rows.append(
            {
                "data_classification": pair.m0["data_classification"],
                "pair_id": pair.m0["pair_id"],
                "task_id": pair.m0["task_id"],
                "task_family": pair.m0["task_family"],
                "question_type": pair.m0["question_type"],
                "memory_checkpoint": pair.m0["memory_checkpoint"],
                "memory_contributions": pair.m0["memory_contributions"],
                "observed_memory_pages": pair.m0["observed_memory_pages"],
                "m0_verifier_passed": pair.m0["verifier_passed"],
                "m2_verifier_passed": pair.m2["verifier_passed"],
                "transfer": pair.transfer,
                "retrieved_page_ids": ";".join(str(item) for item in retrieved),
                "expected_relevant_pages": ";".join(sorted(str(item) for item in expected)),
                "retrieval_covered": "N/A" if not expected else bool(expected & set(retrieved)),
                "wiki_bytes": pair.m2["wiki_bytes"],
                "m0_latency_seconds": pair.m0.get("latency_seconds", "N/A"),
                "m2_latency_seconds": pair.m2.get("latency_seconds", "N/A"),
                "m0_prompt_tokens": pair.m0.get("prompt_tokens", "N/A"),
                "m2_prompt_tokens": pair.m2.get("prompt_tokens", "N/A"),
                "m0_output_tokens": pair.m0.get("output_tokens", "N/A"),
                "m2_output_tokens": pair.m2.get("output_tokens", "N/A"),
                "m2_retrieval_seconds": pair.m2.get("retrieval_seconds", "N/A"),
                "control_digest": pair.m0["control_digest"],
            }
        )
    return rows


def _checkpoint_metrics(pairs: Sequence[Pair]) -> list[dict[str, object]]:
    grouped: dict[int, list[Pair]] = defaultdict(list)
    for pair in pairs:
        grouped[int(pair.m0["memory_checkpoint"])].append(pair)
    rows: list[dict[str, object]] = []
    for checkpoint in sorted(grouped):
        group = grouped[checkpoint]
        structural = [pair for pair in group if pair.m0["question_type"] == "structural"]
        m0_passes = sum(bool(pair.m0["verifier_passed"]) for pair in group)
        m2_passes = sum(bool(pair.m2["verifier_passed"]) for pair in group)
        complete_valid = all(pair.transfer != "ineligible_pair" for pair in group)
        structural_m0 = sum(bool(pair.m0["verifier_passed"]) for pair in structural)
        structural_m2 = sum(bool(pair.m2["verifier_passed"]) for pair in structural)
        counts = _counts(group)
        covered, relevant = _retrieval_coverage(group)
        contributions = {int(pair.m0["memory_contributions"]) for pair in group}
        wiki_sizes = {int(pair.m2["wiki_bytes"]) for pair in group}
        if len(contributions) != 1 or len(wiki_sizes) != 1:
            raise AnalysisError("checkpoint pairs disagree on memory contribution count or wiki size")
        contribution_count = contributions.pop()
        wiki_bytes = wiki_sizes.pop()
        net_structural = structural_m2 - structural_m0
        m0_latencies = [
            float(pair.m0["latency_seconds"])
            for pair in group
            if isinstance(pair.m0.get("latency_seconds"), (int, float))
        ]
        m2_latencies = [
            float(pair.m2["latency_seconds"])
            for pair in group
            if isinstance(pair.m2.get("latency_seconds"), (int, float))
        ]
        rows.append(
            {
                "checkpoint": checkpoint,
                "pairs": len(group),
                "m0_pass_rate": _rate(m0_passes, len(group)) if complete_valid else "N/A",
                "m2_pass_rate": _rate(m2_passes, len(group)) if complete_valid else "N/A",
                "structural_m0_pass_rate": _rate(structural_m0, len(structural)),
                "structural_m2_pass_rate": _rate(structural_m2, len(structural)),
                "structural_memory_lift": (
                    "N/A"
                    if not structural
                    else f"{(structural_m2 - structural_m0) / len(structural):.3f}"
                ),
                **counts,
                "retrieval_coverage": _rate(covered, relevant),
                "net_additional_structural_passes": net_structural,
                "verified_knowledge_yield": (
                    "N/A" if contribution_count == 0 else f"{net_structural / contribution_count:.3f}"
                ),
                "knowledge_efficiency_per_mb": (
                    "N/A" if wiki_bytes == 0 else f"{net_structural / (wiki_bytes / 1_000_000):.3f}"
                ),
                "wiki_bytes": wiki_bytes,
                "m0_median_latency_seconds": (
                    "N/A" if len(m0_latencies) != len(group) else f"{median(m0_latencies):.3f}"
                ),
                "m2_median_latency_seconds": (
                    "N/A" if len(m2_latencies) != len(group) else f"{median(m2_latencies):.3f}"
                ),
            }
        )
    return rows


def _family_rows(pairs: Sequence[Pair]) -> list[dict[str, object]]:
    grouped: dict[str, list[Pair]] = defaultdict(list)
    for pair in pairs:
        grouped[str(pair.m0["task_family"])].append(pair)
    rows: list[dict[str, object]] = []
    for family in sorted(grouped):
        group = grouped[family]
        m0 = sum(bool(pair.m0["verifier_passed"]) for pair in group)
        m2 = sum(bool(pair.m2["verifier_passed"]) for pair in group)
        counts = _counts(group)
        covered, relevant = _retrieval_coverage(group)
        rows.append(
            {
                "family": family,
                "pairs": len(group),
                "m0_pass_rate": _rate(m0, len(group)),
                "m2_pass_rate": _rate(m2, len(group)),
                "memory_lift": f"{(m2 - m0) / len(group):.3f}",
                "positive_transfer": counts["positive_transfer"],
                "negative_transfer": counts["negative_transfer"],
                "retrieval_coverage": _rate(covered, relevant),
            }
        )
    return rows


def _markdown_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def _analyze_incomplete_frozen(
    results: Sequence[Mapping[str, object]], output_dir: Path, skipped: Sequence[str]
) -> dict[str, Path]:
    if skipped:
        raise AnalysisError("frozen analysis refuses malformed result files")
    freeze = load_freeze()
    split = freeze.get("split")
    if not isinstance(split, Mapping):
        raise AnalysisError("frozen split is malformed")
    expected_tasks = {str(value) for value in split["held_out_evaluation_task_ids"]}  # type: ignore[index]
    slots: dict[tuple[str, str], Mapping[str, object]] = {}
    for result in results:
        _validate_result(result)
        task_id = str(result["task_id"])
        condition = str(result["memory_condition"])
        if (
            result.get("data_classification") != MEASURED
            or result.get("split_revision") != EXPECTED_SPLIT_REVISION
            or task_id not in expected_tasks
        ):
            raise AnalysisError("incomplete frozen analysis contains an out-of-freeze result")
        key = (task_id, condition)
        if key in slots:
            raise AnalysisError(f"duplicate {condition} result for task {task_id}")
        audit = result["unsafe_error_audit"]
        if result.get("unsafe_error_audit_sha256") != hashlib.sha256(
            json.dumps(audit, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest():
            raise AnalysisError("frozen unsafe-error audit hash mismatch")
        slots[key] = result
    expected_slots = {(task, condition) for task in expected_tasks for condition in CONDITIONS}
    missing = len(expected_slots - set(slots))
    invalid = sum(value.get("attempt_status", "valid") != "valid" for value in slots.values())
    unsafe = sum(value.get("unsafe_error") is True for value in slots.values())
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["task_id", "memory_condition", "attempt_status", "unsafe_error"]
        )
        writer.writeheader()
        for task_id, condition in sorted(expected_slots):
            result = slots.get((task_id, condition))
            writer.writerow(
                {
                    "task_id": task_id,
                    "memory_condition": condition,
                    "attempt_status": "missing" if result is None else result.get("attempt_status", "valid"),
                    "unsafe_error": "N/A" if result is None else result.get("unsafe_error"),
                }
            )
    summary_path = output_dir / "summary.md"
    summary_path.write_text(
        "# Paired pilot summary\n\n"
        "**Data classification: MEASURED RESULTS.**\n\n"
        "## Data completeness\n\n"
        f"- Fixed M0 denominator: 3\n- Fixed M2 denominator: 3\n"
        f"- Fixed transfer denominator: 3\n- Fixed student-attempt denominator: 6\n"
        f"- Fixed unsafe-error-audit denominator: 6\n- Recorded attempts: {len(slots)}\n"
        f"- Missing attempts: {missing}\n- Invalid or ineligible attempts: {invalid}\n"
        f"- Unsafe errors: {unsafe}\n- Frozen success verdict: INCONCLUSIVE / NO-GO\n\n"
        "No missing or non-scorable attempt is treated as an executable-verifier failure.\n"
    )
    transfer_path = output_dir / "paired_transfer_table.md"
    transfer_path.write_text(
        "# Paired transfer table\n\nTransfer classification is unavailable because the frozen corpus is incomplete or ineligible.\n"
    )
    return {"results_csv": csv_path, "summary": summary_path, "paired_transfer_table": transfer_path}


def analyze_results(
    results: Iterable[Mapping[str, object]],
    output_dir: Path,
    *,
    allow_non_measured: bool = False,
    skipped: Sequence[str] = (),
) -> dict[str, Path]:
    materialized = list(results)
    frozen_records = [
        result
        for result in materialized
        if result.get("data_classification") == MEASURED
        and result.get("split_revision") == EXPECTED_SPLIT_REVISION
    ]
    if frozen_records and (
        len(frozen_records) < 6
        or any(result.get("attempt_status", "valid") != "valid" for result in frozen_records)
    ):
        return _analyze_incomplete_frozen(materialized, output_dir, skipped)
    pairs = pair_results(materialized, allow_non_measured=allow_non_measured)
    frozen_analysis = _validate_frozen_pairs(pairs, skipped)
    rows = _pair_rows(pairs)
    checkpoint_rows = _checkpoint_metrics(pairs)
    checkpoint_by_id = {int(row["checkpoint"]): row for row in checkpoint_rows}
    for row in rows:
        checkpoint = checkpoint_by_id[int(row["memory_checkpoint"])]
        row.update(
            {
                "checkpoint_m0_pass_rate": checkpoint["m0_pass_rate"],
                "checkpoint_m2_pass_rate": checkpoint["m2_pass_rate"],
                "checkpoint_positive_transfer": checkpoint["positive_transfer"],
                "checkpoint_negative_transfer": checkpoint["negative_transfer"],
                "checkpoint_stable_success": checkpoint["stable_success"],
                "checkpoint_unresolved_task": checkpoint["unresolved_task"],
                "checkpoint_retrieval_coverage": checkpoint["retrieval_coverage"],
                "checkpoint_verified_knowledge_yield": checkpoint["verified_knowledge_yield"],
            }
        )
    family_rows = _family_rows(pairs)
    classifications = sorted({str(pair.m0["data_classification"]) for pair in pairs})
    classification_label = (
        "MEASURED RESULTS"
        if classifications == [MEASURED]
        else "NON-MEASURED DEVELOPMENT OR SYNTHETIC FIXTURE DATA"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    overall = _counts(pairs)
    covered, relevant = _retrieval_coverage(pairs)
    m0_passes = sum(bool(pair.m0["verifier_passed"]) for pair in pairs)
    m2_passes = sum(bool(pair.m2["verifier_passed"]) for pair in pairs)
    attempts = [result for pair in pairs for result in (pair.m0, pair.m2)]
    invalid_attempts = sum(result.get("attempt_status", "valid") != "valid" for result in attempts)
    missing_attempts = sum(result.get("attempt_status") == "missing" for result in attempts)
    unsafe_status_attempts = sum(result.get("attempt_status") == "unsafe" for result in attempts)
    unsafe_attempts = sum(result.get("unsafe_error") is True for result in attempts)
    frozen_success = (
        frozen_analysis
        and len(pairs) == 3
        and invalid_attempts == 0
        and unsafe_attempts == 0
        and overall["positive_transfer"] >= 1
        and (m2_passes - m0_passes) / 3 >= 1 / 3
        and overall["negative_transfer"] == 0
        and covered == relevant == 3
    )
    frozen_verdict = (
        f"- Frozen success verdict: {'PASS' if frozen_success else 'INCONCLUSIVE / NO-GO'}"
        if frozen_analysis
        else "- Frozen success verdict: N/A (non-frozen analysis)"
    )
    skipped_lines = "\n".join(f"- Skipped: `{location}`" for location in skipped) or "- None."
    summary = f"""# Paired pilot summary

**Data classification: {classification_label}.**

Terminal Bench executable verifier outcomes from the exact local Qwen student are authoritative. Cloud-teacher outcomes, model confidence, narrative success claims, tool-exit impressions, distillation quality, and learned-judge fields are not efficacy outcomes and cannot override verifier failures.

## Data completeness

- Paired result records analyzed: {len(pairs) * 2}
- Fixed student-attempt denominator: {len(attempts)}/6
- Invalid or ineligible attempts: {invalid_attempts}
- Missing-artifact attempts: {missing_attempts}
- Explicitly unsafe attempts: {unsafe_status_attempts}
- Unsafe-error audits: {unsafe_attempts}/6
- Result files under the run tree that were not student-paired-result-v2 records: {len(skipped)}

{skipped_lines}

## Overall transfer

- Pairs: {len(pairs)}
- Positive transfer: {overall['positive_transfer']}
- Negative transfer: {overall['negative_transfer']}
- Stable success: {overall['stable_success']}
- Unresolved tasks: {overall['unresolved_task']}
- Ineligible pairs: {overall['ineligible_pair']}
- Retrieval coverage: {_rate(covered, relevant)} ({covered}/{relevant})
{frozen_verdict}

## Checkpoints

{_markdown_table(
    ["Checkpoint", "M0 pass", "M2 pass", "Structural M0", "Structural M2", "Structural lift", "Positive", "Negative", "Stable", "Unresolved", "Retrieval coverage", "Verified knowledge yield", "Wiki bytes", "M0 median seconds", "M2 median seconds"],
    ([row['checkpoint'], row['m0_pass_rate'], row['m2_pass_rate'], row['structural_m0_pass_rate'], row['structural_m2_pass_rate'], row['structural_memory_lift'], row['positive_transfer'], row['negative_transfer'], row['stable_success'], row['unresolved_task'], row['retrieval_coverage'], row['verified_knowledge_yield'], row['wiki_bytes'], row['m0_median_latency_seconds'], row['m2_median_latency_seconds']] for row in checkpoint_rows),
)}

## Task families

{_markdown_table(
    ["Family", "Pairs", "M0 pass", "M2 pass", "Lift", "Positive", "Negative", "Retrieval coverage"],
    ([row['family'], row['pairs'], row['m0_pass_rate'], row['m2_pass_rate'], row['memory_lift'], row['positive_transfer'], row['negative_transfer'], row['retrieval_coverage']] for row in family_rows),
)}

Verified knowledge yield is net additional structural verifier passes divided by verified memory contributions. Negative transfer remains visible separately and is never hidden by the net value.
"""
    summary_path = output_dir / "summary.md"
    summary_path.write_text(summary)

    transfer_path = output_dir / "paired_transfer_table.md"
    transfer_path.write_text(
        "# Paired transfer table\n\n"
        f"**Data classification: {classification_label}.**\n\n"
        + _markdown_table(
            ["Pair", "Task", "Checkpoint", "M0 verifier", "M2 verifier", "Classification", "Retrieved pages"],
            (
                [
                    row["pair_id"],
                    row["task_id"],
                    row["memory_checkpoint"],
                    row["m0_verifier_passed"],
                    row["m2_verifier_passed"],
                    row["transfer"],
                    row["retrieved_page_ids"] or "none",
                ]
                for row in rows
            ),
        )
        + "\n"
    )
    return {
        "results_csv": csv_path,
        "summary": summary_path,
        "paired_transfer_table": transfer_path,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate paired CSV and Markdown analysis.")
    parser.add_argument("--runs-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--include-non-measured",
        action="store_true",
        help="explicitly allow fixture/development data; outputs are prominently labeled",
    )
    args = parser.parse_args(argv)
    discovery = discover_results(args.runs_dir)
    outputs = analyze_results(
        discovery.results,
        args.output_dir,
        allow_non_measured=args.include_non_measured,
        skipped=discovery.skipped,
    )
    print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
