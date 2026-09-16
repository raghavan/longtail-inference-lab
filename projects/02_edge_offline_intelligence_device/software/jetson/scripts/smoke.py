#!/usr/bin/env python3
"""Real-model development checks using explicitly authored, synthetic input."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import platform
import resource
import socket
import sys
import threading
import time
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_voice.core import (
    LocalBackend,
    Settings,
    private_workspace,
    process,
    readiness,
    run_turn,
    validate_audio,
)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--root", type=Path, default=Path.home() / ".local/share/longtail-voice"
    )
    p.add_argument("--require-isolated-network", action="store_true")
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    # sysfs can retain the parent namespace's view; query the current namespace.
    interfaces = sorted(name for _, name in socket.if_nameindex())
    if a.require_isolated_network and interfaces != ["lo"]:
        p.error("This check must run in a network namespace containing loopback only.")
    settings = Settings(a.root.expanduser().resolve())
    checks = readiness(settings, verify_hashes=True)
    if not all(checks.values()):
        raise RuntimeError("Readiness failed: " + json.dumps(checks))
    report = {
        "scope": "Linux ARM64 VM CPU development checks; not Jetson measurements",
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "kernel": platform.release(),
        "network_interfaces": interfaces,
        "readiness": checks,
        "trials": [],
        "settings": {
            "threads": settings.threads,
            "context_tokens": 2048,
            "max_output_tokens": settings.max_tokens,
            "temperature": 0,
            "seed": 42,
            "history": "none",
            "retrieval": "none",
        },
    }
    backend = LocalBackend(settings)
    cancel = threading.Event()
    baseline = set(Path("/dev/shm").glob("local-voice-*"))
    try:
        started = time.monotonic()
        typed = run_turn(
            backend, cancel, text="Name two things to pack for a short walk."
        )
        report["trials"].append(
            {
                "mode": "text",
                "server": "cold",
                **asdict(typed),
                "total_seconds": round(time.monotonic() - started, 3),
            }
        )
        with private_workspace() as tmp:
            directory = Path(tmp)
            raw = directory / "authored.wav"
            sample = directory / "input.wav"
            authored = "What is the capital of France?"
            process(
                ["espeak-ng", "-v", "en-us", "-s", "145", "-w", raw, "--stdin"],
                cancel,
                10,
                input_text=authored,
            )
            process(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    raw,
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "-c:a",
                    "pcm_s16le",
                    sample,
                ],
                cancel,
                10,
            )
            duration = validate_audio(sample)
            for i in range(2):
                output = directory / ("answer-" + str(i) + ".wav")
                started = time.monotonic()
                result = run_turn(backend, cancel, audio=sample, output=output)
                with wave.open(str(output), "rb") as w:
                    out_seconds = round(w.getnframes() / w.getframerate(), 3)
                    assert w.getnframes() > 0 and w.getsampwidth() == 2
                report["trials"].append(
                    {
                        "mode": "synthetic_audio",
                        "server": "warm",
                        "authored_input": authored,
                        "input_seconds": duration,
                        "output_seconds": out_seconds,
                        **asdict(result),
                        "total_seconds": round(time.monotonic() - started, 3),
                    }
                )
    finally:
        backend.close()
    report["temporary_audio_removed"] = (
        set(Path("/dev/shm").glob("local-voice-*")) == baseline
    )
    assert report["temporary_audio_removed"]
    report["max_reaped_child_rss_kib"] = resource.getrusage(
        resource.RUSAGE_CHILDREN
    ).ru_maxrss
    report["memory_limit"] = (
        "Largest reaped child peak RSS, not simultaneous pipeline memory or Jetson RAM use"
    )
    report["status"] = "passed"
    data = json.dumps(report, indent=2) + "\n"
    if a.output:
        a.output.write_text(data)
    print(data)


if __name__ == "__main__":
    main()
