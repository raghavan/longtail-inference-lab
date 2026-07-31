"""Artifact sanitizer and Gitleaks boundary for memory admission.

The sanitizer is intentionally conservative. Privacy-bearing spans are redacted;
credentials and benchmark-contamination signals also block admission even after
redaction. Reports contain counts and rule names, never the matched values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

SANITIZER_REVISION = "lily-sanitizer-v1"
REDACTION = {
    "canary": "[CANARY-REMOVED]",
    "credential": "[CREDENTIAL-REMOVED]",
    "private_path": "[PRIVATE-PATH]",
    "workspace_path": "[WORKSPACE-PATH]",
    "docker_mount": "[CONTAINER-MOUNT]",
    "remote": "[REMOTE-ADDRESS]",
    "host": "[PRIVATE-HOST]",
    "network": "[NETWORK-ADDRESS]",
    "hidden_test": "[CONTAMINATION-REMOVED]",
    "reference_solution": "[CONTAMINATION-REMOVED]",
    "verifier_detail": "[CONTAMINATION-REMOVED]",
    "contamination": "[CONTAMINATION-REMOVED]",
    "private_term": "[PRIVATE-TERM]",
}


class SanitizationError(RuntimeError):
    """Raised when an external sanitizer boundary cannot be evaluated."""


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    blocking: bool = False


RULES: tuple[Rule, ...] = (
    Rule(
        "credential",
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        True,
    ),
    Rule(
        "credential",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|credential|secret)"
            r"\s*[:=]\s*['\"]?[^\s'\"]{8,}"
        ),
        True,
    ),
    Rule("credential", re.compile(r"(?i)\bAuthorization\s*:\s*Bearer\s+\S+"), True),
    Rule(
        "credential",
        re.compile(r"\b(?:github_pat_|gh[pousr]_|sk-ant-|hf_)[A-Za-z0-9_-]{12,}\b"),
        True,
    ),
    Rule(
        "hidden_test",
        re.compile(r"(?i)(?:^|[/\\\s])(?:hidden|private)[-_ ]?tests?(?:[/\\\s]|$)"),
        True,
    ),
    Rule(
        "reference_solution",
        re.compile(
            r"(?i)(?:^|[/\\\s])(?:reference[-_ ]?solutions?|refsol|gold[-_ ]?(?:patch|solution)|answer[-_ ]?key)"
            r"(?:[/\\\s.]|$)"
        ),
        True,
    ),
    Rule(
        "verifier_detail",
        re.compile(
            r"(?i)(?:^|[/\\])verifier(?:[/\\])|(?:^|[/\\])(?:reward\.txt|ctrf\.json)(?:\s|$)"
        ),
        True,
    ),
    Rule(
        "contamination",
        re.compile(r"(?i)\b(?:do not show the model|benchmark answer|ground[-_ ]truth patch|hidden canary)\b"),
        True,
    ),
    Rule(
        "private_path",
        re.compile(r"(?i)(?:/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|[A-Z]:\\Users\\[^\\\s]+)(?:[/\\][^\s]*)?"),
    ),
    Rule(
        "workspace_path",
        re.compile(r"(?i)(?:/(?:workspace|workspaces|repo|repos|checkout|checkouts)(?:/[^\s]*)?)"),
    ),
    Rule(
        "docker_mount",
        re.compile(r"(?i)(?:/(?:mnt|mounts|host_mnt|var/lib/docker)(?:/[^\s]*)?)"),
    ),
    Rule(
        "remote",
        re.compile(r"(?i)\b(?:https?|ssh|git)://[^\s<>'\"]+|\bgit@[A-Za-z0-9._-]+:[^\s]+"),
    ),
    Rule(
        "remote",
        re.compile(r"\b[A-Za-z0-9._-]+@[A-Za-z0-9._-]+(?::(?:[A-Za-z0-9._~/-]+))?"),
    ),
    Rule(
        "host",
        re.compile(
            r"(?i)\b(?:host(?:name)?|server)\s*[:=]\s*(?!\[)[A-Za-z0-9][A-Za-z0-9.-]*"
            r"|\b[A-Za-z0-9][A-Za-z0-9.-]*\.(?:internal|local|lan|home|corp)\b"
        ),
    ),
    Rule("network", re.compile(r"(?<![A-Za-z0-9])(?:\d{1,3}\.){3}\d{1,3}(?![A-Za-z0-9])")),
    Rule(
        "network",
        re.compile(r"(?<![A-Fa-f0-9:])(?:[A-Fa-f0-9]{1,4}:){2,7}[A-Fa-f0-9]{0,4}(?![A-Fa-f0-9:])"),
    ),
)

GitleaksRunner = Callable[[Path, Path], dict[str, object]]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_gitleaks_command(target: Path, report_path: Path, executable: str = "gitleaks") -> list[str]:
    """Build the current Gitleaks directory-scan interface as an argv list."""

    return [
        executable,
        "dir",
        "--no-banner",
        "--no-color",
        "--report-format",
        "json",
        "--report-path",
        str(report_path),
        str(target),
    ]


def run_gitleaks(target: Path, report_path: Path, executable: str = "gitleaks") -> dict[str, object]:
    if shutil.which(executable) is None:
        raise SanitizationError(f"required executable not found: {executable}")
    command = build_gitleaks_command(target, report_path, executable)
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode not in (0, 1):
        raise SanitizationError(
            f"Gitleaks failed with exit code {completed.returncode}: {completed.stderr.strip()}"
        )
    try:
        findings = json.loads(report_path.read_text()) if report_path.exists() else []
    except (OSError, json.JSONDecodeError) as exc:
        raise SanitizationError("Gitleaks did not produce a readable JSON report") from exc
    if not isinstance(findings, list):
        raise SanitizationError("Gitleaks report is not a JSON list")
    return {
        "clean": completed.returncode == 0 and not findings,
        "exit_code": completed.returncode,
        "findings_count": len(findings),
        "command_interface": "gitleaks dir --report-format json",
    }


def _replace_rule(text: str, rule: Rule) -> tuple[str, int]:
    return rule.pattern.subn(REDACTION[rule.name], text)


def _safe_ascii(text: str) -> bool:
    return all(char in "\n\r\t" or 0x20 <= ord(char) <= 0x7E for char in text)


def residual_rule_names(text: str, canaries: Iterable[str] = ()) -> list[str]:
    names = {rule.name for rule in RULES if rule.pattern.search(text)}
    if any(canary and canary in text for canary in canaries):
        names.add("canary")
    return sorted(names)


def inspect_unsafe(text: str) -> list[str]:
    """Return unsafe class names without exposing matching values."""

    names = set(residual_rule_names(text))
    if not _safe_ascii(text):
        names.add("allowlist")
    return sorted(names)


def sanitize_text(
    text: str,
    *,
    canaries: Sequence[str],
    blocked_terms: Sequence[str] = (),
) -> tuple[str, dict[str, object]]:
    """Redact a text artifact and return a value-free internal report."""

    normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    counts: dict[str, int] = {}
    blockers: set[str] = set()
    detected_canaries: list[str] = []

    for index, canary in enumerate(canaries):
        if not canary:
            raise ValueError("canary values must be non-empty")
        count = normalized.count(canary)
        if count:
            normalized = normalized.replace(canary, REDACTION["canary"])
            counts["canary"] = counts.get("canary", 0) + count
            detected_canaries.append(f"canary-{index + 1}")

    for term in blocked_terms:
        if not term:
            raise ValueError("blocked terms must be non-empty")
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        normalized, count = pattern.subn(REDACTION["private_term"], normalized)
        if count:
            counts["private_term"] = counts.get("private_term", 0) + count

    for rule in RULES:
        normalized, count = _replace_rule(normalized, rule)
        if not count:
            continue
        counts[rule.name] = counts.get(rule.name, 0) + count
        if rule.blocking:
            blockers.add(rule.name)

    residual = residual_rule_names(normalized, canaries)
    allowlist_passed = _safe_ascii(normalized)
    all_canaries_detected = bool(canaries) and len(detected_canaries) == len(canaries)
    canaries_removed = all(canary not in normalized for canary in canaries)
    internal = {
        "replacement_counts": dict(sorted(counts.items())),
        "blocking_classes": sorted(blockers),
        "canary": {
            "expected_count": len(canaries),
            "detected_ids": detected_canaries,
            "all_detected": all_canaries_detected,
            "removal_verified": canaries_removed,
        },
        "allowlist": {
            "revision": "printable-ascii-v1",
            "passed": allowlist_passed,
        },
        "residual_scan": {
            "passed": not residual,
            "classes": residual,
        },
    }
    return normalized, internal


def sanitize_artifact(
    input_path: Path,
    output_path: Path,
    report_path: Path,
    *,
    artifact_id: str,
    canaries: Sequence[str],
    blocked_terms: Sequence[str] = (),
    gitleaks_runner: GitleaksRunner = run_gitleaks,
) -> dict[str, object]:
    """Sanitize one text artifact and write its admission-gate report."""

    try:
        raw = input_path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise SanitizationError("artifact must be readable UTF-8 text") from exc

    sanitized, internal = sanitize_text(text, canaries=canaries, blocked_terms=blocked_terms)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sanitized)

    source_gitleaks_report = report_path.with_suffix(".source.gitleaks.json")
    sanitized_gitleaks_report = report_path.with_suffix(".sanitized.gitleaks.json")
    source_gitleaks = gitleaks_runner(input_path, source_gitleaks_report)
    sanitized_gitleaks = gitleaks_runner(output_path, sanitized_gitleaks_report)
    try:
        source_gitleaks_report.unlink(missing_ok=True)
        sanitized_gitleaks_report.unlink(missing_ok=True)
    except OSError as exc:
        raise SanitizationError("could not remove temporary Gitleaks detail report") from exc
    gitleaks = {
        "clean": sanitized_gitleaks.get("clean") is True,
        "findings_count": sanitized_gitleaks.get("findings_count"),
        "source_scan_completed": True,
        "source_findings_count": source_gitleaks.get("findings_count"),
        "sanitized_scan": sanitized_gitleaks,
        "command_interface": "gitleaks dir --report-format json",
    }

    accepted = bool(
        not internal["blocking_classes"]
        and internal["canary"]["all_detected"]  # type: ignore[index]
        and internal["canary"]["removal_verified"]  # type: ignore[index]
        and internal["allowlist"]["passed"]  # type: ignore[index]
        and internal["residual_scan"]["passed"]  # type: ignore[index]
        and gitleaks.get("clean") is True
    )
    report: dict[str, object] = {
        "schema_version": "sanitizer-report-v1",
        "sanitizer_revision": SANITIZER_REVISION,
        "artifact_id": artifact_id,
        "input_sha256": sha256_bytes(raw),
        "output_sha256": sha256_file(output_path),
        **internal,
        "gitleaks": gitleaks,
        "accepted_for_human_review": accepted,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def _read_values(path: Path | None) -> list[str]:
    if path is None:
        return []
    values = [line.strip() for line in path.read_text().splitlines()]
    return [value for value in values if value and not value.startswith("#")]


def self_test() -> int:
    """Run an internal synthetic-fixture smoke without external executables."""

    marker = "SYNTHETIC-FIXTURE-CANARY"
    private_path = "/" + "Users/fixture-person/work/project"
    source = f"fixture path={private_path}\nmarker={marker}\n"

    def clean_gitleaks(_target: Path, _report: Path) -> dict[str, object]:
        return {
            "clean": True,
            "exit_code": 0,
            "findings_count": 0,
            "command_interface": "synthetic-fixture-stub",
        }

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        input_path = root / "synthetic-fixture.txt"
        output_path = root / "sanitized.txt"
        report_path = root / "sanitizer.json"
        input_path.write_text(source)
        report = sanitize_artifact(
            input_path,
            output_path,
            report_path,
            artifact_id="synthetic-fixture-artifact",
            canaries=[marker],
            gitleaks_runner=clean_gitleaks,
        )
        output = output_path.read_text()
        if marker in output or private_path in output or report["accepted_for_human_review"] is not True:
            print("Synthetic fixture sanitizer self-test failed.")
            return 1
    print("Synthetic fixture sanitizer self-test passed; this is not measured experiment data.")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sanitize an exported text artifact.")
    parser.add_argument("--self-test", action="store_true", help="run a synthetic fixture self-test")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--artifact-id")
    parser.add_argument("--canary-file", type=Path, help="local file with one expected canary per line")
    parser.add_argument("--blocked-terms-file", type=Path, help="local private names to redact")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    required = (args.input, args.output, args.report, args.artifact_id, args.canary_file)
    if any(value is None for value in required):
        parser.error("--input, --output, --report, --artifact-id, and --canary-file are required")
    report = sanitize_artifact(
        args.input,
        args.output,
        args.report,
        artifact_id=args.artifact_id,
        canaries=_read_values(args.canary_file),
        blocked_terms=_read_values(args.blocked_terms_file),
    )
    print(json.dumps({"accepted_for_human_review": report["accepted_for_human_review"]}))
    return 0 if report["accepted_for_human_review"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
