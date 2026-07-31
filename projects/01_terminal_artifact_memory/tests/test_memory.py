from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lily.memory import MemoryAdmissionError, admit_memory, retrieve
from tests.helpers import admission_fixture, memory_page


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
            self.assertTrue(all(page.score > 0 for page in first.pages))

    def test_retrieval_honors_top_k_and_token_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            wiki = Path(directory)
            (wiki / "a.md").write_text(memory_page("fixture-page-a"))
            (wiki / "b.md").write_text(memory_page("fixture-page-b"))
            limited = retrieve("package environment", wiki, top_k=1, token_budget=5000)
            self.assertEqual(len(limited.pages), 1)
            too_small = retrieve("package environment", wiki, top_k=2, token_budget=1)
            self.assertEqual(too_small.pages, ())
            self.assertEqual(too_small.used_tokens, 0)

    def test_memory_admission_requires_all_gates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            destination = admit_memory(request, root / "wiki", root / "index.jsonl")
            self.assertTrue(destination.is_file())
            self.assertIn("[evidence:fixture-evidence]", destination.read_text())
            index = json.loads((root / "index.jsonl").read_text())
            self.assertEqual(index["page_id"], "fixture-environment-page")

    def test_memory_admission_rejects_incomplete_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            value = json.loads(request.read_text())
            del value["provenance"]["hardware_description"]
            request.write_text(json.dumps(value))
            with self.assertRaisesRegex(MemoryAdmissionError, "incomplete provenance"):
                admit_memory(request, root / "wiki", root / "index.jsonl")

    def test_memory_admission_rejects_unlinked_trajectory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            value = json.loads(request.read_text())
            value["provenance"]["trajectory_sha256"] = "f" * 64
            request.write_text(json.dumps(value))
            with self.assertRaisesRegex(MemoryAdmissionError, "provenance-linked trajectory"):
                admit_memory(request, root / "wiki", root / "index.jsonl")

    def test_memory_admission_requires_explicit_human_approval(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            value = json.loads(request.read_text())
            value["human_review"]["approved"] = False
            request.write_text(json.dumps(value))
            with self.assertRaisesRegex(MemoryAdmissionError, "human review"):
                admit_memory(request, root / "wiki", root / "index.jsonl")

    def test_memory_admission_rejects_failed_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            value = json.loads(request.read_text())
            value["verifier"]["passed"] = False
            request.write_text(json.dumps(value))
            with self.assertRaisesRegex(MemoryAdmissionError, "verifier did not pass"):
                admit_memory(request, root / "wiki", root / "index.jsonl")

    def test_memory_admission_rejects_multiline_distillation_injection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            value = json.loads(request.read_text())
            value["summary"]["title"] = "Fixture title\n## Injected section"
            request.write_text(json.dumps(value))
            with self.assertRaisesRegex(MemoryAdmissionError, "single-line"):
                admit_memory(request, root / "wiki", root / "index.jsonl")

    def test_memory_admission_rejects_unsafe_distillation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            value = json.loads(request.read_text())
            unsafe_path = "/" + "Users/fixture-person/private"
            value["summary"]["problem_pattern"] = unsafe_path
            request.write_text(json.dumps(value))
            with self.assertRaisesRegex(MemoryAdmissionError, "unsafe classes"):
                admit_memory(request, root / "wiki", root / "index.jsonl")


if __name__ == "__main__":
    unittest.main()
