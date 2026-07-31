"""Verified Markdown memory admission and deterministic lexical retrieval."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import tempfile
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

try:
    from .sanitize import SANITIZER_REVISION, inspect_unsafe, sha256_file
except ImportError:  # Allow `python artifact_memory/memory.py` from the project directory.
    from sanitize import SANITIZER_REVISION, inspect_unsafe, sha256_file

RETRIEVAL_REVISION = "direct-markdown-lexical-v1"
SEARCHABLE_FIELDS = (
    "title",
    "problem_pattern",
    "observable_symptoms",
    "environment_assumptions",
    "limitations",
)
TOKEN_RE = re.compile(r"[a-z0-9]+(?:[._+-][a-z0-9]+)*")
SAFE_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
REVISION_RE = re.compile(r"[0-9a-f]{40}")
CONTAINER_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")
PLACEHOLDER_RE = re.compile(
    r"\b(?:REQUIRED|TBD)(?:_[A-Z0-9_]*)?\b|(?i:\b(?:CHANGEME|PLACEHOLDER)(?:_[A-Za-z0-9_]*)?\b)"
)
MARKDOWN_STRUCTURE_PREFIXES = ("#", "---", "```", "~~~")
PAGE_SECTIONS = (
    "title",
    "problem_pattern",
    "observable_symptoms",
    "environment_assumptions",
    "diagnostic_sequence",
    "verified_resolution",
    "supporting_evidence",
    "limitations",
    "provenance",
)

REQUIRED_PROVENANCE = (
    "artifact_id",
    "run_id",
    "task_id",
    "task_family",
    "code_revision",
    "harbor_version",
    "terminal_bench_version",
    "task_container_digest",
    "terminus_version",
    "atif_schema_version",
    "llama_cpp_revision",
    "model_sha256",
    "quantization",
    "prompt_revision",
    "retrieval_revision",
    "sanitizer_revision",
    "python_lock_hash",
    "operating_system",
    "hardware_description",
    "trajectory_sha256",
    "verifier_artifact_sha256",
    "sanitized_artifact_sha256",
    "gitleaks_version",
)


class MemoryAdmissionError(ValueError):
    """Raised when any mandatory memory admission gate fails."""


class MemoryStateError(ValueError):
    """Raised when the wiki and the admitted-page index do not agree."""


@dataclass(frozen=True)
class Page:
    page_id: str
    path: Path
    fields: Mapping[str, str]
    content: str
    token_count: int


@dataclass(frozen=True)
class MemoryState:
    admitted_pages: int
    page_ids: tuple[str, ...]


@dataclass(frozen=True)
class RetrievedPage:
    page_id: str
    score: float
    rank: int
    token_count: int
    path: str


@dataclass(frozen=True)
class RetrievalResult:
    revision: str
    query_sha256: str
    top_k: int
    token_budget: int
    used_tokens: int
    pages: tuple[RetrievedPage, ...]

    def to_dict(self) -> dict[str, object]:
        return {**asdict(self), "pages": [asdict(page) for page in self.pages]}


def tokenize(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).lower()
    return TOKEN_RE.findall(normalized)


def _frontmatter_and_body(content: str) -> tuple[dict[str, str], str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, content
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}, content
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip()
    return metadata, "\n".join(lines[end + 1 :])


def _sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = ""
    for line in body.splitlines():
        if line.startswith("# "):
            sections["title"] = [line[2:].strip()]
            current = ""
        elif line.startswith("## "):
            current = line[3:].strip().lower().replace(" ", "_")
            sections.setdefault(current, [])
        elif current:
            sections[current].append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def load_pages(wiki_dir: Path) -> list[Page]:
    pages: list[Page] = []
    seen: set[str] = set()
    if not wiki_dir.exists():
        return pages
    for path in sorted(wiki_dir.glob("*.md"), key=lambda item: item.name):
        content = path.read_text()
        metadata, body = _frontmatter_and_body(content)
        page_id = metadata.get("page_id", "")
        if not SAFE_ID_RE.fullmatch(page_id):
            continue
        if page_id in seen:
            raise MemoryStateError(f"duplicate memory page_id: {page_id}")
        seen.add(page_id)
        sections = _sections(body)
        fields = {field: sections.get(field, "") for field in SEARCHABLE_FIELDS}
        pages.append(Page(page_id, path, fields, content, len(tokenize(content))))
    return pages


def _index_records(index_path: Path) -> list[Mapping[str, object]]:
    if not index_path.exists():
        return []
    try:
        lines = index_path.read_text().splitlines()
    except OSError as exc:
        raise MemoryStateError("admitted memory index is not readable") from exc
    records: list[Mapping[str, object]] = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise MemoryStateError(f"admitted memory index line {number} is not readable JSON") from exc
        if not isinstance(record, Mapping):
            raise MemoryStateError(f"admitted memory index line {number} is not an object")
        records.append(record)
    return records


def observed_memory_state(wiki_dir: Path, index_path: Path) -> MemoryState:
    """Return the machine-observed memory state, refusing any wiki/index disagreement."""

    latest: dict[str, Mapping[str, object]] = {}
    for record in _index_records(index_path):
        page_id = str(record.get("page_id", ""))
        if not SAFE_ID_RE.fullmatch(page_id):
            raise MemoryStateError("admitted memory index contains an unsafe page identifier")
        latest[page_id] = record
    active = {
        page_id: record
        for page_id, record in latest.items()
        if record.get("superseded") is not True
    }

    pages = {page.page_id: page for page in load_pages(wiki_dir)}
    files = sorted(wiki_dir.glob("*.md")) if wiki_dir.exists() else []
    if len(files) != len(pages):
        raise MemoryStateError("wiki contains Markdown files without a safe admitted page identifier")
    missing = sorted(set(active) - set(pages))
    if missing:
        raise MemoryStateError("admitted memory pages are missing from the wiki: " + ", ".join(missing))
    unadmitted = sorted(set(pages) - set(latest))
    if unadmitted:
        raise MemoryStateError("wiki pages were never admitted: " + ", ".join(unadmitted))
    retired = sorted(set(pages) - set(active))
    if retired:
        raise MemoryStateError("superseded pages are still retrievable in the wiki: " + ", ".join(retired))
    for page_id, record in active.items():
        if sha256_file(pages[page_id].path) != record.get("page_sha256"):
            raise MemoryStateError(f"admitted memory page changed after admission: {page_id}")
    return MemoryState(admitted_pages=len(active), page_ids=tuple(sorted(active)))


def _score_pages(query: str, pages: Sequence[Page]) -> list[tuple[float, Page]]:
    query_terms = sorted(set(tokenize(query)))
    if not query_terms or not pages:
        return []
    page_counts = {
        page.page_id: Counter(tokenize("\n".join(page.fields[field] for field in SEARCHABLE_FIELDS)))
        for page in pages
    }
    document_frequency = {
        term: sum(1 for counts in page_counts.values() if counts.get(term, 0) > 0)
        for term in query_terms
    }
    scored: list[tuple[float, Page]] = []
    count_pages = len(pages)
    for page in pages:
        counts = page_counts[page.page_id]
        score = 0.0
        for term in query_terms:
            frequency = counts.get(term, 0)
            if not frequency:
                continue
            inverse_document_frequency = 1.0 + math.log(
                (count_pages + 1) / (document_frequency[term] + 1)
            )
            score += (1.0 + math.log(frequency)) * inverse_document_frequency
        if score > 0:
            scored.append((score, page))
    return sorted(scored, key=lambda item: (-item[0], item[1].page_id))


def retrieve(query: str, wiki_dir: Path, *, top_k: int, token_budget: int) -> RetrievalResult:
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if token_budget < 1:
        raise ValueError("token_budget must be at least 1")
    pages = load_pages(wiki_dir)
    selected: list[RetrievedPage] = []
    used = 0
    for score, page in _score_pages(query, pages):
        if len(selected) >= top_k:
            break
        if page.token_count > token_budget - used:
            continue
        selected.append(
            RetrievedPage(
                page_id=page.page_id,
                score=round(score, 8),
                rank=len(selected) + 1,
                token_count=page.token_count,
                path=page.path.name,
            )
        )
        used += page.token_count
    return RetrievalResult(
        revision=RETRIEVAL_REVISION,
        query_sha256=hashlib.sha256(query.encode()).hexdigest(),
        top_k=top_k,
        token_budget=token_budget,
        used_tokens=used,
        pages=tuple(selected),
    )


def render_retrieved_memory(result: RetrievalResult, wiki_dir: Path) -> str:
    if not result.pages:
        return "<no-retrieved-memory />"
    blocks: list[str] = []
    for page in result.pages:
        content = (wiki_dir / page.path).read_text().strip()
        blocks.append(
            f'<memory-page id="{page.page_id}" lexical-score="{page.score:.8f}">\n'
            f"{content}\n</memory-page>"
        )
    return "\n\n".join(blocks)


def _require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise MemoryAdmissionError(f"{name} must be an object")
    return value


def _validate_provenance(provenance: Mapping[str, object]) -> None:
    missing = [field for field in REQUIRED_PROVENANCE if not provenance.get(field)]
    if missing:
        raise MemoryAdmissionError("incomplete provenance: " + ", ".join(missing))
    placeholders = [
        field
        for field in REQUIRED_PROVENANCE
        if isinstance(provenance.get(field), str) and PLACEHOLDER_RE.search(str(provenance[field]))
    ]
    if placeholders:
        raise MemoryAdmissionError("unresolved provenance placeholders: " + ", ".join(placeholders))
    for field in ("artifact_id", "run_id", "task_id"):
        if not isinstance(provenance[field], str) or not SAFE_ID_RE.fullmatch(str(provenance[field])):
            raise MemoryAdmissionError(f"invalid safe provenance identifier: {field}")
    if provenance["task_family"] != "environment_setup":
        raise MemoryAdmissionError("pilot memory task_family must be environment_setup")
    if not REVISION_RE.fullmatch(str(provenance["code_revision"])):
        raise MemoryAdmissionError("code_revision must be a full Git revision")
    if not CONTAINER_DIGEST_RE.fullmatch(str(provenance["task_container_digest"])):
        raise MemoryAdmissionError("task_container_digest must be an immutable SHA-256 digest")
    for field in (
        "model_sha256",
        "python_lock_hash",
        "trajectory_sha256",
        "verifier_artifact_sha256",
        "sanitized_artifact_sha256",
    ):
        if not isinstance(provenance[field], str) or not SHA256_RE.fullmatch(str(provenance[field])):
            raise MemoryAdmissionError(f"invalid SHA-256 provenance field: {field}")
    if provenance["retrieval_revision"] != RETRIEVAL_REVISION:
        raise MemoryAdmissionError("retrieval revision does not match this implementation")


def _validate_sanitizer_report(report: Mapping[str, object]) -> None:
    canary = _require_mapping(report.get("canary"), "sanitizer canary")
    allowlist = _require_mapping(report.get("allowlist"), "sanitizer allowlist")
    residual = _require_mapping(report.get("residual_scan"), "sanitizer residual scan")
    gitleaks = _require_mapping(report.get("gitleaks"), "Gitleaks result")
    required = {
        "sanitizer accepted artifact": report.get("accepted_for_human_review") is True,
        "no blocking classes": report.get("blocking_classes") == [],
        "all canaries detected": canary.get("all_detected") is True,
        "all canaries removed": canary.get("removal_verified") is True,
        "allowlist passed": allowlist.get("passed") is True,
        "residual scan passed": residual.get("passed") is True,
        "Gitleaks source scan completed": gitleaks.get("source_scan_completed") is True,
        "Gitleaks clean": gitleaks.get("clean") is True,
        "Gitleaks no unresolved findings": gitleaks.get("findings_count") == 0,
    }
    failed = [name for name, passed in required.items() if not passed]
    if failed:
        raise MemoryAdmissionError("memory safety gate failed: " + ", ".join(failed))


def _single_line(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise MemoryAdmissionError(f"{name} must be a non-empty single-line string")
    stripped = value.strip()
    if stripped.startswith(MARKDOWN_STRUCTURE_PREFIXES):
        raise MemoryAdmissionError(f"{name} must not begin with a Markdown structure marker")
    return stripped


def _safe_list(value: object, name: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise MemoryAdmissionError(f"{name} must be a non-empty list of strings")
    return [_single_line(item, name) for item in value]


def _assert_page_structure(page: str, *, page_id: str, title: str, problem: str) -> None:
    metadata, body = _frontmatter_and_body(page)
    if metadata.get("page_id") != page_id:
        raise MemoryAdmissionError("rendered page frontmatter does not round-trip")
    sections = _sections(body)
    if tuple(sections) != PAGE_SECTIONS:
        raise MemoryAdmissionError("rendered page does not match the fixed memory page structure")
    if sections["title"] != title or sections["problem_pattern"] != problem:
        raise MemoryAdmissionError("rendered page sections do not round-trip to the reviewed distillation")


def _render_page(request: Mapping[str, object], provenance: Mapping[str, object]) -> str:
    page_id = str(request.get("page_id", ""))
    if not SAFE_ID_RE.fullmatch(page_id):
        raise MemoryAdmissionError("page_id must be a lowercase safe identifier")
    summary = _require_mapping(request.get("summary"), "summary")
    title = _single_line(summary.get("title"), "summary title")
    problem = _single_line(summary.get("problem_pattern"), "problem_pattern")
    symptoms = _safe_list(summary.get("observable_symptoms"), "observable_symptoms")
    assumptions = _safe_list(summary.get("environment_assumptions"), "environment_assumptions")
    diagnostics = _safe_list(summary.get("diagnostic_sequence"), "diagnostic_sequence")
    limitations = _safe_list(summary.get("limitations"), "limitations")
    evidence_ids = _safe_list(request.get("evidence_ids"), "evidence_ids")
    if not all(SAFE_ID_RE.fullmatch(identifier) for identifier in evidence_ids):
        raise MemoryAdmissionError("evidence identifiers must be safe identifiers")
    resolutions = summary.get("verified_resolution")
    if not isinstance(resolutions, list) or not resolutions:
        raise MemoryAdmissionError("verified_resolution must be a non-empty list")
    resolution_lines: list[str] = []
    for item in resolutions:
        mapping = _require_mapping(item, "verified resolution item")
        claim = _single_line(mapping.get("claim"), "resolution claim")
        links = mapping.get("evidence_ids")
        if not isinstance(links, list) or not links:
            raise MemoryAdmissionError("each resolution claim needs evidence_ids")
        if not all(isinstance(link, str) and link in evidence_ids for link in links):
            raise MemoryAdmissionError("resolution claim references unknown evidence")
        citations = ", ".join(f"[evidence:{link}]" for link in links)
        resolution_lines.append(f"- {claim} ({citations})")

    def bullets(values: Iterable[str]) -> str:
        return "\n".join(f"- {value}" for value in values)

    page = f"""---
