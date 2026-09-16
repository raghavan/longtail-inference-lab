"""Bounded, local subprocess backends. No downloads or remote inference paths."""

from __future__ import annotations

from dataclasses import dataclass
from array import array
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import sys
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import wave

MAX_AUDIO_SECONDS = 30
MAX_INPUT_CHARS = 1200
MAX_OUTPUT_CHARS = 4000
SYSTEM_PROMPT = (
    "You are a helpful offline voice assistant. Answer in English, briefly and clearly, "
    "usually in two or three sentences. Say when you do not know. You have no internet "
    "or tools. Do not claim to perform actions. Use plain spoken text without Markdown."
)


class VoiceError(Exception):
    """Safe user-facing error; never wrap raw runtime output or input content."""


class Cancelled(VoiceError):
    pass


def check_cancel(cancel: threading.Event):
    if cancel.is_set():
        raise Cancelled("Operation cancelled.")


def stop_process(proc: subprocess.Popen):
    """Terminate the whole subprocess group, including subprocesses after leader exit."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait()


def process(args, cancel, timeout, *, input_text=None, stdout=subprocess.DEVNULL):
    """No shell, no utterances in logs; stdin carries synthesis text."""
    check_cancel(cancel)
    started = time.monotonic()
    try:
        proc = subprocess.Popen(
            [str(x) for x in args],
            stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
            stdout=stdout,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        raise VoiceError("A required local executable could not be started.") from exc
    try:
        if input_text is not None:
            proc.stdin.write(input_text.encode("utf-8"))
            proc.stdin.close()
        while proc.poll() is None:
            check_cancel(cancel)
            if time.monotonic() - started > timeout:
                raise VoiceError("Local processing exceeded its time limit.")
            cancel.wait(0.03)
        check_cancel(cancel)
        if proc.returncode != 0:
            raise VoiceError(
                "A local runtime failed. Check installation and device availability."
            )
    except BrokenPipeError as exc:
        raise VoiceError("A local runtime stopped before accepting input.") from exc
    finally:
        stop_process(proc)


def validate_text(text):
    text = text.strip()
    if not text:
        raise VoiceError("No speech or text was detected.")
    if len(text) > MAX_INPUT_CHARS:
        raise VoiceError("Input exceeds the 1,200-character limit.")
    return text


def validate_audio(path: Path):
    try:
        if not path.is_file():
            raise VoiceError("Input audio must be a readable regular WAV file.")
        if path.stat().st_size > 1_000_000:
            raise VoiceError("Audio exceeds the 30-second input limit.")
        with wave.open(str(path), "rb") as wav:
            if (
                wav.getnchannels(),
                wav.getsampwidth(),
                wav.getframerate(),
                wav.getcomptype(),
            ) != (1, 2, 16000, "NONE"):
                raise VoiceError("Input must be mono 16 kHz signed 16-bit PCM WAV.")
            frames = wav.getnframes()
            if not 1600 <= frames <= 16000 * MAX_AUDIO_SECONDS:
                raise VoiceError("Audio must last between 0.1 and 30 seconds.")
            pcm = wav.readframes(frames)
            if len(pcm) != frames * 2:
                raise VoiceError("Audio file is truncated.")
            samples = array("h", pcm)
            if sys.byteorder != "little":
                samples.byteswap()
            if max(abs(x) for x in samples) < 32:
                raise VoiceError("Recording is silent or too quiet to process.")
            return frames / 16000
    except (OSError, EOFError, wave.Error) as exc:
        raise VoiceError(
            "Input audio is missing or is not a readable WAV file."
        ) from exc


def private_workspace():
    # RAM-backed on Linux; no persistent recording/transcript cache by default.
    base = Path("/dev/shm")
    if not base.is_dir() or not os.access(base, os.W_OK):
        raise VoiceError(
            "A writable RAM-backed /dev/shm is required for transient audio."
        )
    return tempfile.TemporaryDirectory(prefix="local-voice-", dir=base)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, newurl):
        raise VoiceError("Local model server attempted an unsupported redirect.")


@dataclass(frozen=True)
class Settings:
    root: Path
    backend: str = "cpu"
    threads: int = 4
    max_tokens: int = 128
    answer_timeout: float = 120
    transcription_timeout: float = 60
    startup_timeout: float = 120
    capture_device: str = "default"
    playback_device: str = "default"
    system_prompt: str = SYSTEM_PROMPT

    def __post_init__(self):
        if not self.system_prompt.strip() or len(self.system_prompt) > 1200:
            raise VoiceError(
                "System prompt must contain between 1 and 1,200 characters."
            )
        if self.backend not in ("cpu", "cuda"):
            raise VoiceError("Backend must be cpu or cuda.")
        if not 1 <= self.threads <= 16 or not 1 <= self.max_tokens <= 384:
            raise VoiceError("Threads or output-token limit is out of range.")
        if not all(
            0 < x <= 600
            for x in (
                self.answer_timeout,
                self.transcription_timeout,
                self.startup_timeout,
            )
        ):
            raise VoiceError("Timeouts must be between zero and 600 seconds.")

    def binary(self, name):
        return self.root / "bin" / self.backend / name

    def model(self, kind):
        return (
            self.root
            / "models"
            / (
                "qwen2.5-1.5b-instruct-q4_k_m.gguf"
                if kind == "answer"
                else "ggml-tiny.en.bin"
            )
        )


def readiness(settings: Settings, *, verify_hashes=False, audio=False):
    checks = {}
    for name in ("llama-server", "whisper-cli"):
        checks[name] = os.access(settings.binary(name), os.X_OK)
    for name in ("answer", "speech"):
        path = settings.model(name)
        checks[name + "_model"] = path.is_file() and path.stat().st_size > 0
    checks["espeak-ng"] = shutil.which("espeak-ng") is not None
    checks["transient_audio"] = Path("/dev/shm").is_dir() and os.access(
        "/dev/shm", os.W_OK
    )
    if audio:
        checks["arecord"] = shutil.which("arecord") is not None
        checks["aplay"] = shutil.which("aplay") is not None
    if verify_hashes:
        lock_file = Path(__file__).resolve().parents[1] / "runtime-lock.json"
        if not lock_file.is_file():
            lock_file = settings.root / ("installed-" + settings.backend + ".json")
            try:
                lock = json.loads(lock_file.read_text())["lock"]
            except (OSError, KeyError, ValueError) as exc:
                raise VoiceError(
                    "Runtime installation manifest is missing or invalid."
                ) from exc
        else:
            lock = json.loads(lock_file.read_text())
        for kind, key in (("answer", "answer_model"), ("speech", "speech_model")):
            h = hashlib.sha256()
            try:
                with settings.model(kind).open("rb") as f:
                    for block in iter(lambda: f.read(1024 * 1024), b""):
                        h.update(block)
                checks[kind + "_sha256"] = h.hexdigest() == lock[key]["sha256"]
            except OSError:
                checks[kind + "_sha256"] = False
    return checks


class AnswerServer:
    """Owns a private loopback llama-server; never accepts a remote endpoint."""

    def __init__(self, settings):
        self.settings = settings
        self.proc = None
        self.url = None
        self.key = os.urandom(24).hex()
        self.http = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect()
        )

    def close(self):
        if self.proc is not None:
            stop_process(self.proc)
            self.proc = None
        self.url = None

    def _json(self, route, body=None, timeout=1):
        payload = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            self.url + route,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.key,
            },
        )
        with self.http.open(request, timeout=timeout) as response:
            data = response.read(1_000_001)
            if len(data) > 1_000_000:
                raise VoiceError("Local model response exceeded its size limit.")
            return json.loads(data)

    def start(self, cancel):
        if self.proc is not None and self.proc.poll() is None:
            return
        self.close()
        s = self.settings
        if not s.model("answer").is_file():
            raise VoiceError(
                "Local answer model is missing. Run the explicit setup step."
            )
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.url = "http://127.0.0.1:" + str(port)
        args = [
            s.binary("llama-server"),
            "-m",
            s.model("answer"),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--api-key",
            self.key,
            "-c",
            "2048",
            "-np",
            "1",
            "-t",
            str(s.threads),
            "-ngl",
            "0" if s.backend == "cpu" else "99",
            "--no-webui",
            "--no-warmup",
        ]
        if s.backend == "cuda":
            args += ["--device", "CUDA0"]
        try:
            self.proc = subprocess.Popen(
                [str(x) for x in args],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            deadline = time.monotonic() + s.startup_timeout
            while time.monotonic() < deadline:
                check_cancel(cancel)
                if self.proc.poll() is not None:
                    raise VoiceError("Local answer runtime exited during startup.")
                try:
                    if self._json("/health").get("status") == "ok":
                        return
                except (OSError, ValueError, urllib.error.URLError):
                    pass
                cancel.wait(0.1)
            raise VoiceError(
                "Local answer runtime did not become ready before its deadline."
            )
        except OSError as exc:
            self.close()
            raise VoiceError("Local answer runtime could not start.") from exc
        except BaseException:
            self.close()
            raise

    def answer(self, text, cancel):
        text = validate_text(text)
        self.start(cancel)
        results, errors = [], []
        body = {
            "messages": [
                {"role": "system", "content": self.settings.system_prompt},
                {"role": "user", "content": text},
            ],
            "max_tokens": self.settings.max_tokens,
            "temperature": 0,
            "seed": 42,
            "stream": False,
            "cache_prompt": False,
        }

        def request():
            try:
                results.append(
                    self._json(
                        "/v1/chat/completions", body, self.settings.answer_timeout
                    )
                )
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=request, daemon=True)
        thread.start()
        deadline = time.monotonic() + self.settings.answer_timeout
        try:
            while thread.is_alive():
                check_cancel(cancel)
                if time.monotonic() > deadline:
                    raise VoiceError("Local answer exceeded its time limit.")
                thread.join(0.03)
            check_cancel(cancel)
            if errors:
                raise VoiceError("Local answer request failed.")
            try:
                choice = results[0]["choices"][0]
                content = choice["message"]["content"]
                if choice.get("finish_reason") != "stop":
                    raise VoiceError(
                        "Answer reached its output limit; incomplete speech was discarded."
                    )
                if (
                    not isinstance(content, str)
                    or not content.strip()
                    or len(content) > MAX_OUTPUT_CHARS
                ):
                    raise VoiceError(
                        "Local model returned an empty or oversized answer."
                    )
                return content.strip()
            except (KeyError, IndexError, TypeError) as exc:
                raise VoiceError("Local model returned an invalid response.") from exc
        except BaseException:
            # A cancelled HTTP request must also stop generation on the server.
            self.close()
            thread.join(2)
            raise


class LocalBackend:
    def __init__(self, settings):
        self.settings = settings
        self.server = AnswerServer(settings)

    def close(self):
        self.server.close()

    def transcribe(self, wav, directory, cancel):
        validate_audio(wav)
        if not self.settings.model("speech").is_file():
            raise VoiceError(
                "Local transcription model is missing. Run the explicit setup step."
            )
        prefix = directory / "transcript"
        args = [
            self.settings.binary("whisper-cli"),
            "-m",
            self.settings.model("speech"),
            "-f",
            wav,
            "-l",
            "en",
            "-t",
            str(self.settings.threads),
            "-otxt",
            "-of",
            prefix,
            "-nt",
            "-np",
        ]
        if self.settings.backend == "cpu":
            args.append("-ng")
        process(args, cancel, self.settings.transcription_timeout)
        try:
            return validate_text(prefix.with_suffix(".txt").read_text())
        except OSError as exc:
            raise VoiceError("Transcription did not produce readable text.") from exc

    def answer(self, text, cancel):
        return self.server.answer(text, cancel)

    def synthesize(self, text, destination, cancel):
        if not text.strip() or len(text) > MAX_OUTPUT_CHARS:
            raise VoiceError("Answer cannot be synthesized within the output bounds.")
        process(
            ["espeak-ng", "-v", "en-us", "-s", "165", "-w", destination, "--stdin"],
            cancel,
            30,
            input_text=text,
        )
        try:
            with wave.open(str(destination), "rb") as wav:
                duration = wav.getnframes() / wav.getframerate()
                if not 0 < duration <= 120:
                    raise VoiceError("Synthesized speech exceeds the playback limit.")
        except (OSError, wave.Error, EOFError) as exc:
            raise VoiceError("Speech runtime produced invalid audio.") from exc

    def play(self, wav, cancel):
        process(["aplay", "-q", "-D", self.settings.playback_device, wav], cancel, 120)


@dataclass
class Result:
    transcript: str
    answer: str
    seconds: dict


def run_turn(
    backend,
    cancel,
    *,
    text=None,
    audio=None,
    output=None,
    play=False,
    state=lambda _: None,
):
    """A single isolated turn. Content leaves RAM only by explicit output request."""
    if (text is None) == (audio is None):
        raise VoiceError("Supply exactly one text or audio input.")
    times = {}
    with private_workspace() as tmp:
        directory = Path(tmp)
        check_cancel(cancel)
        if audio is not None:
            state("transcribing")
            started = time.monotonic()
            text = backend.transcribe(Path(audio), directory, cancel)
            times["transcription"] = round(time.monotonic() - started, 3)
        text = validate_text(text)
        state("answering")
        started = time.monotonic()
        answer = backend.answer(text, cancel)
        times["answer"] = round(time.monotonic() - started, 3)
        check_cancel(cancel)
        state("synthesizing")
        started = time.monotonic()
        wav = directory / "answer.wav"
        backend.synthesize(answer, wav, cancel)
        times["synthesis"] = round(time.monotonic() - started, 3)
        check_cancel(cancel)
        if play:
            state("speaking")
            backend.play(wav, cancel)
        check_cancel(cancel)
        if output is not None:
            # Exclusive creation protects an existing recording from accidental overwrite.
            fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(fd, "wb") as dest, wav.open("rb") as src:
                    shutil.copyfileobj(src, dest)
                check_cancel(cancel)
            except BaseException:
                Path(output).unlink(missing_ok=True)
                raise
        state("ready")
        return Result(text, answer, times)
