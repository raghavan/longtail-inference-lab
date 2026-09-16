"""ALSA capture and a single-operation button controller."""

from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import termios
import threading
import time
import tty

from .core import (
    Cancelled,
    MAX_AUDIO_SECONDS,
    VoiceError,
    check_cancel,
    private_workspace,
    run_turn,
    stop_process,
    validate_audio,
)


def record(settings, destination, finished, cancel):
    args = [
        "arecord",
        "-q",
        "-D",
        settings.capture_device,
        "-t",
        "wav",
        "-f",
        "S16_LE",
        "-r",
        "16000",
        "-c",
        "1",
        "-d",
        str(MAX_AUDIO_SECONDS),
        str(destination),
    ]
    check_cancel(cancel)
    try:
        proc = subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        raise VoiceError("Microphone capture could not start.") from exc
    stopped = False
    try:
        deadline = time.monotonic() + MAX_AUDIO_SECONDS + 3
        while proc.poll() is None:
            check_cancel(cancel)
            if finished.is_set():
                # SIGINT lets arecord finalize its WAV header before validation.
                os.killpg(proc.pid, signal.SIGINT)
                stopped = True
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired as exc:
                    raise VoiceError("Microphone did not stop cleanly.") from exc
                break
            if time.monotonic() > deadline:
                raise VoiceError("Microphone capture exceeded its time limit.")
            cancel.wait(0.03)
        check_cancel(cancel)
        if not stopped and proc.returncode != 0:
            raise VoiceError("Microphone is unavailable or its format is unsupported.")
        validate_audio(destination)
    finally:
        stop_process(proc)


class Controller:
    """Press: start, finish recording, or cancel current processing/playback."""

    def __init__(self, backend, notify=lambda state: None, recorder=record):
        self.backend = backend
        self.notify = notify
        self.recorder = recorder
        self.state = "ready"
        self.error = None
        self.cancel_event = threading.Event()
        self.finished = threading.Event()
        self.worker = None
        self.lock = threading.RLock()
        self.closed = False

    def _state(self, state):
        with self.lock:
            self.state = state
            self.notify(state)

    def press(self):
        with self.lock:
            if self.closed:
                return
            if self.worker is not None and self.worker.is_alive():
                if self.state == "recording":
                    self.finished.set()
                    self._state("finishing")
                else:
                    self.cancel_event.set()
                    self._state("cancelling")
                return
            self.cancel_event = threading.Event()
            self.finished = threading.Event()
            self.error = None
            self._state("recording")
            self.worker = threading.Thread(
                target=self._turn, name="voice-turn", daemon=True
            )
            self.worker.start()

    def cancel(self):
        with self.lock:
            if self.worker is not None and self.worker.is_alive():
                self.cancel_event.set()
                self._state("cancelling")

    def _turn(self):
        try:
            with private_workspace() as tmp:
                wav = Path(tmp) / "input.wav"
                self.recorder(
                    self.backend.settings, wav, self.finished, self.cancel_event
                )
                run_turn(
                    self.backend,
                    self.cancel_event,
                    audio=wav,
                    play=True,
                    state=self._state,
                )
        except Cancelled:
            self._state("ready")
        except (VoiceError, OSError) as exc:
            self.error = (
                str(exc)
                if isinstance(exc, VoiceError)
                else "Local device operation failed."
            )
            self._state("error")
        except Exception:
            self.error = (
                "Unexpected local processing failure. Retry or restart the application."
            )
            self._state("error")

    def close(self):
        with self.lock:
            self.closed = True
            self.cancel_event.set()
        if self.worker is not None:
            self.worker.join(8)
        self.backend.close()


class SerialButton:
    """115200-baud line protocol: PRESS/CANCEL inbound, STATE <state> outbound."""

    def __init__(self, device):
        self.fd = os.open(device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            self.original = termios.tcgetattr(self.fd)
            tty.setraw(self.fd)
            attrs = termios.tcgetattr(self.fd)
            attrs[4] = attrs[5] = termios.B115200
            termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
        except BaseException:
            os.close(self.fd)
            raise
        self.buffer = bytearray()
        self.last_press = 0.0

    def read_events(self):
        try:
            chunk = os.read(self.fd, 1024)
        except BlockingIOError:
            return []
        if not chunk:
            raise VoiceError("Button disconnected.")
        self.buffer.extend(chunk)
        if len(self.buffer) > 4096:
            self.buffer.clear()
            raise VoiceError("Button sent an oversized event.")
        events = []
        while b"\n" in self.buffer:
            line, _, rest = self.buffer.partition(b"\n")
            self.buffer = bytearray(rest)
            line = line.strip()
            if line == b"PRESS":
                now = time.monotonic()
                if now - self.last_press >= 0.2:
                    events.append("press")
                    self.last_press = now
            elif line == b"CANCEL":
                events.append("cancel")
        return events

    def state(self, state):
        try:
            os.write(self.fd, ("STATE " + state + "\n").encode("ascii"))
        except (OSError, UnicodeError):
            # The read loop handles disconnection and cancels the controller.
            pass

    def close(self):
        try:
            termios.tcsetattr(self.fd, termios.TCSANOW, self.original)
        except OSError:
            pass
        os.close(self.fd)
