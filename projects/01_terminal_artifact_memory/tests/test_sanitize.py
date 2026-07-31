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
        digest = "sha256:" + "a1b2c3d4" * 8
        preserved_pins = (
            "brew install python@3.12 openssl@3",
            "npm install left-pad@1.3.0 node@lts",
            "nvm install node@18.x",
            "asdf ruby@3.2.x",
            "asdf fixture-tool@2.x.x",
            "npm install pkg@1.0.0-alpha.beta",
            "asdf golang@1.22.4",
            "python -m pip install fixture-pkg@3.12.0rc1",
            "pyenv install python@3.13.0b1",
            "python -m pip install fixture-pkg@3.12.0a7",
            "asdf fixture-lib@1.0c2",
            "fixture-tool@v2.1",
            "fixture-formula@version",
            f"docker pull ubuntu@{digest}",
            "rsync -avz src/ dst/ && npm install pkg@1.2.3",
            "ssh fixture-host 'brew install python@3.11'",
        )
        redacted_accounts = (
            "fixture-user@private-host",
            "fixture-person@example.invalid",
            "fixture-user@10.0.0.1",
            "fixture-admin@v2.example.invalid",
            "fixture-bot@v1-prod.example.invalid",
            "fixture-user@3rdparty.example.invalid",
            "fixture-ops@2host.example.invalid",
            "fixture-deploy@2host",
            "fixture-user@10box",
            "fixture-ops@buildbox",
        )
        remote_commands = (
            "ssh fixture-admin@v2",
            "ssh fixture-root@10",
            "scp fixture-local.txt fixture-user@2box:/tmp/fixture",
            "ssh -i /fixture/key fixture-user@host.invalid",
            "sftp fixture-user@3box",
            "mosh fixture-user@11",
        )
        text = "\n".join((*preserved_pins, *redacted_accounts, *remote_commands, "SYNTHETIC-CANARY"))
        output, report = sanitize_text(text, canaries=["SYNTHETIC-CANARY"])
        for preserved in preserved_pins:
            self.assertIn(preserved, output)
        for unsafe in (*redacted_accounts, "fixture-admin@v2", "fixture-root@10", "fixture-user@2box"):
            self.assertNotIn(unsafe, output)
        for fragment in ("example.invalid", "3rdparty", "2host", "v1-prod", "10box", "buildbox"):
            self.assertNotIn(fragment, output)
        for command in ("ssh ", "scp fixture-local.txt "):
            self.assertIn(command, output)
        self.assertEqual(
            report["replacement_counts"]["remote"],
            len(redacted_accounts) + len(remote_commands),
        )
        self.assertTrue(report["residual_scan"]["passed"])

    def test_remote_command_redaction_stays_inside_its_own_segment(self) -> None:
        text = "\n".join(
            [
                "ssh fixture-user@host.invalid && brew install python@3.12",
                "scp fixture-user@2box:/tmp/fixture . && npm install pkg@1.2.3",
                "rsync -avz src/ dst/ | tee fixture.log && asdf ruby@3.2.x",
                "SYNTHETIC-CANARY",
            ]
        )
        first, first_report = sanitize_text(text, canaries=["SYNTHETIC-CANARY"])
        for preserved in ("brew install python@3.12", "npm install pkg@1.2.3", "asdf ruby@3.2.x"):
            self.assertIn(preserved, first)
        for unsafe in ("fixture-user@host.invalid", "fixture-user@2box"):
            self.assertNotIn(unsafe, first)
        self.assertEqual(first_report["replacement_counts"]["remote"], 2)
        self.assertTrue(first_report["residual_scan"]["passed"])

        second, second_report = sanitize_text(first, canaries=["SYNTHETIC-CANARY"])
        self.assertEqual(second, first)
        self.assertNotIn("remote", second_report["replacement_counts"])
        self.assertTrue(second_report["residual_scan"]["passed"])

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
