from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from artifact_memory.experiment import (
    LOCK_PATH,
    PROJECT_ROOT,
    ManifestError,
    assert_control_equivalence,
    build_harbor_command,
    build_llama_command,
    canonical_sha256,
    check_prerequisites,
    control_snapshot,
    harbor_environment,
    load_manifest,
    run_pair,
    validate_manifest,
    verified_memory_state,
)
from artifact_memory.sanitize import sha256_file
from artifact_memory.transfer import (
    DISTILLER_PROMPT_PATH,
    STUDENT_HF_REVISION,
    STUDENT_MODEL_ID,
    STUDENT_MODEL_SHA256,
    TEACHER_MODEL_ID,
    TEACHER_PROMPT_PATH,
)
from tests.helpers import FIXTURE_SHA, result_fixture, synthetic_manifest


class ManifestTests(unittest.TestCase):
    def test_synthetic_manifest_is_valid(self) -> None:
        validate_manifest(synthetic_manifest())

    def test_committed_template_hashes_match_versioned_files(self) -> None:
        template = load_manifest(PROJECT_ROOT / "manifests" / "measured-run-template.v2.json")
        prompt = template["controls"]["prompt"]
        self.assertEqual(prompt["system_sha256"], sha256_file(PROJECT_ROOT / "prompts" / "system.v1.md"))
        self.assertEqual(prompt["memory_sha256"], sha256_file(PROJECT_ROOT / "prompts" / "memory.v1.md"))
        self.assertEqual(
            template["roles"]["teacher"]["prompt"]["sha256"],
            sha256_file(TEACHER_PROMPT_PATH),
        )
        self.assertEqual(
            template["roles"]["distiller"]["prompt"]["sha256"],
            sha256_file(DISTILLER_PROMPT_PATH),
        )
        self.assertEqual(template["run_environment"]["python_lock_hash"], sha256_file(LOCK_PATH))
        self.assertEqual(template["roles"]["teacher"]["model_id"], TEACHER_MODEL_ID)
        self.assertEqual(template["roles"]["distiller"]["model_id"], TEACHER_MODEL_ID)
        self.assertEqual(template["roles"]["student"]["model_id"], STUDENT_MODEL_ID)
        self.assertEqual(
            template["roles"]["student"]["hugging_face_revision"], STUDENT_HF_REVISION
        )
        self.assertEqual(template["roles"]["student"]["sha256"], STUDENT_MODEL_SHA256)

    def test_non_frozen_synthetic_manifest_cannot_become_measured(self) -> None:
        manifest = synthetic_manifest()
        manifest["data_classification"] = "measured"
        with self.assertRaisesRegex(ManifestError, "differs from the freeze"):
            validate_manifest(manifest)

    def test_exact_role_identity_pins_and_student_only_task_are_required(self) -> None:
        manifest = synthetic_manifest()
        self.assertEqual(manifest["roles"]["teacher"]["model_id"], TEACHER_MODEL_ID)
        self.assertEqual(manifest["roles"]["distiller"]["model_id"], TEACHER_MODEL_ID)
        self.assertEqual(manifest["roles"]["student"]["model_id"], STUDENT_MODEL_ID)
        self.assertEqual(
            manifest["roles"]["student"]["hugging_face_revision"], STUDENT_HF_REVISION
        )
        self.assertEqual(manifest["roles"]["student"]["sha256"], STUDENT_MODEL_SHA256)
        manifest["task"]["executed_by_role"] = "cloud_teacher"
        with self.assertRaisesRegex(ManifestError, "local_student"):
            validate_manifest(manifest)

    def test_implementation_worker_cannot_be_added_as_a_measured_role(self) -> None:
        manifest = synthetic_manifest()
        manifest["implementation_worker_model"] = "gpt-5.6-sol"
        with self.assertRaisesRegex(ManifestError, "auditable role contract"):
            validate_manifest(manifest)

    def test_legacy_manifest_has_a_controlled_rejection(self) -> None:
        manifest = synthetic_manifest()
        manifest["schema_version"] = "paired-run-manifest-v1"
        with self.assertRaisesRegex(ManifestError, "legacy paired-run-manifest-v1"):
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
        manifest["data_classification"] = "development"
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

    def test_paired_run_rejects_staged_memory_states(self) -> None:
        manifest = synthetic_manifest()
        manifest["baseline_memory_contributions"] = 0
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ManifestError, "use run-condition"):
                run_pair(
                    manifest,
                    wiki_dir=root / "wiki",
                    index_path=root / "index.jsonl",
                    runs_dir=root / "runs",
                    preflight=False,
                )

        self.assertFalse((root / "runs").exists())

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
            "--include-task-name",
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

    def test_harbor_environment_renames_credential_without_mutating_parent(self) -> None:
        source = "ARTIFACT_MEMORY_FIXTURE_API_KEY"
        destination = "ARTIFACT_MEMORY_FIXTURE_AGENT_API_KEY"
        with patch.dict(os.environ, self.environment, clear=True):
            environment = harbor_environment(self.manifest)
            self.assertEqual(os.environ[source], "synthetic-fixture-key")
            self.assertNotIn(destination, os.environ)

        self.assertNotIn(source, environment)
        self.assertEqual(environment[destination], "synthetic-fixture-key")

    def test_preflight_subprocesses_receive_no_api_key_names(self) -> None:
        source = "ARTIFACT_MEMORY_FIXTURE_API_KEY"
        destination = "ARTIFACT_MEMORY_FIXTURE_AGENT_API_KEY"
        observed_environments: list[dict[str, str]] = []

        def runner(command: list[str], **kwargs: object) -> SimpleNamespace:
            environment = kwargs["env"]
            self.assertIsInstance(environment, dict)
            observed_environments.append(environment)
            stdout = ""
            if command == ["harbor", "run", "--help"]:
                stdout = "--dataset --path --include-task-name --agent-kwarg --skill --jobs-dir --job-name --extra-instruction-path"
            return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

        parent = dict(self.environment)
        parent[destination] = "stale-agent-key"
        with (
            patch.dict(os.environ, parent, clear=True),
            patch("artifact_memory.experiment._require_executable"),
            patch("artifact_memory.experiment._check_local_endpoint"),
        ):
            check_prerequisites(self.manifest, runner)
            self.assertEqual(os.environ[source], "synthetic-fixture-key")
            self.assertEqual(os.environ[destination], "stale-agent-key")

        self.assertTrue(observed_environments)
        for environment in observed_environments:
            self.assertNotIn(source, environment)
            self.assertNotIn(destination, environment)

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