page_id: {page_id}
task_family: {provenance['task_family']}
artifact_id: {provenance['artifact_id']}
run_id: {provenance['run_id']}
status: current
---
# {title}

## Problem pattern

{problem}

## Observable symptoms

{bullets(symptoms)}

## Environment assumptions

{bullets(assumptions)}

## Diagnostic sequence

{bullets(diagnostics)}

## Verified resolution

{chr(10).join(resolution_lines)}

## Supporting evidence

{bullets(f'[evidence:{identifier}]' for identifier in evidence_ids)}

## Limitations

{bullets(limitations)}

## Provenance

- Artifact: {provenance['artifact_id']}
- Run: {provenance['run_id']}
- Task: {provenance['task_id']}
- Model SHA-256: {provenance['model_sha256']}
- Trajectory SHA-256: {provenance['trajectory_sha256']}
- Sanitized artifact SHA-256: {provenance['sanitized_artifact_sha256']}
- Verifier artifact SHA-256: {provenance['verifier_artifact_sha256']}
- Sanitizer revision: {provenance['sanitizer_revision']}
"""
    unsafe = inspect_unsafe(page)
    if unsafe:
        raise MemoryAdmissionError("distilled page contains unsafe classes: " + ", ".join(unsafe))
    _assert_page_structure(page, page_id=page_id, title=title, problem=problem)
    return page


def admit_memory(request_path: Path, wiki_dir: Path, index_path: Path) -> Path:
    try:
        request = json.loads(request_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise MemoryAdmissionError("admission request is not readable JSON") from exc
    request = _require_mapping(request, "admission request")
    provenance = _require_mapping(request.get("provenance"), "provenance")
    _validate_provenance(provenance)

    sanitized_path = Path(str(request.get("sanitized_artifact_path", "")))
    report_path = Path(str(request.get("sanitizer_report_path", "")))
    verifier_path = Path(str(request.get("verifier_artifact_path", "")))
    if not sanitized_path.is_file() or not report_path.is_file() or not verifier_path.is_file():
        raise MemoryAdmissionError("sanitized, sanitizer, and verifier artifact paths must exist")
    try:
        report = json.loads(report_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise MemoryAdmissionError("sanitizer report is not readable JSON") from exc
    report = _require_mapping(report, "sanitizer report")
    _validate_sanitizer_report(report)

    if report.get("sanitizer_revision") != provenance["sanitizer_revision"]:
        raise MemoryAdmissionError("sanitizer revision provenance mismatch")
    if report.get("sanitizer_revision") != SANITIZER_REVISION:
        raise MemoryAdmissionError("sanitizer revision does not match this implementation")
    if report.get("artifact_id") != provenance["artifact_id"]:
        raise MemoryAdmissionError("artifact identifier provenance mismatch")
    if sha256_file(sanitized_path) != provenance["sanitized_artifact_sha256"]:
        raise MemoryAdmissionError("sanitized artifact hash mismatch")
    if report.get("input_sha256") != provenance["trajectory_sha256"]:
        raise MemoryAdmissionError("sanitizer input is not the provenance-linked trajectory")
    if report.get("output_sha256") != provenance["sanitized_artifact_sha256"]:
        raise MemoryAdmissionError("sanitizer report output hash mismatch")
    if sha256_file(verifier_path) != provenance["verifier_artifact_sha256"]:
        raise MemoryAdmissionError("verifier artifact hash mismatch")

    verifier = _require_mapping(request.get("verifier"), "verifier")
    if verifier.get("passed") is not True or verifier.get("authoritative") != "terminal-bench-executable":
        raise MemoryAdmissionError("authoritative Terminal Bench verifier did not pass")

    review = _require_mapping(request.get("human_review"), "human_review")
    if review.get("approved") is not True:
        raise MemoryAdmissionError("explicit human review approval is required")
    reviewer = str(review.get("reviewer_id", ""))
    reviewed_at = str(review.get("reviewed_at", ""))
    if not SAFE_ID_RE.fullmatch(reviewer) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", reviewed_at):
        raise MemoryAdmissionError("human review identity or timestamp is incomplete")
    if review.get("approval_scope_sha256") != provenance["sanitized_artifact_sha256"]:
        raise MemoryAdmissionError("human approval does not cover the sanitized artifact")

    page = _render_page(request, provenance)
    page_id = str(request["page_id"])
    wiki_dir.mkdir(parents=True, exist_ok=True)
    destination = wiki_dir / f"{page_id}.md"
    if destination.exists():
        raise MemoryAdmissionError(f"memory page already exists: {page_id}")
    try:
        indexed = any(record.get("page_id") == page_id for record in _index_records(index_path))
    except MemoryStateError as exc:
        raise MemoryAdmissionError(str(exc)) from exc
    if indexed:
        raise MemoryAdmissionError(f"memory index already contains: {page_id}")

    with tempfile.NamedTemporaryFile("w", dir=wiki_dir, delete=False, encoding="utf-8") as handle:
        handle.write(page)
        temporary = Path(handle.name)
    temporary.replace(destination)
    record = {
        "page_id": page_id,
        "artifact_id": provenance["artifact_id"],
        "run_id": provenance["run_id"],
        "page_sha256": sha256_file(destination),
        "sanitizer_report_sha256": sha256_file(report_path),
        "reviewed_at": reviewed_at,
        "reviewer_id": reviewer,
        "superseded": False,
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return destination


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Admit or retrieve verified Markdown memory.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    admit = subparsers.add_parser("admit")
    admit.add_argument("--request", type=Path, required=True)
    admit.add_argument("--wiki-dir", type=Path, required=True)
    admit.add_argument("--index", type=Path, required=True)
    search = subparsers.add_parser("retrieve")
    search.add_argument("--query", required=True)
    search.add_argument("--wiki-dir", type=Path, required=True)
    search.add_argument("--top-k", type=int, required=True)
    search.add_argument("--token-budget", type=int, required=True)
    search.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    if args.command == "admit":
        destination = admit_memory(args.request, args.wiki_dir, args.index)
        print(destination)
        return 0
    result = retrieve(
        args.query,
        args.wiki_dir,
        top_k=args.top_k,
        token_budget=args.token_budget,
    )
    serialized = json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized)
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
