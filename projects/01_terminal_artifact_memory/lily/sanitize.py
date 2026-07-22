"""Lily sanitizer: gate between terminal artifacts and searchable memory.

Reads exported trial artifacts, applies deterministic redaction rules,
optionally invokes Gitleaks, validates the file allowlist, tests canary
strings, and writes a sanitizer report. An artifact passes only when every
gate condition holds.

Stdlib only. See SETUP.md ("Safety gate") for the acceptance conditions
this module implements.

Usage:
    uv run python lily/sanitize.py --self-test
    uv run python lily/sanitize.py --input <artifact_dir> --output <out_dir>
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

SANITIZER_REVISION = "0.1.0"

REDACTED = "[REDACTED]"

# File extensions permitted in a sanitized evidence bundle. Anything else
# fails the allowlist gate; extend deliberately, never silently.
ALLOWED_EXTENSIONS = frozenset({".json", ".jsonl", ".txt", ".md", ".log", ".csv"})

# Markers whose presence must FAIL the gate rather than be redacted: hidden
# tests and reference solutions must never enter searchable memory.
HARD_FAIL_PATTERNS = (
    re.compile(r"(?:^|/)tests?/hidden/", re.IGNORECASE),
    re.compile(r"(?:^|/)solution(?:s)?/reference/", re.IGNORECASE),
    re.compile(r"(?:^|/)oracle_(?:solution|patch)", re.IGNORECASE),
)

PRIVATE_IP = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
    r"|192\.168\.\d{1,3}\.\d{1,3})\b"
)
GIT_REMOTE = re.compile(
    r"(?:git@[\w.-]+:[\w./-]+|https?://[\w.-]+(?::\d+)?/[\w./-]+?\.git)\b"
)
HOME_DIR = re.compile(r"(?:/home/|/Users/)[^\s/:'\"]+")


@dataclass
class SanitizerConfig:
    """Experiment-specific values to strip from exported artifacts."""

    hostnames: list[str] = field(default_factory=list)
    workspace_paths: list[str] = field(default_factory=list)
    repository_names: list[str] = field(default_factory=list)
    docker_mount_paths: list[str] = field(default_factory=list)
    canaries: list[str] = field(default_factory=list)


@dataclass
class Finding:
    rule: str
    count: int


@dataclass
class FileReport:
    path: str
    status: str  # "sanitized" | "rejected"
    findings: list[Finding] = field(default_factory=list)
    reason: str | None = None


def build_rules(config: SanitizerConfig) -> list[tuple[str, re.Pattern[str]]]:
    """Ordered (rule name, pattern) pairs. Literals are escaped, so
    hostnames, paths, and canaries are treated as exact strings."""
    rules: list[tuple[str, re.Pattern[str]]] = [
        ("private_network_address", PRIVATE_IP),
        ("git_remote_address", GIT_REMOTE),
        ("home_directory_path", HOME_DIR),
    ]
    for name in config.hostnames:
        rules.append(("hostname", re.compile(re.escape(name), re.IGNORECASE)))
    for path in config.workspace_paths:
        rules.append(("workspace_path", re.compile(re.escape(path))))
    for name in config.repository_names:
        rules.append(("repository_name", re.compile(re.escape(name))))
    for path in config.docker_mount_paths:
        rules.append(("docker_mount_path", re.compile(re.escape(path))))
    for canary in config.canaries:
        rules.append(("canary", re.compile(re.escape(canary))))
    return rules


def sanitize_text(text: str, rules: list[tuple[str, re.Pattern[str]]]) -> tuple[str, list[Finding]]:
    findings: list[Finding] = []
    for rule_name, pattern in rules:
        text, count = pattern.subn(REDACTED, text)
        if count:
            findings.append(Finding(rule=rule_name, count=count))
    return text, findings


def hard_fail_reason(relative_path: str, text: str) -> str | None:
    """Return a reason when content must be rejected outright."""
    for pattern in HARD_FAIL_PATTERNS:
        if pattern.search(relative_path):
            return f"hidden test or reference solution path: {relative_path}"
        if pattern.search(text):
            return "hidden test or reference solution reference in content"
    return None


def run_gitleaks(target: Path) -> dict:
    """Invoke Gitleaks if available. Returns a report fragment.

    The pilot records three states: clean, findings, or unavailable.
    Unavailable does not block the gate (Lily rules and manual review
    still run), but it is recorded in the report for transparency."""
    if shutil.which("gitleaks") is None:
        return {"status": "unavailable", "findings": None}
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        report_path = Path(tmp.name)
    try:
        result = subprocess.run(
            ["gitleaks", "dir", "--report-format", "json",
             "--report-path", str(report_path), str(target)],
            capture_output=True, text=True, timeout=120,
        )
        findings = json.loads(report_path.read_text() or "[]")
        return {
            "status": "clean" if result.returncode == 0 else "findings",
            "findings": len(findings),
        }
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return {"status": "error", "findings": None, "detail": str(exc)}
    finally:
        report_path.unlink(missing_ok=True)


def sanitize_tree(
    input_dir: Path, output_dir: Path, config: SanitizerConfig
) -> dict:
    """Sanitize every allowed file from input_dir into output_dir and
    return the report. The run passes only when no file is rejected and
    every planted canary was detected somewhere in the tree."""
    rules = build_rules(config)
    reports: list[FileReport] = []
    canaries_seen: set[str] = set()

    for source in sorted(input_dir.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(input_dir).as_posix()
        if source.suffix.lower() not in ALLOWED_EXTENSIONS:
            reports.append(FileReport(
                path=relative, status="rejected",
                reason=f"extension not in allowlist: {source.suffix}"))
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        reason = hard_fail_reason(relative, text)
        if reason:
            reports.append(FileReport(path=relative, status="rejected", reason=reason))
            continue
        for canary in config.canaries:
            if canary in text:
                canaries_seen.add(canary)
        sanitized, findings = sanitize_text(text, rules)
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(sanitized, encoding="utf-8")
        reports.append(FileReport(path=relative, status="sanitized", findings=findings))

    canaries_missing = [c for c in config.canaries if c not in canaries_seen]
    rejected = [r for r in reports if r.status == "rejected"]
    gitleaks = run_gitleaks(input_dir)
    passed = (
        not rejected
        and not canaries_missing
        and gitleaks["status"] not in {"findings", "error"}
    )
    return {
        "sanitizer_revision": SANITIZER_REVISION,
        "status": "pass" if passed else "fail",
        "files": [
            {
                "path": r.path,
                "status": r.status,
                "reason": r.reason,
                "findings": [{"rule": f.rule, "count": f.count} for f in r.findings],
            }
            for r in reports
        ],
        "canaries": {
            "planted": len(config.canaries),
            "detected": len(canaries_seen),
            "missing": canaries_missing,
        },
        "gitleaks": gitleaks,
    }


def load_config(path: Path | None) -> SanitizerConfig:
    if path is None:
        return SanitizerConfig()
    data = json.loads(path.read_text(encoding="utf-8"))
    return SanitizerConfig(**data)


class SanitizerSelfTest(unittest.TestCase):
    """Canary and rule verification. Run: uv run python lily/sanitize.py --self-test"""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.config = SanitizerConfig(
            hostnames=["builder.internal.example"],
            workspace_paths=["/srv/lily/workspace"],
            repository_names=["raghavan/private-infra"],
            docker_mount_paths=["/var/lib/docker/volumes/task01"],
            canaries=["CANARY_TOKEN_9f3c"],
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, name: str, text: str) -> None:
        target = self.tmp / "in" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def _run(self) -> dict:
        out = self.tmp / "out"
        return sanitize_tree(self.tmp / "in", out, self.config)

    def test_canary_is_detected_and_redacted(self) -> None:
        self._write("log.txt", "export TOKEN=CANARY_TOKEN_9f3c done")
        report = self._run()
        self.assertEqual(report["canaries"]["missing"], [])
        sanitized = (self.tmp / "out" / "log.txt").read_text()
        self.assertNotIn("CANARY_TOKEN_9f3c", sanitized)
        self.assertIn(REDACTED, sanitized)

    def test_missing_canary_fails_run(self) -> None:
        self._write("log.txt", "nothing sensitive here")
        report = self._run()
        self.assertEqual(report["status"], "fail")

    def test_private_ip_and_git_remote_redacted(self) -> None:
        self._write(
            "notes.md",
            "ssh 192.168.1.20 then clone git@git.internal.example:org/repo.git",
        )
        report = self._run()
        sanitized = (self.tmp / "out" / "notes.md").read_text()
        self.assertNotIn("192.168.1.20", sanitized)
        self.assertNotIn("git@git.internal.example", sanitized)

    def test_hidden_test_path_rejects_file(self) -> None:
        self._write("tests/hidden/case01.json", "{}")
        report = self._run()
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["files"][0]["status"], "rejected")

    def test_disallowed_extension_rejected(self) -> None:
        self._write("binary.bin", "payload")
        self._write("log.txt", "CANARY_TOKEN_9f3c")
        report = self._run()
        statuses = {f["path"]: f["status"] for f in report["files"]}
        self.assertEqual(statuses["binary.bin"], "rejected")

    def test_clean_run_passes(self) -> None:
        self._write("verifier.json", '{"passed": true}')
        self._write("log.txt", "task completed CANARY_TOKEN_9f3c")
        report = self._run()
        self.assertEqual(report["status"], "pass")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", type=Path, help="exported artifact directory")
    parser.add_argument("--output", type=Path, help="sanitized output directory")
    parser.add_argument("--config", type=Path, help="JSON sanitizer config")
    parser.add_argument("--report", type=Path, help="write report JSON here")
    parser.add_argument("--self-test", action="store_true", help="run unit tests")
    args = parser.parse_args(argv)

    if args.self_test:
        suite = unittest.TestLoader().loadTestsFromTestCase(SanitizerSelfTest)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1

    if not args.input or not args.output:
        parser.error("--input and --output are required (or use --self-test)")

    config = load_config(args.config)
    report = sanitize_tree(args.input, args.output, config)
    report_json = json.dumps(report, indent=2)
    if args.report:
        args.report.write_text(report_json + "\n", encoding="utf-8")
    print(report_json)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
