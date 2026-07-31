"""Paired verifier-authoritative result analysis for the pilot."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Iterable, Mapping, Sequence

try:
    from .experiment import CONDITIONS, MEASURED, ManifestError, assert_control_equivalence
except ImportError:  # Allow `python artifact_memory/analyze.py` from the project directory.
    from experiment import CONDITIONS, MEASURED, ManifestError, assert_control_equivalence


class AnalysisError(ValueError):
    """Raised when paired results are incomplete or could misstate evidence."""


@dataclass(frozen=True)
class Pair:
    m0: Mapping[str, object]
    m2: Mapping[str, object]

    @property
    def transfer(self) -> str:
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
        if isinstance(value, dict) and value.get("schema_version") == "paired-result-v1":
            results.append(value)
            continue
        skipped.append(location)
    return Discovery(results, skipped)


def _validate_result(result: Mapping[str, object]) -> None:
    required = (
        "data_classification",
        "pair_id",
        "task_id",
        "task_family",
        "question_type",
        "memory_checkpoint",
        "memory_contributions",
        "baseline_memory_contributions",
        "observed_memory_pages",
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
    if not isinstance(result["verifier_passed"], bool):
        raise AnalysisError("verifier_passed must be an authoritative boolean")
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


def _rate(passed: int, total: int) -> str:
    return "N/A" if total == 0 else f"{passed / total:.3f}"


def _counts(pairs: Iterable[Pair]) -> dict[str, int]:
    counts = {
        "positive_transfer": 0,
        "negative_transfer": 0,
        "stable_success": 0,
        "unresolved_task": 0,
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
                "m0_pass_rate": _rate(m0_passes, len(group)),
                "m2_pass_rate": _rate(m2_passes, len(group)),
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


def analyze_results(
    results: Iterable[Mapping[str, object]],
    output_dir: Path,
    *,
    allow_non_measured: bool = False,
    skipped: Sequence[str] = (),
) -> dict[str, Path]:
    pairs = pair_results(results, allow_non_measured=allow_non_measured)
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
    skipped_lines = "\n".join(f"- Skipped: `{location}`" for location in skipped) or "- None."
    summary = f"""# Paired pilot summary

**Data classification: {classification_label}.**

Terminal Bench executable verifier outcomes are authoritative. Learned-judge fields, if present in source records, were not read and cannot override verifier failures.

## Data completeness

- Paired result records analyzed: {len(pairs) * 2}
- Result files under the run tree that were not paired-result-v1 records: {len(skipped)}

{skipped_lines}

## Overall transfer

- Pairs: {len(pairs)}
- Positive transfer: {overall['positive_transfer']}
- Negative transfer: {overall['negative_transfer']}
- Stable success: {overall['stable_success']}
- Unresolved tasks: {overall['unresolved_task']}
- Retrieval coverage: {_rate(covered, relevant)} ({covered}/{relevant})

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
