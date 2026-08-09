"""Capture and playback for the laptop pilot.

Both paths are deliberately thin. The pilot's job is to measure the shape of the
pipeline, not to be the audio design of the finished device, and every shortcut
taken here is recorded in `software/README.md` as a known measurement limit.
"""

from __future__ import annotations

import subprocess
import sys
import wave
from pathlib import Path

from .backends import BackendError

SAMPLE_RATE = 16000


class SubprocessPlayer:
    """Plays a WAV file through whatever the host provides.

    `play` returns as soon as the player process has been started, which is an
    approximation of "first sample submitted to the audio device". The offset
    between process start and audible sound is part of the acoustic calibration
    described in the experiment spec, and is not corrected here.
    """

    def __init__(self) -> None:
        self._command = self._detect()
        self._process: subprocess.Popen | None = None

    @staticmethod
    def _detect() -> list[str]:
        if sys.platform == "darwin":
            return ["afplay"]
        if sys.platform.startswith("win"):
            return [
                "powershell", "-NoProfile", "-Command",
                "(New-Object Media.SoundPlayer $args[0]).PlaySync();", "--",
            ]
        return ["aplay", "-q"]

    def play(self, wav_path: Path) -> None:
        self.wait()
        try:
            self._process = subprocess.Popen(
                [*self._command, str(wav_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise BackendError(
                f"no audio player found ({self._command[0]!r}); "
                "install it or run with --mode dry-run"
            ) from exc

    def wait(self) -> None:
        if self._process is not None:
            self._process.wait()
            self._process = None


class PushToTalkRecorder:
    """Records from the default input device between two key presses.

    A terminal cannot observe a held key reliably across platforms, so the pilot
    uses press-to-start and press-to-stop. This changes what `capture` means but
    not the primary metric, which begins at the moment recording stops.
    """

    def __init__(self, scratch: Path, sample_rate: int = SAMPLE_RATE) -> None:
        self.scratch = Path(scratch)
        self.sample_rate = sample_rate
        self.scratch.mkdir(parents=True, exist_ok=True)
        self._frames: list[bytes] = []
        self._stream = None

    def _sounddevice(self):
        try:
            import sounddevice
        except ImportError as exc:  # pragma: no cover - depends on the host
            raise BackendError(
                "sounddevice is not installed; see software/README.md"
            ) from exc
        return sounddevice

    def start(self) -> None:
        sounddevice = self._sounddevice()
        self._frames = []

        def callback(indata, _frames, _time, status):
            if status:  # overflow and underflow are worth seeing during a pilot
                print(f"  audio status: {status}", file=sys.stderr)
            self._frames.append(bytes(indata))

        self._stream = sounddevice.RawInputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            callback=callback,
        )
        self._stream.start()

    def stop(self, name: str) -> Path:
        """Close the stream and write the WAV. Timed as the `endpoint` stage."""
        if self._stream is None:
            raise BackendError("stop called before start")
        self._stream.stop()
        self._stream.close()
        self._stream = None
        path = self.scratch / f"{name}.wav"
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(self.sample_rate)
            handle.writeframes(b"".join(self._frames))
        return path
