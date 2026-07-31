"""End-to-end synthetic fixture smoke; outputs are never measured results."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from artifact_memory.analyze import analyze_results, discover_results
from artifact_memory.experiment import run_pair
from artifact_memory.memory import admit_memory
from tests.helpers import admission_fixture, synthetic_manifest


class SyntheticFixtureEndToEndSmoke(unittest.TestCase):
    def test_sanitization_admission_pair_and_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request, _, _ = admission_fixture(root)
            wiki = root / "wiki"
            index = root / "artifact-index.jsonl"
            admit_memory(request, wiki, index)

            def synthetic_harbor(
                command: list[str],
                *,
                capture_output: bool,
                text: bool,
                check: bool,
                env: dict[str, str],
            ) -> subprocess.CompletedProcess[str]:
                self.assertEqual(command[:2], ["harbor", "run"])
                self.assertEqual(
                    env["ARTIFACT_MEMORY_FIXTURE_AGENT_API_KEY"], "synthetic-fixture-key"
                )
                self.assertTrue(all("synthetic-fixture-key" not in part for part in command))
                jobs_dir = Path(command[command.index("--jobs-dir") + 1])
                job_name = command[command.index("--job-name") + 1]
                trial = jobs_dir / job_name / "synthetic-fixture-trial"
                (trial / "agent").mkdir(parents=True)
                (trial / "verifier").mkdir()
                (trial / "agent" / "trajectory.json").write_text(
                    json.dumps(
                        {
                            "schema_version": "synthetic-fixture-atif",
                            "session_id": "synthetic-fixture-session",
                            "steps": [],
                        }
                    )
                )
                reward = "1\n" if job_name.endswith("-m2") else "0\n"
                (trial / "verifier" / "reward.txt").write_text(reward)
                return subprocess.CompletedProcess(command, 0, "synthetic fixture", "")

            environment = {
                "ARTIFACT_MEMORY_FIXTURE_API_BASE": "http://localhost:8080/v1",
                "ARTIFACT_MEMORY_FIXTURE_API_KEY": "synthetic-fixture-key",
                "ARTIFACT_MEMORY_FIXTURE_MODEL_PATH": "models/synthetic-fixture.gguf",
            }
            with patch.dict(os.environ, environment, clear=False):
                pair_dir = run_pair(
                    synthetic_manifest(),
                    wiki_dir=wiki,
                    index_path=index,
                    runs_dir=root / "runs",
                    runner=synthetic_harbor,
                    preflight=False,
                )

            m0_skill = (pair_dir / "M0" / "retrieved-memory-skill" / "SKILL.md").read_text()
            m2_skill = (pair_dir / "M2" / "retrieved-memory-skill" / "SKILL.md").read_text()
            self.assertIn("name: verified-artifact-memory", m0_skill)
            self.assertIn("description: Required pilot instructions", m0_skill)
            self.assertIn("<no-retrieved-memory />", m0_skill)
            self.assertIn("fixture-environment-page", m2_skill)

            discovery = discover_results(root / "runs")
            outputs = analyze_results(
                discovery.results,
                root / "analysis",
                allow_non_measured=True,
                skipped=discovery.skipped,
            )
            summary = outputs["summary"].read_text()
            self.assertEqual(discovery.skipped, [])
            self.assertIn("Paired result records analyzed: 2", summary)
            self.assertIn("Positive transfer: 1", summary)
            self.assertIn("NON-MEASURED", summary)
            self.assertNotIn("MEASURED RESULTS.", summary)


if __name__ == "__main__":
    unittest.main()
