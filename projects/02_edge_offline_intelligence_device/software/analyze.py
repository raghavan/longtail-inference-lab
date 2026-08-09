"""Summarize a ledger into the distributions the experiment actually asks for.

Averages are deliberately not reported alone. A voice appliance is judged by its
tail, so p95 leads and the per-stage breakdown explains it.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Sequence

STAGE_ORDER = (
    "endpoint",
    "stt_load",
    "stt_compute",
    "prompt",
    "llm_load",
    "llm_prefill",
    "llm_first_sentence",
    "tts_load",
    "tts_first_chunk",
    "audio_out",
)


def percentile(values: Sequence[float], fraction: float) -> float:
    """Nearest-rank percentile, which needs no interpolation assumption."""
    if not values:
        return float("nan")
    ordered = sorted(values)
    rank = max(1, min(len(ordered), int(round(fraction * len(ordered) + 0.5))))
    return ordered[rank - 1]


def load(path: Path) -> tuple[list[dict], list[dict]]:
    interactions, provenance = [], []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("record_type") == "interaction":
                interactions.append(record)
            elif record.get("record_type") == "provenance":
                provenance.append(record)
    return interactions, provenance


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--offset-ms", type=float, default=0.0,
                        help="measured acoustic offset added to every latency")
    parser.add_argument("--target-s", type=float, default=8.0)
    args = parser.parse_args(argv)

    interactions, provenance = load(args.ledger)
    if not interactions:
        print(f"no interactions in {args.ledger}")
        return 1

    measured = all(record.get("is_measurement") for record in provenance) and bool(provenance)
    if not measured:
        print("!! This ledger contains dry-run data. Timings are invented.\n")

    by_condition: dict[str, list[dict]] = defaultdict(list)
    for record in interactions:
        by_condition[record["condition"]].append(record)

    print(f"{'condition':22} {'n':>4} {'p50':>7} {'p95':>7} {'p99':>7} {'max':>7} {'>target':>8}")
    print("-" * 66)
    for condition in sorted(by_condition):
        values = [r["t_first_word_ms"] + args.offset_ms for r in by_condition[condition]]
        over = sum(1 for value in values if value / 1000.0 > args.target_s)
        print(
            f"{condition:22} {len(values):4d} "
            f"{percentile(values, 0.50) / 1000:7.2f} "
            f"{percentile(values, 0.95) / 1000:7.2f} "
            f"{percentile(values, 0.99) / 1000:7.2f} "
            f"{max(values) / 1000:7.2f} "
            f"{over / len(values):7.0%}"
        )

    print("\nper-stage median seconds")
    header = f"{'stage':20}" + "".join(f"{c[:14]:>15}" for c in sorted(by_condition))
    print(header)
    print("-" * len(header))
    for stage in STAGE_ORDER:
        row = f"{stage:20}"
        for condition in sorted(by_condition):
            stage_values = [
                r["durations_ms"].get(stage, 0.0) for r in by_condition[condition]
            ]
            row += f"{percentile(stage_values, 0.50) / 1000:15.3f}"
        print(row)

    print("\nWorst stage at p95, per condition:")
    for condition in sorted(by_condition):
        records = by_condition[condition]
        p95_value = percentile([r["t_first_word_ms"] for r in records], 0.95)
        nearest = min(records, key=lambda r: abs(r["t_first_word_ms"] - p95_value))
        worst = max(nearest["durations_ms"].items(), key=lambda item: item[1])
        print(f"  {condition:22} {worst[0]} at {worst[1] / 1000:.2f}s "
              f"of {nearest['t_first_word_ms'] / 1000:.2f}s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
