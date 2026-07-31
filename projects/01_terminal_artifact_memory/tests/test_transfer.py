from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from artifact_memory.sanitize import sha256_file
from artifact_memory.transfer import (
    DENIED_CLOUD_DATA,
    DISTILLER_ALLOWED_FIELDS,
    STUDENT_HF_REVISION,
    STUDENT_MODEL_ID,
    STUDENT_MODEL_SHA256,
    TEACHER_MODEL_ID,
    TransferError,
    prepare_distillation_request,
    validate_build_manifest,
    validate_distillation_draft,
    validate_roles,
    validate_transmission_policy,
)
from tests.helpers import admission_fixture, synthetic_manifest


class RoleAndDisclosureTests(unittest.TestCase):
    def test_exact_teacher_distiller_and_student_pins_are_separate(self) -> None:
        manifest = synthetic_manifest()
        validate_roles(manifest["roles"])
        self.assertEqual(manifest["roles"]["teacher"]["model_id"], TEACHER_MODEL_ID)
        self.assertEqual(manifest["roles"]["distiller"]["model_id"], TEACHER_MODEL_ID)
        self.assertEqual(manifest["roles"]["student"]["model_id"], STUDENT_MODEL_ID)
        self.assertEqual(
            manifest["roles"]["student"]["hugging_face_revision"], STUDENT_HF_REVISION
        )
        self.assertEqual(manifest["roles"]["student"]["sha256"], STUDENT_MODEL_SHA256)
        self.assertFalse(manifest["roles"]["teacher"]["may_score_student_evaluation"])
        self.assertTrue(manifest["roles"]["student"]["sole_evaluation_model"])

    def test_role_conflation_is_rejected(self) -> None:
        roles = synthetic_manifest()["roles"]
        roles["teacher"]["model_id"] = STUDENT_MODEL_ID
        with self.assertRaisesRegex(TransferError, "exact pinned model"):
            validate_roles(roles)

    def test_transmission_policy_is_an_exact_allow_and_deny_inventory(self) -> None:
        policy = synthetic_manifest()["data_transmission"]
        validate_transmission_policy(policy)
        self.assertEqual(
            policy["distiller"]["allowed_request_fields"], list(DISTILLER_ALLOWED_FIELDS)
        )
        self.assertEqual(policy["denied_for_all_cloud_roles"], list(DENIED_CLOUD_DATA))
        policy["distiller"]["allowed_request_fields"].append("raw_trajectory.content")
        with self.assertRaisesRegex(TransferError, "explicit allowlist"):
            validate_transmission_policy(policy)


class TransferLifecycleTests(unittest.TestCase):
    def test_build_provenance_is_teacher_only_and_split_disjoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            admission, _, _ = admission_fixture(root)
            request = json.loads(admission.read_text())
            build_path = Path(request["build_manifest_path"])
            build = json.loads(build_path.read_text())
            validate_build_manifest(build)
            build["execution"]["executed_by_role"] = "local_student"
            with self.assertRaisesRegex(TransferError, "cloud_teacher"):
                validate_build_manifest(build)

            build = json.loads(build_path.read_text())
            build["split"]["held_out_evaluation_task_ids"] = ["synthetic-build-task"]
            with self.assertRaisesRegex(TransferError, "overlap"):
                validate_build_manifest(build)

    def test_local_sanitizer_and_verifier_gate_precede_distillation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            admission, sanitized, report_path = admission_fixture(root)
            paths = json.loads(admission.read_text())
            build_path = Path(paths["build_manifest_path"])
            output = root / "regenerated-request.json"
            packet = prepare_distillation_request(build_path, output)
            serialized = json.dumps(packet)
            self.assertEqual(packet["source_evidence"][0]["content"], sanitized.read_text())
            self.assertNotIn("SYNTHETIC-FIXTURE-CANARY", serialized)
            self.assertNotIn("replacement_counts", serialized)
            self.assertNotIn("raw-fixture.txt", serialized)
            self.assertNotIn("sanitizer-fixture.json", serialized)
            self.assertEqual(packet["gate_attestations"]["executable_verifier_passed"], True)

            report = json.loads(report_path.read_text())
            report["accepted_for_human_review"] = False
            report_path.write_text(json.dumps(report))
            with self.assertRaisesRegex(TransferError, "before distillation"):
                prepare_distillation_request(build_path, root / "must-not-exist.json")
            self.assertFalse((root / "must-not-exist.json").exists())

    def test_missing_or_mismatched_distillation_provenance_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            admission, _, _ = admission_fixture(root)
            paths = json.loads(admission.read_text())
            build = Path(paths["build_manifest_path"])
            request = Path(paths["distillation_request_path"])
            draft = Path(paths["distillation_draft_path"])
            validate_distillation_draft(build, request, draft)
            value = json.loads(draft.read_text())
            value["distiller_model_id"] = "different-model"
            draft.write_text(json.dumps(value))
            with self.assertRaisesRegex(TransferError, "distiller_model_id"):
                validate_distillation_draft(build, request, draft)


if __name__ == "__main__":
    unittest.main()
