from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from artifact_memory.memory import (
    MemoryAdmissionError,
    MemoryStateError,
    admit_memory,
    observed_memory_state,
    retrieve,
    validate_memory_split,
)
from artifact_memory.sanitize import sha256_file
from tests.helpers import admission_fixture, memory_page, split_fixture


class MemoryTests(unittest.TestCase):
    def test_deterministic_retrieval_uses_page_id_tiebreak(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory)
            (wiki / "b.md").write_text(memory_page("fixture-page-b"))
            (wiki / "a.md").write_text(memory_page("fixture-page-a"))
            first = retrieve("package environment shell path", wiki, top_k=2, token_budget=5000)
            second = retrieve("package environment shell path", wiki, top_k=2, token_budget=5000)
            self.assertEqual(first.to_dict(), second.to_dict())
            self.assertEqual([page.page_id for page in first.pages], ["fixture-page-a", "fixture-page-b"])
            self.assertEqual([page.rank for page in first.pages], [1, 2])

    def test_retrieval_honors_top_k_and_token_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory)
            (wiki / "a.md").write_text(memory_page("fixture-page-a"))
            (wiki / "b.md").write_text(memory_page("fixture-page-b"))
            self.assertEqual(len(retrieve("package environment", wiki, top_k=1, token_budget=5000).pages), 1)
            too_small = retrieve("package environment", wiki, top_k=2, token_budget=1)
            self.assertEqual(too_small.pages, ())

    def test_teacher_derived_memory_admission_requires_every_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            destination = admit_memory(request, root / "wiki", root / "index.jsonl")
            self.assertTrue(destination.is_file())
            page = destination.read_text()
            self.assertIn("Cloud teacher model: gpt-5.6-sol", page)
            self.assertIn("Cloud distiller model: gpt-5.6-sol", page)
            self.assertIn("Local student model: Qwen/Qwen2.5-Coder-7B-Instruct-GGUF", page)
            record = json.loads((root / "index.jsonl").read_text())
            self.assertEqual(record["task_role"], "memory_build")
            self.assertEqual(record["source_evidence_sha256"], [sha256_file(root / "sanitized-fixture.txt")])
            self.assertTrue(record["approval_record_sha256"])
            validate_memory_split(root / "index.jsonl", split_fixture())

    def test_approval_must_exist_before_admission_and_cover_all_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            admission = json.loads(request.read_text())
            approval_path = Path(admission["approval_record_path"])
            approval = json.loads(approval_path.read_text())
            approval["approved"] = False
            approval_path.write_text(json.dumps(approval))
            with self.assertRaisesRegex(MemoryAdmissionError, "approval is required"):
                admit_memory(request, root / "wiki", root / "index.jsonl")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            admission = json.loads(request.read_text())
            approval_path = Path(admission["approval_record_path"])
            approval = json.loads(approval_path.read_text())
            approval["scope"]["distillation_draft_sha256"] = "f" * 64
            approval_path.write_text(json.dumps(approval))
            with self.assertRaisesRegex(MemoryAdmissionError, "does not cover"):
                admit_memory(request, root / "wiki", root / "index.jsonl")

    def test_failed_executable_verifier_blocks_sanitization_chain_admission(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            admission = json.loads(request.read_text())
            build_path = Path(admission["build_manifest_path"])
            build = json.loads(build_path.read_text())
            verifier_path = Path(build["execution"]["verifier_artifact_path"])
            verifier_path.write_text(json.dumps({"authoritative": "terminal-bench-executable", "passed": False}))
            build["execution"]["verifier_artifact_sha256"] = sha256_file(verifier_path)
            build_path.write_text(json.dumps(build))
            with self.assertRaisesRegex(MemoryAdmissionError, "executable-verifier pass"):
                admit_memory(request, root / "wiki", root / "index.jsonl")

    def test_mismatched_distiller_provenance_blocks_admission(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            admission = json.loads(request.read_text())
            draft_path = Path(admission["distillation_draft_path"])
            draft = json.loads(draft_path.read_text())
            draft["distiller_model_id"] = "not-the-pinned-distiller"
            draft_path.write_text(json.dumps(draft))
            with self.assertRaisesRegex(MemoryAdmissionError, "distiller_model_id"):
                admit_memory(request, root / "wiki", root / "index.jsonl")

    def test_distilled_markdown_must_be_safe_structured_and_evidence_linked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            admission = json.loads(request.read_text())
            draft_path = Path(admission["distillation_draft_path"])
            draft = json.loads(draft_path.read_text())
            draft["markdown_body"] = draft["markdown_body"].replace(
                "[evidence:fixture-evidence]", "[evidence:unknown-evidence]", 1
            )
            draft_path.write_text(json.dumps(draft))
            approval_path = Path(admission["approval_record_path"])
            approval = json.loads(approval_path.read_text())
            approval["scope"]["distillation_draft_sha256"] = sha256_file(draft_path)
            approval_path.write_text(json.dumps(approval))
            with self.assertRaisesRegex(MemoryAdmissionError, "supplied sanitized evidence"):
                admit_memory(request, root / "wiki", root / "index.jsonl")

    def test_observed_state_rejects_unadmitted_edited_or_contaminating_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            wiki = root / "wiki"
            index = root / "index.jsonl"
            self.assertEqual(observed_memory_state(wiki, index).admitted_pages, 0)
            admit_memory(request, wiki, index)
            self.assertEqual(observed_memory_state(wiki, index).page_ids, ("fixture-environment-page",))

            (wiki / "unadmitted.md").write_text(memory_page("unadmitted-page"))
            with self.assertRaisesRegex(MemoryStateError, "never admitted"):
                observed_memory_state(wiki, index)
            (wiki / "unadmitted.md").unlink()
            page = wiki / "fixture-environment-page.md"
            original = page.read_text()
            page.write_text(original + "\n- Changed after approval.\n")
            with self.assertRaisesRegex(MemoryStateError, "changed after admission"):
                observed_memory_state(wiki, index)
            page.write_text(original)

            record = json.loads(index.read_text())
            record["task_id"] = "synthetic-held-out-task"
            index.write_text(json.dumps(record) + "\n")
            with self.assertRaisesRegex(MemoryStateError, "contaminates"):
                validate_memory_split(index, split_fixture())


if __name__ == "__main__":
    unittest.main()
