from __future__ import annotations

import json
import unittest

from artifact_memory.preregistration import (
    ATTESTATIONS_PATH,
    EXPECTED_DOCKER_COMPOSE_VERSION,
    EXPECTED_DOCKER_VERSION,
    EXPECTED_FREEZE_REVISION,
    FREEZE_PATH,
    EXPECTED_SPLIT_REVISION,
    PreregistrationError,
    load_freeze,
    validate_public_freeze,
    validate_student_manifest_against_freeze,
)
from tests.helpers import synthetic_manifest


class PreregistrationTests(unittest.TestCase):
    def test_public_freeze_has_no_placeholders_and_is_internally_consistent(self) -> None:
        validate_public_freeze()
        freeze = load_freeze()
        self.assertEqual(freeze["split_revision"], EXPECTED_SPLIT_REVISION)
        self.assertEqual(freeze["freeze_revision"], EXPECTED_FREEZE_REVISION)
        correction = freeze["corrective_refreeze"]
        self.assertEqual(correction["prior_measured_actor_attempts"], 0)
        self.assertFalse(correction["prior_execution_ledger_initialized"])
        self.assertEqual(correction["prior_execution_ledger_slots_consumed"], 0)
        self.assertFalse(correction["scientific_controls_changed"])
        self.assertEqual(correction["docker_version_record"], EXPECTED_DOCKER_VERSION)
        self.assertEqual(
            correction["docker_compose_version_record"],
            EXPECTED_DOCKER_COMPOSE_VERSION,
        )
        self.assertEqual(freeze["student_controls"]["context_tokens"], 32768)
        self.assertEqual(freeze["student_controls"]["max_turns"], 24)
        self.assertFalse(freeze["student_controls"]["summarization_enabled"])
        self.assertEqual(freeze["memory_controls"]["token_budget"], 1800)
        serialized = FREEZE_PATH.read_text()
        for marker in ("REQUIRED_", "TBD_", "CHANGEME", "PLACEHOLDER"):
            self.assertNotIn(marker, serialized)

    def test_safe_attestations_cover_exact_disjoint_measured_split(self) -> None:
        freeze = load_freeze()
        attestations = json.loads(ATTESTATIONS_PATH.read_text())
        task_ids = {task["task_id"] for task in attestations["tasks"]}
        split = freeze["split"]
        expected = set(split["memory_build_task_ids"]) | set(
            split["held_out_evaluation_task_ids"]
        )
        self.assertEqual(task_ids, expected)
        forbidden = (
            "command",
            "hidden_tests",
            "local_path",
            "mutation_patch",
            "reference_solution",
            "verifier_source",
        )
        serialized = ATTESTATIONS_PATH.read_text()
        for field in forbidden:
            self.assertNotIn(f'"{field}"', serialized)

    def test_non_frozen_measured_task_is_rejected(self) -> None:
        manifest = synthetic_manifest()
        manifest["data_classification"] = "measured"
        with self.assertRaisesRegex(PreregistrationError, "differs from the freeze"):
            validate_student_manifest_against_freeze(manifest)


if __name__ == "__main__":
    unittest.main()
