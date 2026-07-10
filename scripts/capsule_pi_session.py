#!/usr/bin/env python3
"""Package a pi coding agent session as a transferable capsule.

pi (https://github.com/badlogic/pi-mono) stores sessions as JSONL under
~/.pi/agent/sessions/ and assembles agent instructions from a global
~/.pi/agent/AGENTS.md plus AGENTS.md / CLAUDE.md files found walking up
from the working directory. This script gathers the session, the exact
instruction files that shaped it, and optionally the llama.cpp server
state behind it, into one hash-verified generation-numbered archive.

Tiers, matching docs/experiment-session-transfer-capsule.md:
  Tier 0  transcript capsule: session JSONL + instruction files.
          Works for any backend, including hosted APIs.
  Tier 1  Tier 0 plus the serialized KV state of a local llama-server
          slot. Only possible when pi talks to a llama-server you run,
          started with --slot-save-path.

Usage:
  capsule_pi_session.py create [--session PATH] [--out DIR]
      [--llama-server URL --slot N --slot-save-path DIR]
  capsule_pi_session.py verify CAPSULE.tar.gz
  capsule_pi_session.py restore CAPSULE.tar.gz [--out DIR]
      [--llama-server URL --slot N --slot-save-path DIR]

Only the Python standard library is used. Nothing here talks to any
network host except the llama-server URL you pass explicitly.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

SCHEMA_VERSION = 1


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pi_home() -> Path:
    return Path(os.environ.get("PI_DIR", Path.home() / ".pi"))


def find_latest_session(session_dir: Path) -> Path:
    candidates = sorted(
        session_dir.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not candidates:
        sys.exit(f"no session files found under {session_dir}; "
                 "pass --session explicitly")
    return candidates[0]


def collect_instruction_files(cwd: Path) -> list[Path]:
    """Mirror pi's context loading: global AGENTS.md, then AGENTS.md or
    CLAUDE.md in each directory from the filesystem root down to cwd.
    The manifest records the exact order so the capsule is auditable."""
    found = []
    global_agents = pi_home() / "agent" / "AGENTS.md"
    if global_agents.is_file():
        found.append(global_agents)
    chain = list(reversed([cwd, *cwd.parents]))
    for directory in chain:
        for name in ("AGENTS.md", "CLAUDE.md"):
            candidate = directory / name
            if candidate.is_file():
                found.append(candidate)
    return found


def llama_slot_request(base_url: str, slot: int, action: str, filename: str) -> dict:
    url = f"{base_url.rstrip('/')}/slots/{slot}?action={action}"
    body = json.dumps({"filename": filename}).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.URLError as e:
        sys.exit(f"llama-server slot {action} failed at {url}: {e}")


def next_generation(out_dir: Path) -> str:
    current = out_dir / "CURRENT"
    if current.is_file():
        return f"{int(current.read_text().strip()) + 1:06d}"
    return "000001"


def cmd_create(args) -> None:
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    gen = next_generation(out_dir)

    session_path = (
        Path(args.session).expanduser()
        if args.session
        else find_latest_session(pi_home() / "agent" / "sessions")
    )
    if not session_path.is_file():
        sys.exit(f"session file not found: {session_path}")
    print(f"session: {session_path}")

    instruction_files = collect_instruction_files(Path.cwd())
    for path in instruction_files:
        print(f"instructions: {path}")
    if not instruction_files:
        print("instructions: none found (no AGENTS.md or CLAUDE.md in scope)")

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / f"capsule.{gen}"
        (stage / "instructions").mkdir(parents=True)

        shutil.copy2(session_path, stage / "session.jsonl")

        instructions_manifest = []
        for i, path in enumerate(instruction_files):
            staged_name = f"{i:02d}_{path.name}"
            shutil.copy2(path, stage / "instructions" / staged_name)
            instructions_manifest.append(
                {"order": i, "source": str(path), "file": f"instructions/{staged_name}"}
            )

        tier = 0
        if args.llama_server:
            if not args.slot_save_path:
                sys.exit("--llama-server requires --slot-save-path so the "
                         "state file the server writes can be collected")
            state_name = f"capsule.{gen}.state.bin"
            result = llama_slot_request(
                args.llama_server, args.slot, "save", state_name
            )
            saved = Path(args.slot_save_path).expanduser() / state_name
            if not saved.is_file():
                sys.exit(f"server reported a save but {saved} does not exist; "
                         "check the server's --slot-save-path")
            shutil.move(str(saved), stage / "state.bin")
            tier = 1
            print(f"state: slot {args.slot} saved "
                  f"({result.get('n_saved', '?')} tokens reported)")

        payloads = {
            entry.relative_to(stage).as_posix(): sha256_file(entry)
            for entry in sorted(stage.rglob("*"))
            if entry.is_file()
        }
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "generation": gen,
            "tier": tier,
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "harness": "pi",
            "session_source": str(session_path),
            "instruction_files": instructions_manifest,
            "hashes": payloads,
        }
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

        archive = out_dir / f"capsule.{gen}.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(stage, arcname=f"capsule.{gen}")

    (out_dir / "CURRENT").write_text(f"{int(gen)}\n")
    print(f"\nwrote {archive} (tier {tier})")
    print("ship it with, for example:")
    print(f"  rsync -a --partial --fuzzy --stats {archive} standby:capsules/")
    if tier == 0:
        print("note: tier 0 capsule; the target rebuilds state by replaying "
              "the session through pi (--session) against the same model")


def load_and_verify(archive: Path, dest: Path) -> Path:
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(dest, filter="data")
    roots = [p for p in dest.iterdir() if p.is_dir()]
    if len(roots) != 1:
        sys.exit(f"unexpected archive layout in {archive}")
    root = roots[0]
    manifest = json.loads((root / "manifest.json").read_text())
    for rel, expected in manifest["hashes"].items():
        actual = sha256_file(root / rel)
        if actual != expected:
            sys.exit(f"hash mismatch for {rel}: capsule is torn or tampered")
    print(f"verified {len(manifest['hashes'])} files, "
          f"generation {manifest['generation']}, tier {manifest['tier']}")
    return root


def cmd_verify(args) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        load_and_verify(Path(args.capsule).expanduser(), Path(tmp))


def cmd_restore(args) -> None:
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        root = load_and_verify(Path(args.capsule).expanduser(), Path(tmp))
        manifest = json.loads((root / "manifest.json").read_text())
        target = out_dir / root.name
        if target.exists():
            sys.exit(f"{target} already exists; refusing to overwrite")
        shutil.copytree(root, target)

    session = target / "session.jsonl"
    print(f"restored to {target}")
    print(f"resume the conversation with:\n  pi --session {session}")

    if manifest["tier"] == 1 and args.llama_server:
        if not args.slot_save_path:
            sys.exit("--llama-server requires --slot-save-path")
        state_name = f"capsule.{manifest['generation']}.state.bin"
        shutil.copy2(
            target / "state.bin",
            Path(args.slot_save_path).expanduser() / state_name,
        )
        result = llama_slot_request(
            args.llama_server, args.slot, "restore", state_name
        )
        print(f"state: slot {args.slot} restored "
              f"({result.get('n_restored', '?')} tokens reported)")
    elif manifest["tier"] == 1:
        print("capsule carries state.bin; pass --llama-server and "
              "--slot-save-path to restore it into a local server")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    def add_llama_args(p):
        p.add_argument("--llama-server", metavar="URL",
                       help="base URL of a local llama-server, "
                            "for example http://127.0.0.1:8080")
        p.add_argument("--slot", type=int, default=0)
        p.add_argument("--slot-save-path", metavar="DIR",
                       help="directory the server was started with "
                            "via --slot-save-path")

    p_create = sub.add_parser("create", help="capsule the current pi session")
    p_create.add_argument("--session", help="session JSONL path; "
                          "defaults to the most recently modified session")
    p_create.add_argument("--out", default="~/capsules")
    add_llama_args(p_create)
    p_create.set_defaults(func=cmd_create)

    p_verify = sub.add_parser("verify", help="check a capsule's hashes")
    p_verify.add_argument("capsule")
    p_verify.set_defaults(func=cmd_verify)

    p_restore = sub.add_parser("restore", help="unpack a capsule for resumption")
    p_restore.add_argument("capsule")
    p_restore.add_argument("--out", default="~/capsules/restored")
    add_llama_args(p_restore)
    p_restore.set_defaults(func=cmd_restore)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
