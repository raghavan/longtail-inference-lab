"""Speech, language, and synthesis backends behind one small interface.

Every backend exposes `load`, `unload`, and its one useful method, so the
residency policy under test is a property of the controller rather than of any
particular runtime. Real backends import their dependencies lazily, which keeps
the stub path importable with nothing installed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Protocol


class BackendError(RuntimeError):
    """Raised when a runtime is missing or refuses a request."""


class SpeechToText(Protocol):
    def load(self) -> None: ...
    def unload(self) -> None: ...
    def transcribe(self, wav_path: Path) -> str: ...


class LanguageModel(Protocol):
    def load(self) -> None: ...
    def unload(self) -> None: ...
    def stream(self, question: str) -> Iterator[str]: ...


class TextToSpeech(Protocol):
    def load(self) -> None: ...
    def unload(self) -> None: ...
    def synthesize(self, text: str, out_path: Path) -> Path: ...


# --------------------------------------------------------------------------
# Stub backends
# --------------------------------------------------------------------------
#
# The stubs sleep for a configurable time instead of computing. They exist to
# exercise the state machine, the residency policy, and the ledger without any
# model, audio device, or GPU. Their timings are invented and must never be
# reported as measurements.


@dataclass
class StubTimings:
    stt_load_s: float = 0.60
    stt_compute_s: float = 0.45
    llm_load_s: float = 1.20
    llm_prefill_s: float = 0.35
    llm_token_s: float = 0.012
    tts_load_s: float = 0.25
    tts_synth_per_char_s: float = 0.0022


class StubSpeechToText:
    def __init__(self, transcript: str, timings: StubTimings) -> None:
        self._transcript = transcript
        self._timings = timings
        self.loaded = False

    def load(self) -> None:
        if not self.loaded:
            time.sleep(self._timings.stt_load_s)
            self.loaded = True

    def unload(self) -> None:
        self.loaded = False

    def transcribe(self, wav_path: Path) -> str:
        if not self.loaded:
            raise BackendError("transcribe called before load")
        time.sleep(self._timings.stt_compute_s)
        return self._transcript


class StubLanguageModel:
    """Emits a fixed three-sentence answer one word at a time."""

    ANSWER = (
        "A tide is the rise and fall of sea level caused by the gravitational "
        "pull of the moon and sun. The moon dominates because it is much closer. "
        "Most coasts see two high tides each day."
    )

    def __init__(self, timings: StubTimings) -> None:
        self._timings = timings
        self.loaded = False

    def load(self) -> None:
        if not self.loaded:
            time.sleep(self._timings.llm_load_s)
            self.loaded = True

    def unload(self) -> None:
        self.loaded = False

    def stream(self, question: str) -> Iterator[str]:
        if not self.loaded:
            raise BackendError("stream called before load")
        time.sleep(self._timings.llm_prefill_s)
        for word in self.ANSWER.split(" "):
            time.sleep(self._timings.llm_token_s)
            yield word + " "


class StubTextToSpeech:
    def __init__(self, timings: StubTimings) -> None:
        self._timings = timings
        self.loaded = False

    def load(self) -> None:
        if not self.loaded:
            time.sleep(self._timings.tts_load_s)
            self.loaded = True

    def unload(self) -> None:
        self.loaded = False

    def synthesize(self, text: str, out_path: Path) -> Path:
        if not self.loaded:
            raise BackendError("synthesize called before load")
        time.sleep(self._timings.tts_synth_per_char_s * len(text))
        _write_silence(out_path, seconds=max(0.4, len(text) * 0.055))
        return out_path


def _write_silence(path: Path, seconds: float, rate: int = 22050) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(b"\x00\x00" * int(rate * seconds))


# --------------------------------------------------------------------------
# Real backends
# --------------------------------------------------------------------------


class FasterWhisperSpeechToText:
    """faster-whisper, which runs on CPU, CUDA, and Apple Silicon."""

    def __init__(self, model_name: str = "base.en", device: str = "auto",
                 compute_type: str = "default") -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def load(self) -> None:
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - depends on the host
            raise BackendError(
                "faster-whisper is not installed; see software/README.md"
            ) from exc
        self._model = WhisperModel(
            self.model_name, device=self.device, compute_type=self.compute_type
        )

    def unload(self) -> None:
        self._model = None

    def transcribe(self, wav_path: Path) -> str:
        if self._model is None:
            raise BackendError("transcribe called before load")
        segments, _info = self._model.transcribe(str(wav_path), beam_size=1)
        return " ".join(segment.text.strip() for segment in segments).strip()


class OllamaLanguageModel:
    """Streaming generation through a local Ollama server.

    Ollama is the simplest prototype runtime and behaves the same on macOS,
    Windows, and Linux, which is why the pilot starts here. The design direction
    expects llama.cpp to replace it once tighter memory control matters.
    """

    def __init__(self, model: str = "qwen3:4b", host: str = "http://127.0.0.1:11434",
                 system_prompt: str = "", max_tokens: int = 160,
                 temperature: float = 0.0) -> None:
        self.model = model
        self.host = host.rstrip("/")
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._loaded = False

    def load(self) -> None:
        """Ask Ollama to resident-load the weights without generating."""
        if self._loaded:
            return
        self._post("/api/generate", {"model": self.model, "prompt": "", "stream": False})
        self._loaded = True

    def unload(self) -> None:
        """Ask Ollama to release the weights immediately."""
        try:
            self._post(
                "/api/generate",
                {"model": self.model, "prompt": "", "keep_alive": 0, "stream": False},
            )
        except BackendError:
            pass
        self._loaded = False

    def stream(self, question: str) -> Iterator[str]:
        payload = {
            "model": self.model,
            "prompt": question,
            "system": self.system_prompt,
            "stream": True,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
            },
        }
        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request) as response:
                for raw in response:
                    line = raw.decode("utf-8").strip()
                    if not line:
                        continue
                    chunk = json.loads(line)
                    if chunk.get("response"):
                        yield chunk["response"]
                    if chunk.get("done"):
                        break
        except urllib.error.URLError as exc:
            raise BackendError(
                f"cannot reach Ollama at {self.host}; is `ollama serve` running?"
            ) from exc

    def _post(self, path: str, payload: dict) -> None:
        request = urllib.request.Request(
            f"{self.host}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(request).read()
        except urllib.error.URLError as exc:
            raise BackendError(f"cannot reach Ollama at {self.host}") from exc


class PiperTextToSpeech:
    """Piper via its command line binary."""

    def __init__(self, voice_path: Path, binary: str = "piper") -> None:
        self.voice_path = Path(voice_path)
        self.binary = binary

    def load(self) -> None:
        if shutil.which(self.binary) is None:
            raise BackendError(f"{self.binary!r} is not on PATH; see software/README.md")
        if not self.voice_path.exists():
            raise BackendError(f"Piper voice not found at {self.voice_path}")

    def unload(self) -> None:
        """Piper is a short-lived subprocess, so there is nothing resident."""

    def synthesize(self, text: str, out_path: Path) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [self.binary, "--model", str(self.voice_path), "--output_file", str(out_path)],
            input=text.encode("utf-8"),
            capture_output=True,
        )
        if result.returncode != 0:
            raise BackendError(f"piper failed: {result.stderr.decode('utf-8', 'replace')}")
        return out_path


def scratch_dir() -> Path:
    return Path(tempfile.gettempdir()) / "edge_voice_pilot"
