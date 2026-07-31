from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from artifact_memory.sanitize import sha256_file
from artifact_memory.verifier_qualification import (
    VerifierQualificationError,
    validate_qualification_path,
    validate_qualification_record,
)
from tests.helpers import (
    FIXTURE_CONTAINER_DIGEST,
    FIXTURE_REVISION,
    FIXTURE_SHA,
    qualification_fixture,
)


class VerifierQualificationTests(unittest.TestCase):
    def validate(self, record: dict[str, object], instruction_sha: str = FIXTURE_SHA) -> None:
        validate_qualification_record(
            record,
            task_id="synthetic-build-task",
            terminal_bench_revision=FIXTURE_REVISION,
            task_instruction_sha256=instruction_sha,
            task_container_digest=FIXTURE_CONTAINER_DIGEST,
            verifier_bundle_sha256=FIXTURE_SHA,
        )

    def test_complete_development_only_record_is_eligible(self) -> None:
        self.validate(qualification_fixture(FIXTURE_SHA))

    def test_pin_or_record_hash_mismatch_is_rejected(self) -> None:
        record = qualification_fixture(FIXTURE_SHA)
        record["pins"]["verifier_bundle_sha256"] = "c" * 64
        with self.assertRaisesRegex(VerifierQualificationError, "does not match"):
            self.validate(record)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qualification.json"
            path.write_text("{}")
            with self.assertRaisesRegex(VerifierQualificationError, "hash mismatch"):
                validate_qualification_path(
                    path,
                    expected_record_sha256=FIXTURE_SHA,
                    task_id="synthetic-build-task",
                    terminal_bench_revision=FIXTURE_REVISION,
                    task_instruction_sha256=FIXTURE_SHA,
                    task_container_digest=FIXTURE_CONTAINER_DIGEST,
                    verifier_bundle_sha256=FIXTURE_SHA,
                )
            self.assertNotEqual(sha256_file(path), FIXTURE_SHA)

    def test_incomplete_public_requirement_coverage_is_rejected(self) -> None:
        record = qualification_fixture(FIXTURE_SHA)
        record["targeted_negative_controls"].pop()
        with self.assertRaisesRegex(VerifierQualificationError, "do not cover"):
            self.validate(record)

    def test_false_reject_and_false_accept_are_ineligible(self) -> None:
        false_reject = qualification_fixture(FIXTURE_SHA)
        false_reject["known_good_positive_control"]["accepted"] = 1
        with self.assertRaisesRegex(VerifierQualificationError, "known-good"):
            self.validate(false_reject)

        false_accept = qualification_fixture(FIXTURE_SHA)
        false_accept["targeted_negative_controls"][0]["accepted"] = 1
        with self.assertRaisesRegex(VerifierQualificationError, "accepted a targeted broken"):
            self.validate(false_accept)

    def test_nondeterminism_and_failed_isolation_are_ineligible(self) -> None:
        nondeterministic = qualification_fixture(FIXTURE_SHA)
        nondeterministic["clean_container_determinism"]["distinct_reward_values"] = [0.0, 1.0]
        with self.assertRaisesRegex(VerifierQualificationError, "nondeterministic"):
            self.validate(nondeterministic)

        not_isolated = qualification_fixture(FIXTURE_SHA)
        not_isolated["reward_and_test_isolation"]["tamper_accepts"] = 1
        with self.assertRaisesRegex(VerifierQualificationError, "tamper resistance"):
            self.validate(not_isolated)

    def test_verifier_internals_cannot_enter_compact_record(self) -> None:
        record = qualification_fixture(FIXTURE_SHA)
        record["verifier_source"] = "synthetic forbidden detail"
        with self.assertRaisesRegex(VerifierQualificationError, "prohibited verifier detail"):
            self.validate(record)


if __name__ == "__main__":
    unittest.main()
