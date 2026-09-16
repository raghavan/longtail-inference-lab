#!/usr/bin/env python3
"""Linux VM check of the actual service sandbox and USB-serial protocol.

Creates and removes one uniquely named temporary system service. Uses a pseudo
terminal and an intentionally nonexistent microphone; never captures host audio.
"""

import argparse
import json
import os
from pathlib import Path
import pty
import pwd
import select
import subprocess
import tempfile
import time
import uuid

from service_unit import unit, quoted


def command(*args, check=True):
    result = subprocess.run(
        args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or "Service check command failed")
    return result.stdout


def wait_for(fd, expected, timeout=15):
    deadline = time.monotonic() + timeout
    data = b""
    while time.monotonic() < deadline:
        if select.select([fd], [], [], 0.2)[0]:
            data += os.read(fd, 4096)
            if expected in data:
                return
    raise RuntimeError("Service did not emit the expected serial state")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    app = Path(__file__).resolve().parents[1]
    root = Path.home() / ".local/share/longtail-voice"
    user = pwd.getpwuid(os.getuid()).pw_name
    name = "longtail-voice-vm-check-" + uuid.uuid4().hex[:8] + ".service"
    unit_path = "/run/systemd/system/" + name
    master, slave = pty.openpty()
    report = {
        "scope": "Linux VM service and virtual serial checks; no physical microphone or button"
    }
    try:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_text(
                unit(
                    app,
                    root,
                    user,
                    os.ttyname(slave),
                    capture="nonexistent-local-voice-test-device",
                    playback="null",
                )
            )
            command("sudo", "systemd-analyze", "verify", str(path))
            command("sudo", "install", "-m", "644", str(path), unit_path)
            command("sudo", "systemctl", "daemon-reload")
            command("sudo", "systemctl", "start", name)
            wait_for(master, b"STATE ready\n")
            report["service_start"] = "passed"
            pid = command(
                "systemctl", "show", "--property=MainPID", "--value", name
            ).strip()
            links = json.loads(
                command("sudo", "nsenter", "-t", pid, "-n", "ip", "-j", "link", "show")
            )
            assert [x["ifname"] for x in links] == ["lo"]
            report["service_network_interfaces"] = ["lo"]
            for _ in range(2):
                os.write(master, b"PRESS\n")
                wait_for(master, b"STATE error\n")
                time.sleep(0.3)
            report["capture_failure_and_retry"] = "passed"
            journal = command(
                "sudo", "journalctl", "-u", name, "--no-pager", "-o", "cat"
            )
            assert "Microphone is unavailable" in journal
            report["sanitized_error_visible"] = True
            command("sudo", "systemctl", "stop", name)
            report["clean_stop"] = (
                command(
                    "systemctl", "show", "--property=MainPID", "--value", name
                ).strip()
                == "0"
            )
            # Run real inference under the same service filesystem/network sandbox.
            text = unit(app, root, user, os.ttyname(slave))
            argv = [
                "/usr/bin/python3",
                "-m",
                "local_voice",
                "--root",
                str(root),
                "ask",
                "--text",
                "Name a primary color.",
            ]
            text = (
                "\n".join(
                    "ExecStart=" + " ".join(quoted(x) for x in argv)
                    if line.startswith("ExecStart=")
                    else line
                    for line in text.splitlines()
                )
                + "\n"
            )
            text = text.replace("Type=simple", "Type=oneshot").replace(
                "Restart=on-failure", "RemainAfterExit=true"
            )
            path.write_text(text)
            command("sudo", "install", "-m", "644", str(path), unit_path)
            command("sudo", "systemctl", "daemon-reload")
            command("sudo", "systemctl", "start", name)
            report["sandbox_real_inference_exit"] = int(
                command(
                    "systemctl", "show", "--property=ExecMainStatus", "--value", name
                ).strip()
            )
            assert report["sandbox_real_inference_exit"] == 0
            report["status"] = "passed"
    finally:
        command("sudo", "systemctl", "stop", name, check=False)
        command("sudo", "rm", "-f", unit_path)
        command("sudo", "systemctl", "daemon-reload")
        command("sudo", "systemctl", "reset-failed", name, check=False)
        os.close(master)
        os.close(slave)
    data = json.dumps(report, indent=2) + "\n"
    if a.output:
        a.output.write_text(data)
    print(data)


if __name__ == "__main__":
    main()
