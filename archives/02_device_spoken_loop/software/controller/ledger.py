"""Per-stage latency ledger for the local voice loop.

Stage names match the ledger table in
`experiments/01_spoken_latency_and_residency.md` so that a laptop pilot and a
later device run are read by the same analysis script. The pilot and the device
are different hardware conditions and are never pooled; sharing the schema only
means the same questions can be asked of both.
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Mapping

STAGES = (
    "capture",
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

# Everything between button release and the first audio sample. `capture` is the
# user speaking, so it is excluded from the primary metric by definition.
FIRST_WORD_STAGES = tuple(stage for stage in STAGES if stage != "capture")


class LedgerError(RuntimeError):
    """Raised when a stage name is not part of the frozen schema."""


@dataclass
class Interaction:
    """One question and answer, timed stage by stage."""

    run_id: str
    index: int
    condition: str
    question_id: str
    durations_ms: dict[str, float] = field(default_factory=dict)
    meta: dict[str, object] = field(default_factory=dict)

    @contextmanager
    def stage(self, name: str) -> Iterator[None]:
        if name not in STAGES:
            raise LedgerError(f"unknown stage {name!r}; schema is frozen to {STAGES}")
        started = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - started) * 1000.0
            self.durations_ms[name] = self.durations_ms.get(name, 0.0) + elapsed

    def skip(self, name: str) -> None:
        """Record a stage as zero cost.

        A resident model still passes through its load stage; the stage simply
        costs nothing. Recording the zero explicitly keeps every interaction
        shaped identically, so a missing key always means a bug rather than a
        policy difference.
        """
        if name not in STAGES:
            raise LedgerError(f"unknown stage {name!r}; schema is frozen to {STAGES}")
        self.durations_ms.setdefault(name, 0.0)

    @property
    def t_first_word_ms(self) -> float:
        return sum(self.durations_ms.get(stage, 0.0) for stage in FIRST_WORD_STAGES)

    def as_record(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "index": self.index,
            "condition": self.condition,
            "question_id": self.question_id,
            "t_first_word_ms": round(self.t_first_word_ms, 3),
            "durations_ms": {k: round(v, 3) for k, v in self.durations_ms.items()},
            "meta": self.meta,
        }


class LedgerWriter:
    """Appends one JSON line per interaction."""

    def __init__(self, path: Path, provenance: Mapping[str, object]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._provenance = dict(provenance)
        if not self.path.exists():
            self._append({"record_type": "provenance", **self._provenance})

    def _append(self, record: Mapping[str, object]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def write(self, interaction: Interaction) -> None:
        self._append({"record_type": "interaction", **interaction.as_record()})
