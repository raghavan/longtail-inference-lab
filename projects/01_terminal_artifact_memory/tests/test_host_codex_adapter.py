from __future__ import annotations

import asyncio
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from artifact_memory.host_codex_distiller import (
    build_distiller_command,
    validate_no_tools_event_stream,
)
from artifact_memory.host_codex_adapter import (
    ADAPTER_ID,
    CODEX_MODEL_ID,
    CODEX_VERSION,
    HostCodexAdapterError,
    TaskBridgeServer,
    build_codex_command,
    codex_events_to_atif,
    contains_credential_material,
    sensitive_environment_names,
    validate_bridge_audit,
    validate_host_codex,
    validate_task_command,
    write_private_text,
)


class HostCodexPreflightTests(unittest.TestCase):
    @staticmethod
    def runner(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        outputs = {
            ("codex", "--version"): f"codex-cli {CODEX_VERSION}\n",
            ("codex", "login", "status"): "Logged in using ChatGPT\n",
            ("codex", "debug", "models"): json.dumps(
                {"models": [{"slug": CODEX_MODEL_ID, "context_window": 272000}]}
            ),
        }
        return subprocess.CompletedProcess(argv, 0, outputs[tuple(argv)], "")

    def test_exact_subscription_model_and_version_are_required(self) -> None:
        result = validate_host_codex(CODEX_MODEL_ID, runner=self.runner)
        self.assertEqual(result.adapter_id, ADAPTER_ID)
        self.assertEqual(result.codex_version, CODEX_VERSION)
        self.assertEqual(result.model_id, CODEX_MODEL_ID)
        self.assertEqual(result.login_method, "existing-chatgpt-subscription")
        self.assertFalse(result.credential_material_forwarded)

        with self.assertRaisesRegex(HostCodexAdapterError, "model must be exactly"):
            validate_host_codex("different-model", runner=self.runner)

    def test_version_or_login_mismatch_fails_before_execution(self) -> None:
        def wrong_version(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            value = self.runner(argv, **kwargs)
            if argv == ["codex", "--version"]:
                value.stdout = "codex-cli 0.145.0\n"
            return value

        with self.assertRaisesRegex(HostCodexAdapterError, "must be exactly"):
            validate_host_codex(CODEX_MODEL_ID, runner=wrong_version)

        def wrong_login(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            value = self.runner(argv, **kwargs)
            if argv == ["codex", "login", "status"]:
                value.stdout = "Not logged in\n"
            return value

        with self.assertRaisesRegex(HostCodexAdapterError, "existing ChatGPT"):
            validate_host_codex(CODEX_MODEL_ID, runner=wrong_login)


class HostCodexBoundaryTests(unittest.TestCase):
    def test_codex_command_is_ephemeral_exact_and_task_tool_only(self) -> None:
        command = build_codex_command(
            instruction="Synthetic public fixture instruction",
            endpoint="unix:///private-fixture/task.sock",
            python_executable="/fixture/python",
            module_root=Path("/fixture/module"),
        )
        self.assertEqual(command[0], "codex")
        self.assertIn("exec", command)
        self.assertIn("--ephemeral", command)
        self.assertIn("--ask-for-approval", command)
        self.assertIn("never", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn(CODEX_MODEL_ID, command)
        for feature in ("shell_tool", "unified_exec", "apps", "browser_use", "computer_use"):
            self.assertIn(feature, command)
        serialized = " ".join(command)
        self.assertNotIn("auth.json", serialized)
        self.assertNotIn("OPENAI_API_KEY", serialized)
        self.assertNotIn("CODEX_ACCESS_TOKEN", serialized)

    def test_task_command_validation_is_bounded_not_text_based(self) -> None:
        validate_task_command("python3 -m unittest")
        # Text matching is not the isolation boundary; Landlock denies these
        # targets regardless of shell spelling when the command executes.
        validate_task_command("cat /tests/test_hidden.py")
        with self.assertRaisesRegex(HostCodexAdapterError, "bounded input"):
            validate_task_command("echo fixture\x00suffix")

    def test_credential_material_guards_are_value_sensitive(self) -> None:
        self.assertFalse(contains_credential_material("Credentials must not be requested."))
        self.assertTrue(contains_credential_material("Authorization: Bearer abcdefghijklmnopqrstuvwxyz"))
        self.assertTrue(contains_credential_material('"refresh_token":"fixture"'))
        self.assertTrue(contains_credential_material("GH_TOKEN=abcdefghijklmnopqrstuvwxyz"))
        self.assertEqual(
            sensitive_environment_names(
                [
                    "PATH",
                    "GH_TOKEN",
                    "DATABASE_PASSWORD",
                    "AWS_ACCESS_KEY_ID",
                    "GOOGLE_APPLICATION_CREDENTIALS",
                    "DATABASE_URL",
                ]
            ),
            [
                "AWS_ACCESS_KEY_ID",
                "DATABASE_PASSWORD",
                "DATABASE_URL",
                "GH_TOKEN",
                "GOOGLE_APPLICATION_CREDENTIALS",
            ],
        )

    def test_private_provenance_writes_reject_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.txt"
            target.write_text("unchanged")
            link = root / "events.jsonl"
            link.symlink_to(target)
            with self.assertRaises((HostCodexAdapterError, OSError)):
                write_private_text(link, "unsafe")
            self.assertEqual(target.read_text(), "unchanged")

    def test_bridge_executes_only_the_supplied_task_executor(self) -> None:
        async def exercise() -> None:
            calls: list[tuple[str, int]] = []

            async def executor(command: str, timeout: int) -> tuple[int, str, str]:
                calls.append((command, timeout))
                return 0, "fixture output", ""

            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory).resolve()
                async with TaskBridgeServer(
                    root / "bridge.sock", executor, root / "audit.jsonl", max_timeout_seconds=30
                ) as bridge:
                    reader, writer = await asyncio.open_unix_connection(str(root / "bridge.sock"))
                    writer.write(
                        (
                            json.dumps(
                                {
                                    "auth_token": bridge.auth_token,
                                    "bridge_call_id": "a" * 32,
                                    "command": "echo fixture",
                                    "timeout_seconds": 90,
                                }
                            )
                            + "\n"
                        ).encode()
                    )
                    await writer.drain()
                    response = json.loads(await reader.readline())
                    writer.close()
                    await writer.wait_closed()

                    reader, writer = await asyncio.open_unix_connection(str(root / "bridge.sock"))
                    writer.write(
                        b'{"auth_token":"wrong","bridge_call_id":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","command":"echo bypass","timeout_seconds":1}\n'
                    )
                    await writer.drain()
                    rejected = json.loads(await reader.readline())
                    writer.close()
                    await writer.wait_closed()
                self.assertEqual(calls, [("echo fixture", 30)])
                self.assertTrue(response["ok"])
                self.assertFalse(rejected["ok"])
                self.assertIn("fixture output", response["output"])
                self.assertEqual((root / "audit.jsonl").stat().st_mode & 0o077, 0)
                audit = json.loads((root / "audit.jsonl").read_text())
                self.assertEqual(audit["bounded_timeout_seconds"], 30)
                self.assertNotIn("output", audit)

        asyncio.run(exercise())

    def test_distiller_command_is_fresh_ephemeral_and_no_tools(self) -> None:
        command = build_distiller_command()
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn(CODEX_MODEL_ID, command)
        self.assertEqual(command[-1], "-")
        serialized = " ".join(command)
        self.assertNotIn("auth.json", serialized)
        self.assertNotIn("OPENAI_API_KEY", serialized)

        safe = [
            json.dumps({"type": "thread.started", "thread_id": "distiller-fixture"}),
            json.dumps({"type": "turn.started"}),
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": '{"fixture":true}'},
                }
            ),
            json.dumps({"type": "turn.completed", "usage": {}}),
        ]
        self.assertEqual(validate_no_tools_event_stream(safe), '{"fixture":true}')
        unsafe = safe[:2] + [
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "command_execution", "command": "pwd"},
                }
            ),
            safe[-1],
        ]
        with self.assertRaisesRegex(HostCodexAdapterError, "prohibited tool"):
            validate_no_tools_event_stream(unsafe)
        empty_final = safe[:2] + [
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": ""},
                }
            ),
            safe[-1],
        ]
        with self.assertRaisesRegex(HostCodexAdapterError, "nonempty"):
            validate_no_tools_event_stream(empty_final)

    def test_event_conversion_rejects_non_task_tools(self) -> None:
        safe = [
            json.dumps({"type": "thread.started", "thread_id": "fixture-thread"}),
            json.dumps({"type": "turn.started"}),
            json.dumps(
                {
                    "type": "item.started",
                    "item": {
                        "id": "call-1",
                        "type": "mcp_tool_call",
                        "server": "artifact_memory_task",
                        "tool": "task_shell",
                        "status": "in_progress",
                    },
                }
            ),
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "id": "call-1",
                        "type": "mcp_tool_call",
                        "server": "artifact_memory_task",
                        "tool": "task_shell",
                        "arguments": {"command": "echo fixture"},
                        "status": "completed",
                        "error": None,
                        "result": {"content": [{"type": "text", "text": "bridge_call_id=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\nexit_code=0"}]},
                    },
                }
            ),
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "agent_message", "text": "Finished."},
                }
            ),
            json.dumps(
                {
                    "type": "turn.completed",
                    "usage": {"input_tokens": 10, "output_tokens": 2, "cached_input_tokens": 1},
                }
            ),
        ]
        trajectory = codex_events_to_atif(safe, instruction="Synthetic fixture")
        self.assertEqual(trajectory["schema_version"], "ATIF-v1.7")
        self.assertEqual(trajectory["agent"]["model_name"], CODEX_MODEL_ID)
        self.assertEqual(trajectory["steps"][1]["tool_calls"][0]["function_name"], "artifact_memory_task.task_shell")
        output = "bridge_call_id=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\nexit_code=0"
        audit = json.dumps(
            {
                "bounded_timeout_seconds": 120,
                "bridge_call_id": "a" * 32,
                "command": "echo fixture",
                "exit_code": 0,
                "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
                "requested_timeout_seconds": 120,
                "stderr_chars": 0,
                "stdout_chars": 0,
            }
        )
        self.assertEqual(validate_bridge_audit([audit], trajectory), 1)

        unsafe = safe[:2] + [
            json.dumps(
                {
                    "type": "item.completed",
                    "item": {"type": "command_execution", "command": "pwd"},
                }
            ),
            safe[-1],
        ]
        with self.assertRaisesRegex(HostCodexAdapterError, "non-task-scoped tool"):
            codex_events_to_atif(unsafe, instruction="Synthetic fixture")
        with self.assertRaisesRegex(HostCodexAdapterError, "lifecycle"):
            codex_events_to_atif(safe[:-1], instruction="Synthetic fixture")
        with self.assertRaisesRegex(HostCodexAdapterError, "repeated a started"):
            codex_events_to_atif(
                safe[:3] + [safe[2]] + safe[3:], instruction="Synthetic fixture"
            )
        trailing_reasoning = json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "reasoning", "text": "late reasoning"},
            }
        )
        with self.assertRaisesRegex(HostCodexAdapterError, "final completed item"):
            codex_events_to_atif(
                safe[:-1] + [trailing_reasoning, safe[-1]],
                instruction="Synthetic fixture",
            )


if __name__ == "__main__":
    unittest.main()
