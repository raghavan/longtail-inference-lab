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
    from .transfer import (
        DISTILLER_TRANSMISSION_CLASSIFICATION,
        STUDENT_HF_REVISION,
        STUDENT_MODEL_ID,
        STUDENT_MODEL_SHA256,
        TEACHER_MODEL_ID,
        TransferError,
        validate_approval_record,
        validate_build_evidence,
        validate_distillation_draft,
    )
except ImportError:  # Allow `python artifact_memory/memory.py` from the project directory.
    from sanitize import SANITIZER_REVISION, inspect_unsafe, sha256_file
    from transfer import (
        DISTILLER_TRANSMISSION_CLASSIFICATION,
        STUDENT_HF_REVISION,
        STUDENT_MODEL_ID,
        STUDENT_MODEL_SHA256,
        TEACHER_MODEL_ID,
        TransferError,
        validate_approval_record,
        validate_build_evidence,
        validate_distillation_draft,
    )

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

ADMISSION_SCHEMA_VERSION = "teacher-memory-admission-v2"
DISTILLED_BODY_SECTIONS = PAGE_SECTIONS[:-1]
CITATION_RE = re.compile(r"\[evidence:([a-z0-9][a-z0-9._-]{2,127})\]")


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


def active_memory_records(index_path: Path) -> dict[str, Mapping[str, object]]:
    """Return the latest active record for each page without exposing local evidence."""

    latest: dict[str, Mapping[str, object]] = {}
    for record in _index_records(index_path):
        page_id = str(record.get("page_id", ""))
        if not SAFE_ID_RE.fullmatch(page_id):
            raise MemoryStateError("admitted memory index contains an unsafe page identifier")
        latest[page_id] = record
    return {
        page_id: record
        for page_id, record in latest.items()
        if record.get("superseded") is not True
    }


MEMORY_PROVENANCE_FIELDS = (
    "page_id",
    "page_sha256",
    "task_id",
    "task_role",
    "split_revision",
    "teacher_model_id",
    "teacher_execution_adapter",
    "teacher_prompt_revision",
    "teacher_prompt_sha256",
    "distiller_model_id",
    "distiller_adapter",
    "distiller_prompt_revision",
    "distiller_prompt_sha256",
    "student_model_id",
    "student_hugging_face_revision",
    "student_model_sha256",
    "data_transmission_classification",
    "source_evidence_sha256",
    "sanitizer_revision",
    "verifier_artifact_sha256",
    "verifier_bundle_sha256",
    "verifier_qualification_record_sha256",
    "distillation_request_sha256",
    "distillation_draft_sha256",
    "approval_record_sha256",
)


def memory_provenance_snapshot(index_path: Path) -> list[dict[str, object]]:
    """Return safe, path-free admitted-page provenance for a condition result."""

    snapshot: list[dict[str, object]] = []
    for page_id, record in sorted(active_memory_records(index_path).items()):
        missing = [field for field in MEMORY_PROVENANCE_FIELDS if field not in record]
        if missing:
            raise MemoryStateError(
                f"memory provenance snapshot is incomplete for {page_id}: " + ", ".join(missing)
            )
        snapshot.append({field: record[field] for field in MEMORY_PROVENANCE_FIELDS})
    return snapshot


