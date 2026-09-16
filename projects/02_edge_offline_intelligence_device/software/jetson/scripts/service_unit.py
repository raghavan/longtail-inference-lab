#!/usr/bin/env python3
"""Generate a reviewable system service. Does not write system files or start it."""

import argparse
from pathlib import Path
import pwd
import sys


def quoted(value):
    if any(c in value for c in "\n\r\0"):
        raise ValueError("Service values must not contain line breaks or NUL")
    # systemd specifier and environment expansion differ from shell quoting.
    return (
        '"'
        + value.replace("%", "%%")
        .replace("$", "$$")
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        + '"'
    )


def unit(
    app,
    root,
    user,
    serial,
    backend="cpu",
    capture="default",
    playback="default",
    prompt_file=None,
):
    if not user or any(
        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        for c in user
    ):
        raise ValueError("Invalid service user")
    if backend not in ("cpu", "cuda"):
        raise ValueError("Invalid backend")
    workdir = str(app)
    if not workdir.startswith("/") or any(c in workdir for c in "\n\r\0"):
        raise ValueError(
            "Working directory must be an absolute path without line breaks"
        )
    args = [
        "/usr/bin/python3",
        "-m",
        "local_voice",
        "--root",
        str(root),
        "--backend",
        backend,
        "--capture-device",
        capture,
        "--playback-device",
        playback,
    ]
    if prompt_file:
        args += ["--system-prompt-file", str(prompt_file)]
    args += ["device", "--serial", serial]
    return "\n".join(
        [
            "[Unit]",
            "Description=Long Tail local voice",
            "After=sound.target",
            "StartLimitIntervalSec=60",
            "StartLimitBurst=5",
            "",
            "[Service]",
            "Type=simple",
            "User=" + user,
            "SupplementaryGroups=audio dialout",
            "WorkingDirectory=" + workdir.replace("%", "%%"),
            "ExecStart=" + " ".join(quoted(x) for x in args),
            "Restart=on-failure",
            "RestartSec=5",
            "TimeoutStopSec=12",
            "KillMode=control-group",
            "UMask=0077",
            "NoNewPrivileges=true",
            "PrivateNetwork=true",
            "PrivateTmp=true",
            "ProtectSystem=strict",
            "ProtectHome=read-only",
            "TemporaryFileSystem=/dev/shm:rw,nosuid,nodev,size=16M,mode=1777",
            "Environment=PYTHONDONTWRITEBYTECODE=1",
            "LimitCORE=0",
            "StandardOutput=journal",
            "StandardError=journal",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "",
        ]
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--app", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument(
        "--root", type=Path, default=Path.home() / ".local/share/longtail-voice"
    )
    p.add_argument("--user", default=pwd.getpwuid(__import__("os").getuid()).pw_name)
    p.add_argument("--serial", required=True)
    p.add_argument("--backend", choices=["cpu", "cuda"], default="cpu")
    p.add_argument("--capture-device", default="default")
    p.add_argument("--playback-device", default="default")
    p.add_argument("--system-prompt-file", type=Path)
    a = p.parse_args()
    sys.stdout.write(
        unit(
            a.app.resolve(),
            a.root.expanduser().resolve(),
            a.user,
            a.serial,
            a.backend,
            a.capture_device,
            a.playback_device,
            a.system_prompt_file.resolve() if a.system_prompt_file else None,
        )
    )


if __name__ == "__main__":
    main()
