"""Run the local voice loop as a pilot on ordinary hardware.

Two modes:

    dry-run      stub backends, no models, no audio device. Exercises the state
                 machine, the residency policy, and the ledger anywhere Python
                 runs. Its timings are invented and are never measurements.

    interactive  real backends. Press Enter to start speaking, Enter to stop,
                 then listen. This is the pilot that tells you whether the loop
                 is worth building on dedicated hardware.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

if __package__ in (None, ""):  # Allow `python controller/main.py`.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from controller import backends as backends_module
    from controller.audio import PushToTalkRecorder, SubprocessPlayer
    from controller.ledger import Interaction, LedgerWriter
    from controller.pipeline import (
        NullPlayer,
        PipelineConfig,
        ensure_resident,
        release_all,
        run_interaction,
    )
else:
    from . import backends as backends_module
    from .audio import PushToTalkRecorder, SubprocessPlayer
    from .ledger import Interaction, LedgerWriter
    from .pipeline import (
        NullPlayer,
        PipelineConfig,
        ensure_resident,
        release_all,
        run_interaction,
    )

DEFAULT_QUESTIONS = Path(__file__).resolve().parents[1] / "evaluations" / "question_set.jsonl"


def load_questions(path: Path, limit: int | None) -> list[dict]:
    questions = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions[:limit] if limit else questions


def build_backends(args: argparse.Namespace, transcript: str):
    if args.mode == "dry-run":
        timings = backends_module.StubTimings()
        return (
            backends_module.StubSpeechToText(transcript, timings),
            backends_module.StubLanguageModel(timings),
            backends_module.StubTextToSpeech(timings),
        )
    stt = backends_module.FasterWhisperSpeechToText(
        model_name=args.stt_model, device=args.stt_device
    )
    llm = backends_module.OllamaLanguageModel(
        model=args.llm_model,
        system_prompt=PipelineConfig().system_prompt,
        max_tokens=args.max_tokens,
    )
    tts = backends_module.PiperTextToSpeech(voice_path=Path(args.piper_voice))
    return stt, llm, tts


def provenance(args: argparse.Namespace, config: PipelineConfig) -> dict:
    return {
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": args.mode,
        "condition": config.condition,
        "residency": config.residency,
        "synthesis": config.synthesis,
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "models": {
            "stt": args.stt_model if args.mode != "dry-run" else "stub",
            "llm": args.llm_model if args.mode != "dry-run" else "stub",
            "tts": args.piper_voice if args.mode != "dry-run" else "stub",
        },
        "max_tokens": args.max_tokens,
        "is_measurement": args.mode != "dry-run",
        "note": (
            "Pilot on general-purpose hardware. Not the device, not Experiment "
            "02.1, and never pooled with device runs."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("dry-run", "interactive"), default="dry-run")
    parser.add_argument("--residency", choices=("sequential", "resident"), default="sequential")
    parser.add_argument("--synthesis", choices=("whole", "streamed"), default="streamed")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--limit", type=int, default=None, help="use the first N questions")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path("runs/pilot.jsonl"))
    parser.add_argument("--stt-model", default="base.en")
    parser.add_argument("--stt-device", default="auto")
    parser.add_argument("--llm-model", default="qwen3:4b")
    parser.add_argument("--piper-voice", default="voices/en_US-lessac-medium.onnx")
    parser.add_argument("--max-tokens", type=int, default=160)
    args = parser.parse_args(argv)

    config = PipelineConfig(residency=args.residency, synthesis=args.synthesis)
    questions = load_questions(args.questions, args.limit)
    if not questions:
        parser.error(f"no questions found in {args.questions}")

    run_id = uuid.uuid4().hex[:8]
    writer = LedgerWriter(args.out, provenance(args, config))
    scratch = backends_module.scratch_dir()

    stt, llm, tts = build_backends(args, questions[0]["question"])
    player = NullPlayer() if args.mode == "dry-run" else SubprocessPlayer()
    recorder = None if args.mode == "dry-run" else PushToTalkRecorder(scratch)

    if config.residency == "resident":
        print("Loading all three models before measurement...")
        ensure_resident(stt, llm, tts)

    print(f"run {run_id}  condition {config.condition}  {len(questions)} questions "
          f"x {args.repeats}")
    if args.mode == "dry-run":
        print("DRY RUN: stub backends. Timings are invented, not measurements.\n")

    index = 0
    try:
        for repeat in range(args.repeats):
            for question in questions:
                index += 1
                interaction = Interaction(
                    run_id=run_id,
                    index=index,
                    condition=config.condition,
                    question_id=question["id"],
                    meta={"repeat": repeat, "stratum": question.get("stratum", "")},
                )

                if args.mode == "dry-run":
                    stt._transcript = question["question"]  # noqa: SLF001 - stub only
                    interaction.durations_ms["capture"] = 0.0
                    finalize = lambda: scratch / "stub.wav"  # noqa: E731
                    _ensure_stub_wav(scratch / "stub.wav")
                else:
                    print(f"[{index}] {question['question']}")
                    input("  press Enter, speak, then press Enter again... ")
                    recorder.start()
                    input("  recording, press Enter to stop... ")
                    finalize = lambda: recorder.stop(f"{run_id}-{index}")

                turn = run_interaction(
                    interaction, finalize, stt, llm, tts, config, player
                )
                interaction.meta.update(
                    {
                        "transcript": turn.transcript,
                        "answer_chars": len(turn.answer),
                        "sentences": turn.sentences,
                        "t_complete_ms": round(turn.t_complete_ms, 3),
                        "gap_max_ms": round(turn.gap_max_ms, 3),
                    }
                )
                writer.write(interaction)
                print(f"  t_first_word {interaction.t_first_word_ms / 1000:6.2f}s"
                      f"   complete {turn.t_complete_ms / 1000:6.2f}s")
                if args.mode != "dry-run":
                    print(f"  {turn.answer}\n")
    except KeyboardInterrupt:
        print("\ninterrupted; partial ledger retained", file=sys.stderr)
    finally:
        if config.residency == "resident":
            release_all(stt, llm, tts)

    print(f"\nledger: {args.out}")
    return 0


def _ensure_stub_wav(path: Path) -> None:
    if not path.exists():
        backends_module._write_silence(path, seconds=0.2)  # noqa: SLF001 - stub only


if __name__ == "__main__":
    raise SystemExit(main())