def validate_memory_split(index_path: Path, split: Mapping[str, object]) -> None:
    """Reject held-out contamination and legacy records lacking teacher provenance."""

    revision = split.get("revision")
    build_ids = split.get("memory_build_task_ids")
    evaluation_ids = split.get("held_out_evaluation_task_ids")
    if not isinstance(build_ids, list) or not isinstance(evaluation_ids, list):
        raise MemoryStateError("evaluation split must contain explicit task lists")
    records = active_memory_records(index_path)
    seen_tasks: set[str] = set()
    required = (
        "task_id",
        "task_role",
        "split_revision",
        "teacher_model_id",
        "distiller_model_id",
        "student_model_id",
        "student_hugging_face_revision",
        "student_model_sha256",
        "source_evidence_sha256",
        "approval_record_sha256",
        "verifier_bundle_sha256",
        "verifier_qualification_record_sha256",
        "distillation_request_sha256",
        "distillation_draft_sha256",
        "data_transmission_classification",
    )
    for page_id, record in records.items():
        missing = [field for field in required if not record.get(field)]
        if missing:
            raise MemoryStateError(
                f"legacy or incomplete memory provenance for {page_id}: " + ", ".join(missing)
            )
        task_id = str(record["task_id"])
        if (
            record["task_role"] != "memory_build"
            or task_id not in build_ids
            or task_id in evaluation_ids
            or record["split_revision"] != revision
        ):
            raise MemoryStateError(f"memory page contaminates the held-out task split: {page_id}")
        if task_id in seen_tasks:
            raise MemoryStateError(f"multiple active pages come from one memory-build task: {task_id}")
        seen_tasks.add(task_id)
        if record["teacher_model_id"] != TEACHER_MODEL_ID or record[
            "distiller_model_id"
        ] != TEACHER_MODEL_ID:
            raise MemoryStateError(f"memory page lacks exact teacher/distiller provenance: {page_id}")
        if (
            record["student_model_id"] != STUDENT_MODEL_ID
            or record["student_hugging_face_revision"] != STUDENT_HF_REVISION
            or record["student_model_sha256"] != STUDENT_MODEL_SHA256
        ):
            raise MemoryStateError(f"memory page lacks exact student provenance: {page_id}")
        if record["data_transmission_classification"] != DISTILLER_TRANSMISSION_CLASSIFICATION:
            raise MemoryStateError(f"memory page lacks the pinned disclosure provenance: {page_id}")
        for field in (
            "approval_record_sha256",
            "distillation_request_sha256",
            "distillation_draft_sha256",
            "verifier_bundle_sha256",
            "verifier_qualification_record_sha256",
        ):
            if not isinstance(record[field], str) or not SHA256_RE.fullmatch(record[field]):
                raise MemoryStateError(f"memory page provenance hash is invalid: {page_id}.{field}")
        hashes = record["source_evidence_sha256"]
        if not isinstance(hashes, list) or not hashes or not all(
            isinstance(value, str) and SHA256_RE.fullmatch(value) for value in hashes
        ):
            raise MemoryStateError(f"memory page source evidence hashes are invalid: {page_id}")


def observed_memory_state(wiki_dir: Path, index_path: Path) -> MemoryState:
    """Return the machine-observed memory state, refusing any wiki/index disagreement."""

    latest: dict[str, Mapping[str, object]] = {}
    for record in _index_records(index_path):
        page_id = str(record.get("page_id", ""))
        if not SAFE_ID_RE.fullmatch(page_id):
            raise MemoryStateError("admitted memory index contains an unsafe page identifier")
        latest[page_id] = record
    active = active_memory_records(index_path)

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


def _single_line(value: str, name: str) -> str:
    if not value.strip() or "\n" in value or "\r" in value:
        raise MemoryAdmissionError(f"{name} must be a non-empty single-line string")
    stripped = value.strip()
    if stripped.startswith(MARKDOWN_STRUCTURE_PREFIXES):
        raise MemoryAdmissionError(f"{name} must not begin with a Markdown structure marker")
    return stripped


