#!/usr/bin/env python3
"""Actual CLI failure/cancellation checks against installed Linux runtimes."""

import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import wave


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    app = Path(__file__).resolve().parents[1]
    report = {"scope": "Linux CPU actual CLI failure handling; no physical device"}
    base = [sys.executable, "-m", "local_voice"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, command, expected in [
            (
                "missing_runtime",
                base + ["--root", str(root), "ask", "--text", "Hello"],
                "not ready",
            ),
            ("oversized_text", base + ["ask", "--stdin"], "1,200-character"),
            (
                "output_limit",
                base
                + [
                    "--max-tokens",
                    "1",
                    "ask",
                    "--text",
                    "Explain why the sky is blue.",
                ],
                "output limit",
            ),
        ]:
            proc = subprocess.run(
                command,
                input="x" * 1201 if name == "oversized_text" else None,
                cwd=app,
                text=True,
                capture_output=True,
                timeout=30,
            )
            assert proc.returncode == 1, name
            assert expected in proc.stderr, name
            report[name] = "passed"
        silent = root / "silent.wav"
        with wave.open(str(silent), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(bytes(32000))
        proc = subprocess.run(
            base + ["ask", "--wav", str(silent)],
            cwd=app,
            text=True,
            capture_output=True,
            timeout=10,
        )
        assert proc.returncode == 1 and "silent" in proc.stderr
        report["silence"] = "passed"
    # An open stdin pipe must not prevent signal-based shutdown.
    waiting = subprocess.Popen(
        base + ["ask", "--stdin"],
        cwd=app,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(0.25)
        waiting.send_signal(signal.SIGINT)
        waiting.wait(timeout=3)
        stdout, stderr = waiting.communicate()
        assert (
            waiting.returncode == 130 and not stdout.strip() and "cancelled" in stderr
        )
        report["stdin_cancellation_before_eof"] = "passed"
    finally:
        if waiting.poll() is None:
            waiting.kill()
            waiting.wait()
    # Signal the actual application once its owned model server exists.
    proc = subprocess.Popen(
        base + ["ask", "--text", "Describe a garden in two sentences."],
        cwd=app,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    children = []
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            path = Path("/proc") / str(proc.pid) / "task" / str(proc.pid) / "children"
            children = path.read_text().split() if path.exists() else []
            if children:
                break
            if proc.poll() is not None:
                raise AssertionError(
                    "CLI exited before cancellation could be exercised"
                )
            time.sleep(0.01)
        assert children, "Model server was not observed"
        started = time.monotonic()
        proc.send_signal(signal.SIGINT)
        stdout, stderr = proc.communicate(timeout=5)
        assert proc.returncode == 130 and "cancelled" in stderr
        assert not stdout.strip(), "Cancelled result must not be printed"
        assert all(not (Path("/proc") / child).exists() for child in children)
        report["real_server_cancellation"] = "passed"
        report["cancellation_seconds"] = round(time.monotonic() - started, 3)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    report["status"] = "passed"
    data = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(data)
    print(data)


if __name__ == "__main__":
    main()
