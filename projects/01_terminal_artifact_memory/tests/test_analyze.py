from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from lily.analyze import AnalysisError, analyze_results, pair_results
from tests.helpers import result_fixture


class AnalysisTests(unittest.TestCase):
    def fixture_results(self) -> list[dict[str, object]]:
        results: list[dict[str, object]] = []
        for pair_id, outcomes in (
            ("fixture-positive", (False, True)),
            ("fixture-negative", (True, False)),
            ("fixture-stable", (True, True)),
            ("fixture-unresolved", (False, False)),
        ):
            results.extend(result_fixture(pair_id, *outcomes))
        return results

    def test_four_transfer_classes_and_judge_cannot_override(self) -> None:
        pairs = pair_results(self.fixture_results(), allow_non_measured=True)
        self.assertEqual(
            [pair.transfer for pair in pairs],
            [
                "negative_transfer",
                "positive_transfer",
                "stable_success",
                "unresolved_task",
            ],
        )
        unresolved = next(pair for pair in pairs if pair.m0["pair_id"] == "fixture-unresolved")
        self.assertEqual(unresolved.m2["judge_probability"], 1.0)
        self.assertEqual(unresolved.transfer, "unresolved_task")

    def test_non_measured_data_is_refused_by_default(self) -> None:
        with self.assertRaisesRegex(AnalysisError, "non-measured data refused"):
            pair_results(self.fixture_results())

    def test_analysis_writes_labeled_csv_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = analyze_results(
                self.fixture_results(), root, allow_non_measured=True
            )
            summary = outputs["summary"].read_text()
            self.assertIn("NON-MEASURED DEVELOPMENT OR SYNTHETIC FIXTURE DATA", summary)
            self.assertIn("Positive transfer: 1", summary)
            self.assertIn("Negative transfer: 1", summary)
            self.assertIn("Stable success: 1", summary)
            self.assertIn("Unresolved tasks: 1", summary)
            self.assertIn("Retrieval coverage: 1.000", summary)
            with outputs["results_csv"].open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 4)
            self.assertEqual(
                {row["transfer"] for row in rows},
                {
                    "positive_transfer",
                    "negative_transfer",
                    "stable_success",
                    "unresolved_task",
                },
            )

    def test_missing_pair_is_rejected(self) -> None:
        m0, _ = result_fixture("fixture-incomplete", False, True)
        with self.assertRaisesRegex(AnalysisError, "missing M0 or M2"):
            pair_results([m0], allow_non_measured=True)

    def test_non_executable_authority_is_rejected(self) -> None:
        m0, m2 = result_fixture("fixture-authority", False, True)
        m2["verifier_authority"] = "learned-judge"
        with self.assertRaisesRegex(AnalysisError, "executable verifier"):
            pair_results([m0, m2], allow_non_measured=True)


if __name__ == "__main__":
    unittest.main()