def _validate_markdown_body(body: str, evidence_ids: Sequence[str]) -> tuple[str, str]:
    metadata, parsed_body = _frontmatter_and_body(body)
    if metadata or parsed_body != body:
        raise MemoryAdmissionError("distiller Markdown body must not contain frontmatter")
    sections = _sections(body)
    if tuple(sections) != DISTILLED_BODY_SECTIONS:
        raise MemoryAdmissionError("distiller Markdown body does not match the fixed structure")
    title = _single_line(sections["title"], "distilled title")
    problem = _single_line(sections["problem_pattern"], "distilled problem pattern")
    for name in DISTILLED_BODY_SECTIONS[2:]:
        lines = sections[name].splitlines()
        if not lines or not all(line.startswith("- ") and len(line) > 2 for line in lines):
            raise MemoryAdmissionError(f"distilled {name} must contain single-line bullets")
    allowed = set(evidence_ids)
    supporting = sections["supporting_evidence"].splitlines()
    if supporting != [f"- [evidence:{identifier}]" for identifier in evidence_ids]:
        raise MemoryAdmissionError("supporting evidence must list each supplied evidence identifier")
    for line in sections["verified_resolution"].splitlines():
        citations = CITATION_RE.findall(line)
        if not citations or not set(citations) <= allowed:
            raise MemoryAdmissionError("every resolution claim must cite supplied sanitized evidence")
    unknown = set(CITATION_RE.findall(body)) - allowed
    if unknown:
        raise MemoryAdmissionError("distillation references unknown evidence identifiers")
    unsafe = inspect_unsafe(body)
    if unsafe:
        raise MemoryAdmissionError("distilled page contains unsafe classes: " + ", ".join(unsafe))
    return title, problem


def _render_page(
    *,
    page_id: str,
    markdown_body: str,
    build: Mapping[str, object],
    request_path: Path,
    draft_path: Path,
    approval_path: Path,
    sanitized_sha256: str,
) -> str:
    task = _require_mapping(build["task"], "task")
    execution = _require_mapping(build["execution"], "execution")
    roles = _require_mapping(build["roles"], "roles")
    teacher = _require_mapping(roles["teacher"], "teacher")
    distiller = _require_mapping(roles["distiller"], "distiller")
    page = f"""---
page_id: {page_id}
task_family: {task['task_family']}
artifact_id: {build['build_id']}
run_id: {execution['operator_record_id']}
status: current
---
{markdown_body.strip()}

## Provenance

- Task role: memory_build
- Task: {task['task_id']}
- Cloud teacher model: {TEACHER_MODEL_ID}
- Cloud distiller model: {TEACHER_MODEL_ID}
- Local student model: {STUDENT_MODEL_ID}
- Local student revision: {STUDENT_HF_REVISION}
- Local student SHA-256: {STUDENT_MODEL_SHA256}
- Teacher trajectory SHA-256: {execution['trajectory_sha256']}
- Executable verifier artifact SHA-256: {execution['verifier_artifact_sha256']}
- Verifier bundle SHA-256: {task['verifier_bundle_sha256']}
- Private verifier qualification record SHA-256: {task['verifier_qualification_record_sha256']}
- Sanitized evidence SHA-256: {sanitized_sha256}
- Distillation request SHA-256: {sha256_file(request_path)}
- Distillation draft SHA-256: {sha256_file(draft_path)}
- External approval record SHA-256: {sha256_file(approval_path)}
- Sanitizer revision: {SANITIZER_REVISION}
"""
    unsafe = inspect_unsafe(page)
    if unsafe:
        raise MemoryAdmissionError("admitted Markdown contains unsafe classes: " + ", ".join(unsafe))
    metadata, body = _frontmatter_and_body(page)
    if metadata.get("page_id") != page_id or tuple(_sections(body)) != PAGE_SECTIONS:
        raise MemoryAdmissionError("rendered page does not match the fixed admitted structure")
    return page


