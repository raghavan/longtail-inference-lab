"""Command line and headless device entry points."""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import select
import signal
import sys
import threading
import time

from .core import (
    Cancelled,
    LocalBackend,
    Settings,
    VoiceError,
    readiness,
    run_turn,
    SYSTEM_PROMPT,
    check_cancel,
    validate_text,
)
from .device import Controller, SerialButton


def read_stdin_text(fd, cancel):
    """Wait for bounded UTF-8 input without making SIGINT/SIGTERM wait for EOF."""
    data = bytearray()
    while True:
        check_cancel(cancel)
        if not select.select([fd], [], [], 0.1)[0]:
            continue
        chunk = os.read(fd, min(4096, 4801 - len(data)))
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > 4800:
            raise VoiceError("Input exceeds the 1,200-character limit.")
    check_cancel(cancel)
    return validate_text(data.decode("utf-8"))


def parser():
    p = argparse.ArgumentParser(
        description="Offline local voice for Linux ARM64 / Jetson development"
    )
    p.add_argument(
        "--root", type=Path, default=Path.home() / ".local/share/longtail-voice"
    )
    p.add_argument("--backend", choices=["cpu", "cuda"], default="cpu")
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--max-tokens", type=int, default=128)
    p.add_argument("--answer-timeout", type=float, default=120)
    p.add_argument("--capture-device", default="default")
    p.add_argument("--playback-device", default="default")
    p.add_argument(
        "--system-prompt-file",
        type=Path,
        help="Optional local prompt file, at most 1,200 characters",
    )
    sub = p.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser(
        "doctor", help="Check local assets and executables without downloading"
    )
    doctor.add_argument("--verify-hashes", action="store_true")
    doctor.add_argument(
        "--audio",
        action="store_true",
        help="Also check audio executables; not device acceptance",
    )
    ask = sub.add_parser(
        "ask", help="Run one text or WAV input through real local models"
    )
    inputs = ask.add_mutually_exclusive_group(required=True)
    inputs.add_argument(
        "--text", help="Authored test text; use --stdin for private input"
    )
    inputs.add_argument(
        "--stdin", action="store_true", help="Read input text from stdin"
    )
    inputs.add_argument("--wav", type=Path)
    ask.add_argument(
        "--output",
        type=Path,
        help="Explicitly retain answer WAV; never overwrites an existing file",
    )
    ask.add_argument("--play", action="store_true", help="Play the answer through ALSA")
    ask.add_argument(
        "--show-text",
        action="store_true",
        help="Explicitly print transcript and answer",
    )
    device = sub.add_parser(
        "device", help="Press to record, press to finish, press while busy to cancel"
    )
    source = device.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--keyboard", action="store_true", help="Enter = press; c = cancel; q = quit"
    )
    source.add_argument("--serial", help="USB button serial device path")
    return p


def main():
    p = parser()
    args = p.parse_args()
    shutdown = threading.Event()
    old_handlers = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        old_handlers[sig] = signal.signal(sig, lambda *_: shutdown.set())
    backend = None
    controller = None
    serial = None
    try:
        prompt = SYSTEM_PROMPT
        if args.system_prompt_file:
            if not args.system_prompt_file.is_file():
                raise VoiceError("System prompt must be a readable regular file.")
            with args.system_prompt_file.open(encoding="utf-8") as stream:
                prompt = stream.read(1201)
        settings = Settings(
            args.root.expanduser().resolve(),
            args.backend,
            args.threads,
            args.max_tokens,
            args.answer_timeout,
            capture_device=args.capture_device,
            playback_device=args.playback_device,
            system_prompt=prompt,
        )
        if args.command == "doctor":
            checks = readiness(
                settings, verify_hashes=args.verify_hashes, audio=args.audio
            )
            print(
                json.dumps({"ready": all(checks.values()), "checks": checks}, indent=2)
            )
            return 0 if all(checks.values()) else 1
        checks = readiness(settings, audio=args.command == "device" or args.play)
        if not all(checks.values()):
            raise VoiceError(
                "Local runtime is not ready. Run doctor for asset and executable checks."
            )
        backend = LocalBackend(settings)
        if args.command == "ask":
            text = (
                read_stdin_text(sys.stdin.fileno(), shutdown)
                if args.stdin
                else args.text
            )
            result = run_turn(
                backend,
                shutdown,
                text=text,
                audio=args.wav,
                output=args.output,
                play=args.play,
            )
            data = (
                asdict(result)
                if args.show_text
                else {"status": "complete", "seconds": result.seconds}
            )
            print(json.dumps(data, indent=2))
            return 0
        if args.serial:
            serial = SerialButton(args.serial)

        def notify(state):
            event = {"state": state}
            if state == "error" and controller is not None:
                event["error"] = controller.error
            print(json.dumps(event), flush=True)
            if serial:
                serial.state(state)

        controller = Controller(backend, notify)
        notify("ready")
        source_fd = serial.fd if serial else sys.stdin.fileno()
        heartbeat = 0
        keyboard_buffer = bytearray()
        while not shutdown.is_set():
            if serial and time.monotonic() - heartbeat >= 1:
                serial.state(controller.state)
                heartbeat = time.monotonic()
            readable, _, _ = select.select([source_fd], [], [], 0.1)
            if not readable:
                continue
            if serial:
                events = serial.read_events()
            else:
                chunk = os.read(source_fd, 1024)
                if not chunk:
                    break
                keyboard_buffer.extend(chunk)
                if len(keyboard_buffer) > 4096:
                    raise VoiceError("Keyboard command exceeded its size limit.")
                events = []
                while b"\n" in keyboard_buffer:
                    line, _, rest = keyboard_buffer.partition(b"\n")
                    keyboard_buffer = bytearray(rest)
                    line = line.strip().lower()
                    if line == b"q":
                        shutdown.set()
                        events = []
                        break
                    if line in (b"", b"c"):
                        events.append("cancel" if line else "press")
            for event in events:
                if event == "press":
                    controller.press()
                else:
                    controller.cancel()
        return 0
    except Cancelled:
        print("Operation cancelled.", file=sys.stderr)
        return 130
    except VoiceError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError):
        print("Local file, device, or configuration operation failed.", file=sys.stderr)
        return 1
    finally:
        if controller:
            controller.close()
        elif backend:
            backend.close()
        if serial:
            serial.close()
        for sig, old in old_handlers.items():
            signal.signal(sig, old)


if __name__ == "__main__":
    raise SystemExit(main())
