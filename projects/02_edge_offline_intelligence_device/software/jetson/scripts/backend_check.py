#!/usr/bin/env python3
"""Small same-device CPU/CUDA check using authored inputs, not a quality benchmark."""

import argparse
import audioop
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import threading
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_voice.core import LocalBackend, Settings, SYSTEM_PROMPT, readiness, run_turn


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--root", type=Path, default=Path.home() / ".local/share/longtail-voice")
    args = parser.parse_args()
    app = Path(__file__).resolve().parents[1]
    root = args.root.expanduser().resolve()
    report = {
        "scope": "Physical Jetson same-device development comparison; authored inputs only",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "architecture": platform.machine(),
        "kernel": platform.release(),
        "python": platform.python_version(),
        "runtime_lock": json.loads((app / "runtime-lock.json").read_text()),
        "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
        "settings": {"threads": 4, "context": 2048, "max_tokens": 128,
                     "temperature": 0, "seed": 42, "history": "none", "retrieval": "none"},
        "order": ["cpu", "cuda", "cuda", "cpu"],
        "limits": "Two sessions per backend; cold means new server, not cold OS file cache. "
                  "Times exclude microphone capture and speaker playback. "
                  "Synthesis remains on CPU. No quality or percentile claim.",
        "trials": [],
    }
    for name in ("cpu", "cuda"):
        checks = readiness(Settings(root, backend=name), verify_hashes=True)
        if not all(checks.values()):
            raise RuntimeError(f"{name} readiness failed: {checks}")
    cancel = threading.Event()
    with tempfile.TemporaryDirectory(prefix="local-voice-check-", dir="/dev/shm") as td:
        raw, sample = Path(td) / "authored.wav", Path(td) / "input.wav"
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", "145", "-w", str(raw),
                        "What is the capital of France?"], check=True, timeout=30)
        with wave.open(str(raw), "rb") as wav:
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                raise RuntimeError("Unexpected synthetic input format")
            pcm, _ = audioop.ratecv(wav.readframes(wav.getnframes()), 2, 1,
                                   wav.getframerate(), 16000, None)
        with wave.open(str(sample), "wb") as wav:
            wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            wav.writeframes(pcm)
        report["fixture"] = {
            "text": "What is the capital of France?",
            "generator": "espeak-ng",
            "voice": "en-us",
            "words_per_minute": 145,
            "format": "mono 16 kHz signed 16-bit PCM WAV",
            "seconds": len(pcm) / 32000,
            "sha256": hashlib.sha256(sample.read_bytes()).hexdigest(),
        }
        for session, name in enumerate(report["order"]):
            backend = LocalBackend(Settings(root, backend=name))
            try:
                for index, kwargs in enumerate([
                    {"text": "Name two things to pack for a short walk."},
                    {"text": "In one short sentence, why do plants need sunlight?"},
                    {"audio": sample},
                ]):
                    result = run_turn(backend, cancel, **kwargs)
                    trial = {"session": session, "backend": name,
                             "server": "cold" if index == 0 else "warm",
                             "mode": "synthetic_audio" if "audio" in kwargs else "text",
                             **asdict(result)}
                    report["trials"].append(trial)
                    print(json.dumps(trial), flush=True)
            finally:
                backend.close()
    report["status"] = "passed"
    report["synthetic_fixtures_removed"] = True
    data = json.dumps(report, indent=2) + "\n"
    if args.output:
        with args.output.open("x") as out:
            out.write(data)
    else:
        print(data)


if __name__ == "__main__":
    main()