def admit_memory(request_path: Path, wiki_dir: Path, index_path: Path) -> Path:
    try:
        request = json.loads(request_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise MemoryAdmissionError("admission request is not readable JSON") from exc
    request = _require_mapping(request, "admission request")
    if request.get("schema_version") != ADMISSION_SCHEMA_VERSION:
        raise MemoryAdmissionError(f"admission schema must be {ADMISSION_SCHEMA_VERSION}")
    page_id = str(request.get("page_id", ""))
    if not SAFE_ID_RE.fullmatch(page_id):
        raise MemoryAdmissionError("page_id must be a lowercase safe identifier")
    build_manifest_path = Path(str(request.get("build_manifest_path", "")))
    distillation_request_path = Path(str(request.get("distillation_request_path", "")))
    distillation_draft_path = Path(str(request.get("distillation_draft_path", "")))
    approval_path = Path(str(request.get("approval_record_path", "")))
    try:
        evidence = validate_build_evidence(build_manifest_path)
        draft = validate_distillation_draft(
            build_manifest_path, distillation_request_path, distillation_draft_path
        )
        sanitized_sha256 = sha256_file(evidence.sanitized_path)
        approval = validate_approval_record(
            approval_path,
            manifest=evidence.manifest,
            request_path=distillation_request_path,
            draft_path=distillation_draft_path,
            sanitized_sha256=sanitized_sha256,
            page_id=page_id,
        )
    except TransferError as exc:
        raise MemoryAdmissionError(str(exc)) from exc

    evidence_ids = draft["evidence_ids"]
    markdown_body = str(draft["markdown_body"])
    _validate_markdown_body(markdown_body, evidence_ids)  # type: ignore[arg-type]
    page = _render_page(
        page_id=page_id,
        markdown_body=markdown_body,
        build=evidence.manifest,
        request_path=distillation_request_path,
        draft_path=distillation_draft_path,
        approval_path=approval_path,
        sanitized_sha256=sanitized_sha256,
    )
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
    task = _require_mapping(evidence.manifest["task"], "task")
    split = _require_mapping(evidence.manifest["split"], "split")
    execution = _require_mapping(evidence.manifest["execution"], "execution")
    roles = _require_mapping(evidence.manifest["roles"], "roles")
    teacher = _require_mapping(roles["teacher"], "teacher")
    distiller = _require_mapping(roles["distiller"], "distiller")
    record = {
        "page_id": page_id,
        "artifact_id": evidence.manifest["build_id"],
        "run_id": execution["operator_record_id"],
        "task_id": task["task_id"],
        "task_role": "memory_build",
        "split_revision": split["revision"],
        "page_sha256": sha256_file(destination),
        "sanitizer_report_sha256": sha256_file(evidence.sanitizer_report_path),
        "sanitizer_revision": SANITIZER_REVISION,
        "teacher_model_id": TEACHER_MODEL_ID,
        "teacher_execution_adapter": teacher["provider_runtime_or_operator_adapter"],
        "teacher_prompt_revision": teacher["prompt"]["revision"],  # type: ignore[index]
        "teacher_prompt_sha256": teacher["prompt"]["sha256"],  # type: ignore[index]
        "distiller_model_id": TEACHER_MODEL_ID,
        "distiller_adapter": distiller["provider_runtime_or_operator_adapter"],
        "distiller_prompt_revision": distiller["prompt"]["revision"],  # type: ignore[index]
        "distiller_prompt_sha256": distiller["prompt"]["sha256"],  # type: ignore[index]
        "student_model_id": STUDENT_MODEL_ID,
        "student_hugging_face_revision": STUDENT_HF_REVISION,
        "student_model_sha256": STUDENT_MODEL_SHA256,
        "data_transmission_classification": DISTILLER_TRANSMISSION_CLASSIFICATION,
        "source_evidence_sha256": [sanitized_sha256],
        "verifier_artifact_sha256": execution["verifier_artifact_sha256"],
        "verifier_bundle_sha256": task["verifier_bundle_sha256"],
        "verifier_qualification_record_sha256": task[
            "verifier_qualification_record_sha256"
        ],
        "distillation_request_sha256": sha256_file(distillation_request_path),
        "distillation_draft_sha256": sha256_file(distillation_draft_path),
        "approval_record_sha256": sha256_file(approval_path),
        "reviewed_at": approval["reviewed_at"],
        "reviewer_id": approval["reviewer_id"],
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
