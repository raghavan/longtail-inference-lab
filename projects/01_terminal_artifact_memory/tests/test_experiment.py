from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from artifact_memory.experiment import (
    LOCK_PATH,
    PROJECT_ROOT,
    ManifestError,
    assert_control_equivalence,
    build_harbor_command,
    build_llama_command,
    canonical_sha256,
    control_snapshot,
    load_manifest,
    validate_manifest,
    verified_memory_state,
)
from artifact_memory.sanitize import sha256_file
from tests.helpers import FIXTURE_SHA, result_fixture, synthetic_manifest


class ManifestTests(unittest.TestCase):
    def test_synthetic_manifest_is_valid(self) -> None:
        validate_manifest(synthetic_manifest())

    def test_committed_template_hashes_match_versioned_files(self) -> None:
        template = load_manifest(PROJECT_ROOT / "manifests" / "measured-run-template.v1.json")
        prompt = template["controls"]["prompt"]
        self.assertEqual(prompt["system_sha256"], sha256_file(PROJECT_ROOT / "prompts" / "system.v1.md"))
        self.assertEqual(prompt["memory_sha256"], sha256_file(PROJECT_ROOT / "prompts" / "memory.v1.md"))
        self.assertEqual(template["run_environment"]["python_lock_hash"], sha256_file(LOCK_PATH))

    def test_complete_measured_manifest_is_structurally_valid(self) -> None:
        manifest = synthetic_manifest()
        manifest["data_classification"] = "measured"
        validate_manifest(manifest)

    def test_incomplete_measured_provenance_is_rejected(self) -> None:
        manifest = synthetic_manifest()
        manifest["data_classification"] = "measured"
        del manifest["run_environment"]["hardware_description"]
        with self.assertRaisesRegex(ManifestError, "incomplete measured-run provenance"):
            validate_manifest(manifest)

    def test_measured_placeholders_are_rejected(self) -> None:
        manifest = synthetic_manifest()
        manifest["data_classification"] = "measured"
        manifest["run_environment"]["hardware_description"] = "REQUIRED_HARDWARE"
        with self.assertRaisesRegex(ManifestError, "placeholders"):
            validate_manifest(manifest)

    def test_ordinary_prose_is_not_treated_as_a_placeholder(self) -> None:
        manifest = synthetic_manifest()
        manifest["data_classification"] = "measured"
        manifest["task"]["retrieval_query"] = "install the required build toolchain and configure PATH"
        manifest["run_environment"]["hardware_description"] = "laptop, 16 GB required"
        validate_manifest(manifest)

    def test_memory_state_must_match_the_admitted_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            wiki.mkdir()
            index = root / "index.jsonl"
            manifest = synthetic_manifest()
            with self.assertRaisesRegex(ManifestError, "memory_contributions"):
                verified_memory_state(manifest, wiki, index)
            manifest["memory_contributions"] = 0
            with self.assertRaisesRegex(ManifestError, "memory_checkpoint"):
                verified_memory_state(manifest, wiki, index)
            manifest["memory_checkpoint"] = 0
            self.assertEqual(verified_memory_state(manifest, wiki, index).admitted_pages, 0)

    def test_measured_container_digest_must_be_immutable(self) -> None:
        for digest in ("sha256:abc123", "sha256:changeme", "sha256:" + "g" * 64):
            manifest = synthetic_manifest()
            manifest["data_classification"] = "measured"
            manifest["run_environment"]["task_container_digest"] = digest
            with self.assertRaisesRegex(ManifestError, "task_container_digest"):
                validate_manifest(manifest)

    def test_measured_hashes_are_not_inferred(self) -> None:
        manifest = synthetic_manifest()
        manifest["data_classification"] = "measured"
        manifest["run_environment"]["python_lock_hash"] = "short"
        with self.assertRaisesRegex(ManifestError, "python_lock_hash"):
            validate_manifest(manifest)

    def test_m0_m2_control_difference_is_rejected(self) -> None:
        m0, m2 = result_fixture("fixture-pair", False, True)
        m2["control_snapshot"]["controls"]["decoding"]["seed"] = 99
        with self.assertRaisesRegex(ManifestError, "fixed control"):
            assert_control_equivalence(m0, m2)

    def test_control_digest_is_canonical(self) -> None:
        snapshot = control_snapshot(synthetic_manifest())
        reordered = json.loads(json.dumps(snapshot, sort_keys=True))
        self.assertEqual(canonical_sha256(snapshot), canonical_sha256(reordered))


class ExternalCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = synthetic_manifest()
        self.environment = {
            "ARTIFACT_MEMORY_FIXTURE_API_BASE": "http://localhost:8080/v1",
            "ARTIFACT_MEMORY_FIXTURE_API_KEY": "synthetic-fixture-key",
            "ARTIFACT_MEMORY_FIXTURE_MODEL_PATH": "models/synthetic-fixture.gguf",
        }

    def test_harbor_command_is_narrow_and_explicit(self) -> None:
        with patch.dict(os.environ, self.environment, clear=False):
            command = build_harbor_command(
                self.manifest,
                condition="M2",
                jobs_dir=Path("fixture-jobs"),
                skill_dir=Path("fixture-skill"),
            )
        self.assertEqual(command[:2], ["harbor", "run"])
        for flag in (
            "--dataset",
            "--task-name",
            "--agent",
            "--model",
            "--env",
            "--skill",
            "--agent-kwarg",
        ):
            self.assertIn(flag, command)
        self.assertIn("terminus-2", command)
        self.assertIn("docker", command)
        self.assertIn("api_base=http://localhost:8080/v1", command)
        self.assertIn('llm_call_kwargs={"seed":7}', command)

    def test_harbor_conditions_only_change_output_and_memory_paths(self) -> None:
        with patch.dict(os.environ, self.environment, clear=False):
            m0 = build_harbor_command(
                self.manifest,
                condition="M0",
                jobs_dir=Path("m0-jobs"),
                skill_dir=Path("m0-skill"),
            )
            m2 = build_harbor_command(
                self.manifest,
                condition="M2",
                jobs_dir=Path("m2-jobs"),
                skill_dir=Path("m2-skill"),
            )
        variable_flags = {"--job-name", "--jobs-dir", "--skill"}

        def fixed(argv: list[str]) -> list[str]:
            output: list[str] = []
            index = 0
            while index < len(argv):
                if argv[index] in variable_flags:
                    index += 2
                else:
                    output.append(argv[index])
                    index += 1
            return output

        self.assertEqual(fixed(m0), fixed(m2))

    def test_llama_server_command_uses_documented_flags(self) -> None:
        with patch.dict(os.environ, self.environment, clear=False):
            command = build_llama_command(self.manifest)
        self.assertEqual(command[0], "llama-server")
        self.assertEqual(
            command[1:],
            [
                "--model",
                "models/synthetic-fixture.gguf",
                "--ctx-size",
                "4096",
                "--host",
                "localhost",
                "--port",
                "8080",
            ],
        )


if __name__ == "__main__":
    unittest.main()
