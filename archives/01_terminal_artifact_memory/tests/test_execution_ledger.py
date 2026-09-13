from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from artifact_memory.execution_ledger import (
    LEDGER_ENV,
    LEDGER_FILENAME,
    ExecutionLedgerError,
    complete_attempt,
    initialize,
    reserve_attempt,
)


class ExecutionLedgerTests(unittest.TestCase):
    def test_single_global_sequence_is_ordered_and_one_attempt(self) -> None:
        revision = "a" * 40
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / LEDGER_FILENAME
            anchor = Path(directory).resolve() / "ledger-anchor"
            with patch(
                "artifact_memory.execution_ledger.validate_landed_freeze_revision",
                return_value=revision,
            ), patch(
                "artifact_memory.execution_ledger._anchor_path",
                return_value=anchor,
            ), patch.dict(os.environ, {LEDGER_ENV: str(path)}):
                initialize(path)
                self.assertEqual(path.stat().st_mode & 0o077, 0)
                alternate = path.parent / "alternate" / LEDGER_FILENAME
                with patch.dict(os.environ, {LEDGER_ENV: str(alternate)}):
                    with self.assertRaisesRegex(ExecutionLedgerError, "checkout-wide anchor"):
                        reserve_attempt("M0", "configure-git-webserver")
                with self.assertRaisesRegex(ExecutionLedgerError, "next frozen attempt"): 
                    reserve_attempt("teacher", "openssl-selfsigned-cert")
                reserve_attempt("M0", "configure-git-webserver")
                with self.assertRaisesRegex(ExecutionLedgerError, "already started"):
                    reserve_attempt("M0", "configure-git-webserver")
                complete_attempt("M0", "configure-git-webserver", "b" * 64)
                with self.assertRaisesRegex(ExecutionLedgerError, "next frozen attempt"):
                    reserve_attempt("M0", "configure-git-webserver")
                document = json.loads(path.read_text())
                self.assertEqual(document["next_index"], 1)
                self.assertEqual(document["attempts"][0]["attempt_count"], 1)
                self.assertEqual(document["attempts"][0]["status"], "complete")


if __name__ == "__main__":
    unittest.main()
