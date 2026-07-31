from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from artifact_memory.sanitize import build_gitleaks_command, sanitize_artifact, sanitize_text
from tests.helpers import clean_gitleaks


class SanitizerTests(unittest.TestCase):
    def test_privacy_classes_are_redacted(self) -> None:
        private_path = "/" + "Users/fixture-person/work/repository"
        text = "\n".join(
            [
                private_path,
                "host=fixture-node.lan",
                "network 10.2.3.4",
                "ssh://example.invalid/team/repository",
                "fixture-user@private-host",
                "/workspace/task/file.txt",
                "/mnt/fixture/data.txt",
                "SYNTHETIC-CANARY",
            ]
        )
        output, report = sanitize_text(text, canaries=["SYNTHETIC-CANARY"])
        for unsafe in (
            private_path,
            "fixture-node.lan",
            "10.2.3.4",
            "example.invalid",
            "fixture-user@private-host",
        ):
            self.assertNotIn(unsafe, output)
        self.assertEqual(report["blocking_classes"], [])
        self.assertTrue(report["canary"]["all_detected"])
        self.assertTrue(report["residual_scan"]["passed"])

    def test_account_forms_are_redacted_and_version_pins_are_kept(self) -> None:
        text = "\n".join(
            [
                "brew install python@3.12 openssl@3",
                "npm install left-pad@1.3.0 node@lts",
                "image pinned at fixture-tool@v2.1",
                "fixture-user@private-host",
                "fixture-person@example.invalid",
                "fixture-user@10.0.0.1",
                "SYNTHETIC-CANARY",
            ]
        )
        output, report = sanitize_text(text, canaries=["SYNTHETIC-CANARY"])
        for preserved in ("python@3.12", "openssl@3", "left-pad@1.3.0", "node@lts", "fixture-tool@v2.1"):
            self.assertIn(preserved, output)
        for unsafe in (
            "fixture-user@private-host",
            "fixture-person@example.invalid",
            "fixture-user@10.0.0.1",
        ):
            self.assertNotIn(unsafe, output)
        self.assertEqual(report["replacement_counts"]["remote"], 3)
        self.assertTrue(report["residual_scan"]["passed"])

    def test_contamination_and_credential_classes_block(self) -> None:
        credential = "api" + "_key=" + "x" * 20
        hidden = "hidden" + "_tests/check.py"
        reference = "reference" + "_solution/answer.txt"
        verifier_detail = "verifier" + "/reward.txt"
        text = f"{credential}\n{hidden}\n{reference}\n{verifier_detail}\nSYNTHETIC-CANARY\n"
        output, report = sanitize_text(text, canaries=["SYNTHETIC-CANARY"])
        self.assertNotIn("x" * 20, output)
        self.assertEqual(
            report["blocking_classes"],
            ["credential", "hidden_test", "reference_solution", "verifier_detail"],
        )

    def test_missing_canary_fails_admission_gate(self) -> None:
        _, report = sanitize_text("safe fixture", canaries=["EXPECTED-CANARY"])
        self.assertFalse(report["canary"]["all_detected"])

    def test_gitleaks_failure_prevents_human_review(self) -> None:
        def leaking(_target: Path, _report: Path) -> dict[str, object]:
            return {
                "clean": False,
                "exit_code": 1,
                "findings_count": 1,
                "command_interface": "synthetic-fixture-stub",
            }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fixture.txt"
            source.write_text("safe fixture SYNTHETIC-CANARY")
            report = sanitize_artifact(
                source,
                root / "output.txt",
                root / "report.json",
                artifact_id="fixture-artifact",
                canaries=["SYNTHETIC-CANARY"],
                gitleaks_runner=leaking,
            )
            self.assertFalse(report["accepted_for_human_review"])

    def test_clean_sanitized_artifact_is_reviewable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fixture.txt"
            source.write_text("safe fixture SYNTHETIC-CANARY")
            report = sanitize_artifact(
                source,
                root / "output.txt",
                root / "report.json",
                artifact_id="fixture-artifact",
                canaries=["SYNTHETIC-CANARY"],
                gitleaks_runner=clean_gitleaks,
            )
            self.assertTrue(report["accepted_for_human_review"])
            self.assertTrue(report["gitleaks"]["source_scan_completed"])
            self.assertEqual(report["gitleaks"]["findings_count"], 0)

    def test_gitleaks_command_uses_current_dir_interface(self) -> None:
        command = build_gitleaks_command(Path("artifact.txt"), Path("report.json"))
        self.assertEqual(command[:2], ["gitleaks", "dir"])
        self.assertIn("--report-format", command)
        self.assertNotIn("detect", command)


if __name__ == "__main__":
    unittest.main()
