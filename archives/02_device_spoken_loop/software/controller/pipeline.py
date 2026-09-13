"""The conversation controller: one interaction, timed stage by stage.

The two conditions under test in Experiment 02.1 are properties of this file
and nothing else. Residency decides whether a model pays its load cost inside
the interaction; synthesis granularity decides whether the first sentence is
spoken while the rest is still being generated.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Protocol

from .backends import LanguageModel, SpeechToText, TextToSpeech, scratch_dir
from .ledger import Interaction

SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

RESIDENCY_POLICIES = ("sequential", "resident")
SYNTHESIS_POLICIES = ("whole", "streamed")


class Player(Protocol):
    def play(self, wav_path: Path) -> None:
        """Submit audio and return once the first sample has been handed off."""

    def wait(self) -> None:
        """Block until queued audio has finished."""


class NullPlayer:
    """Accounts for submission cost without an audio device."""

    def play(self, wav_path: Path) -> None:
        time.sleep(0.005)

    def wait(self) -> None:
        return


@dataclass
class PipelineConfig:
    residency: str = "sequential"
    synthesis: str = "streamed"
    max_sentences: int = 4
    system_prompt: str = (
        "You are a small offline voice assistant. Answer in one to four short "
        "sentences. Lead with the direct answer. Do not use lists, markdown, or "
        "emoji, because your answer is spoken aloud. Say when you are unsure."
    )

    def __post_init__(self) -> None:
        if self.residency not in RESIDENCY_POLICIES:
            raise ValueError(f"residency must be one of {RESIDENCY_POLICIES}")
        if self.synthesis not in SYNTHESIS_POLICIES:
            raise ValueError(f"synthesis must be one of {SYNTHESIS_POLICIES}")

    @property
    def condition(self) -> str:
        return f"{self.residency}+{self.synthesis}"


@dataclass
class Turn:
    transcript: str
    answer: str
    t_complete_ms: float
    gap_max_ms: float
    sentences: int


def ensure_resident(stt: SpeechToText, llm: LanguageModel, tts: TextToSpeech) -> None:
    """Pay every load cost before measurement begins."""
    stt.load()
    llm.load()
    tts.load()


def release_all(stt: SpeechToText, llm: LanguageModel, tts: TextToSpeech) -> None:
    stt.unload()
    llm.unload()
    tts.unload()


def run_interaction(
    interaction: Interaction,
    finalize_recording: Callable[[], Path],
    stt: SpeechToText,
    llm: LanguageModel,
    tts: TextToSpeech,
    config: PipelineConfig,
    player: Player,
) -> Turn:
    """Run one question through the loop, writing stage timings as it goes."""
    sequential = config.residency == "sequential"
    started = time.perf_counter()

    with interaction.stage("endpoint"):
        wav_path = finalize_recording()

    if sequential:
        with interaction.stage("stt_load"):
            stt.load()
    else:
        interaction.skip("stt_load")

    with interaction.stage("stt_compute"):
        transcript = stt.transcribe(wav_path)

    with interaction.stage("prompt"):
        question = transcript.strip()

    if sequential:
        # Speech recognition is finished, so its memory is released before the
        # answer model is loaded. This is the discipline a smaller device forces.
        stt.unload()
        with interaction.stage("llm_load"):
            llm.load()
    else:
        interaction.skip("llm_load")

    stream = llm.stream(question)
    first_chunk, prefill_ms = _time_first_chunk(stream)
    interaction.durations_ms["llm_prefill"] = prefill_ms

    with interaction.stage("llm_first_sentence"):
        if config.synthesis == "streamed":
            head, tail = _read_until_sentence(stream, first_chunk)
        else:
            # Whole-answer synthesis cannot begin until generation finishes, so
            # the whole stream is consumed inside this stage.
            head, tail = _drain(stream, first_chunk), ""

    if sequential:
        llm.unload()
        with interaction.stage("tts_load"):
            tts.load()
    else:
        interaction.skip("tts_load")

    first_audio = scratch_dir() / f"{interaction.run_id}-{interaction.index}-0.wav"
    with interaction.stage("tts_first_chunk"):
        tts.synthesize(_trim(head), first_audio)

    with interaction.stage("audio_out"):
        player.play(first_audio)

    answer_parts = [head]
    gap_max_ms = 0.0
    sentences = 1

    if config.synthesis == "streamed" and tail is not None:
        remaining = _drain(stream, tail)
        for position, sentence in enumerate(_split_sentences(remaining), start=1):
            if sentences >= config.max_sentences:
                break
            gap_started = time.perf_counter()
            player.wait()
            gap_max_ms = max(gap_max_ms, (time.perf_counter() - gap_started) * 1000.0)
            chunk_path = scratch_dir() / f"{interaction.run_id}-{interaction.index}-{position}.wav"
            tts.synthesize(sentence, chunk_path)
            player.play(chunk_path)
            answer_parts.append(sentence)
            sentences += 1

    player.wait()
    t_complete_ms = (time.perf_counter() - started) * 1000.0

    if sequential:
        tts.unload()

    answer = " ".join(part.strip() for part in answer_parts if part.strip())
    return Turn(
        transcript=transcript,
        answer=answer,
        t_complete_ms=t_complete_ms,
        gap_max_ms=gap_max_ms,
        sentences=sentences,
    )


def _time_first_chunk(stream: Iterator[str]) -> tuple[str, float]:
    started = time.perf_counter()
    try:
        chunk = next(stream)
    except StopIteration:
        chunk = ""
    return chunk, (time.perf_counter() - started) * 1000.0


def _read_until_sentence(stream: Iterator[str], seed: str) -> tuple[str, str]:
    """Collect text until the first sentence boundary.

    Returns the first sentence and any text already read past it, so no token is
    dropped between the first spoken sentence and the rest of the answer.
    """
    buffer = seed
    for chunk in stream:
        buffer += chunk
        parts = SENTENCE_END.split(buffer, maxsplit=1)
        if len(parts) == 2:
            return parts[0], parts[1]
    return buffer, ""


def _drain(stream: Iterator[str], seed: str) -> str:
    return seed + "".join(stream)


def _split_sentences(text: str) -> list[str]:
    return [part.strip() for part in SENTENCE_END.split(text) if part.strip()]


def _trim(text: str) -> str:
    return " ".join(text.split())
