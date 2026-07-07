#!/usr/bin/env python3
"""Basic repository safety scanner for Long Tail Inference Lab.

This scanner is intentionally lightweight and dependency free. It is not a
replacement for a full secret scanning product. It catches common mistakes that
are risky in a public research repo, such as private keys, tokens, public IPs,
SSH config fragments, tunnel config hints, and personal machine paths.
"""

from __future__ import annotations

import argparse
import ipaddress
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

MAX_FILE_BYTES = 2_000_000

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
}

SKIP_SUFFIXES = {
    ".bin",
    ".gguf",
    ".safetensors",
    ".pt",
    ".pth",
    ".onnx",
    ".zip",
    ".tar",
    ".gz",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".pdf",
    ".parquet",
    ".sqlite",
    ".db",
}


@dataclass(frozen=True)
class Finding:
    path: Path
    line_number: int
    rule: str
    snippet: str


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


RULES = [
    Rule("private key block", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    Rule("github token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b")),
    Rule("github fine grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b")),
    Rule("openai style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    Rule("anthropic style key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    Rule("aws access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    Rule("google api key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    Rule("hugging face token", re.compile(r"\bhf_[A-Za-z0-9]{20,}\b")),
    Rule("slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    Rule("tailscale auth key", re.compile(r"\btskey-[A-Za-z0-9_-]{20,}\b")),
    Rule("wireguard private key", re.compile(r"(?im)^\s*PrivateKey\s*=\s*[A-Za-z0-9+/=]{32,}\s*$")),
    Rule("likely secret assignment", re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd|credential)\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=:-]{12,}")),
    Rule("personal mac path", re.compile(r"/Users/(?!runner|shared|Shared)[A-Za-z0-9._-]+")),
    Rule("personal linux path", re.compile(r"/home/(?!runner|root|github|actions)[A-Za-z0-9._-]+")),
    Rule("ssh command with remote user", re.compile(r"\bssh\s+[^\s@]+@[A-Za-z0-9._-]+")),
    Rule("ssh hostname line", re.compile(r"(?im)^\s*HostName\s+[A-Za-z0-9._-]+\s*$")),
]

IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    if path.suffix in SKIP_SUFFIXES:
        return True
    return False


def iter_paths(paths: list[str]) -> Iterable[Path]:
    if paths:
        for raw in paths:
            path = Path(raw)
            if path.exists() and path.is_file() and not should_skip(path):
                yield path
        return

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        for file_name in files:
            path = root_path / file_name
            if path.exists() and path.is_file() and not should_skip(path):
                yield path


def read_text(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
        raw = path.read_bytes()
        if b"\x00" in raw:
            return None
        return raw.decode("utf-8", errors="replace")
    except OSError:
        return None


def sanitize(snippet: str) -> str:
    snippet = snippet.strip().replace("\t", " ")
    snippet = re.sub(r"\s+", " ", snippet)
    if len(snippet) > 160:
        snippet = snippet[:157] + "..."
    return snippet


def is_public_ip(candidate: str) -> bool:
    try:
        ip = ipaddress.ip_address(candidate)
    except ValueError:
        return False
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_link_local
        or ip.is_unspecified
    )


def scan_file(path: Path) -> list[Finding]:
    text = read_text(path)
    if text is None:
        return []

    findings: list[Finding] = []
    lines = text.splitlines()

    for index, line in enumerate(lines, start=1):
        for rule in RULES:
            if rule.pattern.search(line):
                findings.append(Finding(path, index, rule.name, sanitize(line)))

        for match in IPV4_RE.finditer(line):
            if is_public_ip(match.group(0)):
                findings.append(Finding(path, index, "public ip address", sanitize(line)))
                break

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a basic repository safety scan.")
    parser.add_argument("paths", nargs="*", help="Optional file paths to scan. Defaults to the full repo.")
    args = parser.parse_args()

    findings: list[Finding] = []
    for path in iter_paths(args.paths):
        findings.extend(scan_file(path))

    if findings:
        print("Safety scan failed. Review these possible leaks before committing or publishing:\n")
        for finding in findings:
            print(f"{finding.path}:{finding.line_number}: {finding.rule}: {finding.snippet}")
        print("\nIf this is a false positive, replace the value with a placeholder before committing.")
        return 1

    print("Safety scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
