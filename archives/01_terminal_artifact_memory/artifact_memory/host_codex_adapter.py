"""Narrow host-side Codex subscription boundary for public Harbor tasks.

The host Codex process keeps subscription OAuth on the host.  It receives one
public task instruction and one MCP tool whose implementation calls Harbor's
already-isolated task environment.  This module never reads or copies Codex
authentication files and never places credential values in commands, manifests,
or logs.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import hmac
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping, Sequence

CODEX_VERSION = "0.146.0"
CODEX_MODEL_ID = "gpt-5.6-sol"
ADAPTER_ID = "host-codex-subscription-task-mcp-v1"
ATIF_SCHEMA_VERSION = "ATIF-v1.7"
MCP_SERVER_NAME = "artifact_memory_task"
MCP_TOOL_NAME = "task_shell"
MAX_TOOL_OUTPUT_CHARS = 50_000
MAX_TASK_COMMAND_CHARS = 100_000
DEFAULT_MAX_TOOL_TIMEOUT_SECONDS = 900
ADAPTER_TASK_TOOL_PROMPT = """# Host adapter tool boundary

Use only `artifact_memory_task.task_shell` for all task inspection and changes. It runs inside the isolated public benchmark task with working directory `/app`. Do not use host shell, apply-patch, file-edit, browser, web-search, or any other tool. Finish after making the task state ready for its executable verifier; never claim verifier passage.
"""

SENSITIVE_ENV_NAME_PATTERN = re.compile(
    r"(?:^|_)(?:ACCESS_?KEY(?:_ID)?|API_?KEY|AUTH|BEARER|CONNECTION_?STRING|"
    r"CREDENTIALS?|DATABASE_?URL|DSN|PASSWORD|PRIVATE_?KEY|SECRET|TOKEN)(?:_|$)",
    re.IGNORECASE,
)
CREDENTIAL_MATERIAL_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{20,}", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"\b(?:gh[opurs]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(
        r'"(?:access_token|refresh_token|id_token|api_key|client_secret|private_key)"\s*:',
        re.IGNORECASE,
    ),
    re.compile(
        r"\b[A-Z0-9_]*(?:API_?KEY|AUTH|CREDENTIAL|PASSWORD|SECRET|TOKEN)[A-Z0-9_]*\s*=\s*\S+",
        re.IGNORECASE,
    ),
)
SAFE_IDENTIFIER_RE = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")


class HostCodexAdapterError(RuntimeError):
    """Raised when the approved adapter boundary cannot be established."""


@dataclass(frozen=True)
class HostCodexPreflight:
    adapter_id: str
    codex_version: str
    model_id: str
    login_method: str
    task_environment: str
    credential_material_forwarded: bool


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
TaskExecutor = Callable[[str, int], Awaitable[tuple[int, str, str]]]


def _run_text(argv: Sequence[str], runner: CommandRunner = subprocess.run) -> str:
    completed = runner(
        list(argv),
        capture_output=True,
        text=True,
        check=False,
        env=_minimal_host_environment(),
    )
    if completed.returncode != 0:
        raise HostCodexAdapterError(f"host command failed during adapter preflight: {argv[0]}")
    return (completed.stdout + "\n" + completed.stderr).strip()


def _minimal_host_environment() -> dict[str, str]:
    """Return only process settings needed by the host Codex executable.

    HOME remains available so Codex itself can use the existing subscription.
    No credential value is resolved, copied, or renamed by this adapter.
    """

    allowed = ("HOME", "PATH", "TMPDIR", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR")
    return {name: os.environ[name] for name in allowed if os.environ.get(name)}


def validate_host_codex(
    model_id: str,
    *,
    runner: CommandRunner = subprocess.run,
) -> HostCodexPreflight:
    if model_id != CODEX_MODEL_ID:
        raise HostCodexAdapterError(f"model must be exactly {CODEX_MODEL_ID}")

    version_output = _run_text(("codex", "--version"), runner)
    if version_output != f"codex-cli {CODEX_VERSION}":
        raise HostCodexAdapterError(f"Codex CLI must be exactly {CODEX_VERSION}")

    login_output = _run_text(("codex", "login", "status"), runner)
    if login_output != "Logged in using ChatGPT":
        raise HostCodexAdapterError("host Codex must use the existing ChatGPT subscription")

    catalog_output = _run_text(("codex", "debug", "models"), runner)
    try:
        catalog = json.loads(catalog_output)
    except json.JSONDecodeError as exc:
        raise HostCodexAdapterError("Codex model catalog was not valid JSON") from exc
    models = catalog if isinstance(catalog, list) else catalog.get("models", [])
    exact = [item for item in models if isinstance(item, Mapping) and item.get("slug") == model_id]
    if len(exact) != 1:
        raise HostCodexAdapterError("exactly one pinned Codex model catalog entry is required")

    return HostCodexPreflight(
        adapter_id=ADAPTER_ID,
        codex_version=CODEX_VERSION,
        model_id=model_id,
        login_method="existing-chatgpt-subscription",
        task_environment="docker",
        credential_material_forwarded=False,
    )


def contains_credential_material(text: str) -> bool:
    return any(pattern.search(text) for pattern in CREDENTIAL_MATERIAL_PATTERNS)


def sensitive_environment_names(names: Sequence[str]) -> list[str]:
    return sorted(name for name in names if SENSITIVE_ENV_NAME_PATTERN.search(name))


def _open_private_parent(path: Path) -> int:
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise HostCodexAdapterError("private provenance path must be an absolute file path")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open("/", directory_flags)
    try:
        parts = path.parent.parts[1:]
        for index, part in enumerate(parts):
            try:
                child = os.open(
                    part,
                    directory_flags | nofollow,
                    dir_fd=descriptor,
                )
            except FileNotFoundError:
                os.mkdir(part, mode=0o700, dir_fd=descriptor)
                child = os.open(
                    part,
                    directory_flags | nofollow,
                    dir_fd=descriptor,
                )
            os.close(descriptor)
            descriptor = child
            if index == len(parts) - 1:
                metadata = os.fstat(descriptor)
                if metadata.st_uid != os.getuid():
                    raise HostCodexAdapterError(
                        "private provenance parent must be owned by the current user"
                    )
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _open_private_file(path: Path, flags: int) -> int:
    parent_descriptor = _open_private_parent(path)
    try:
        try:
            existing = os.stat(
                path.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            existing = None
        if existing is not None and (
            not stat.S_ISREG(existing.st_mode)
            or existing.st_uid != os.getuid()
            or existing.st_nlink != 1
        ):
            raise HostCodexAdapterError(
                "private provenance path is not a sole-owned regular file"
            )
        nofollow = getattr(os, "O_NOFOLLOW", 0)
        create_flags = os.O_CREAT | (os.O_EXCL if existing is None else 0)
        descriptor = os.open(
            path.name,
            flags | create_flags | os.O_CLOEXEC | nofollow,
            0o600,
            dir_fd=parent_descriptor,
        )
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_nlink != 1
            or (
                existing is not None
                and (metadata.st_dev, metadata.st_ino)
                != (existing.st_dev, existing.st_ino)
            )
        ):
            os.close(descriptor)
            raise HostCodexAdapterError(
                "opened provenance path failed regular-file validation"
            )
        os.fchmod(descriptor, 0o600)
        return descriptor
    finally:
        os.close(parent_descriptor)


def _fsync_private_parent(path: Path) -> None:
    descriptor = _open_private_parent(path)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_private_text(path: Path, text: str) -> None:
    descriptor = _open_private_file(path, os.O_WRONLY | os.O_TRUNC)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_private_parent(path)


def append_private_text(path: Path, text: str) -> None:
    descriptor = _open_private_file(path, os.O_WRONLY | os.O_APPEND)
    with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    _fsync_private_parent(path)


def validate_bridge_audit(
    audit_lines: Sequence[str],
    trajectory: Mapping[str, object],
) -> int:
    audited: list[Mapping[str, object]] = []
    for line in audit_lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HostCodexAdapterError("bridge audit contains invalid JSON") from exc
        if not isinstance(record, Mapping) or set(record) != {
            "bounded_timeout_seconds",
            "bridge_call_id",
            "command",
            "exit_code",
            "output_sha256",
            "requested_timeout_seconds",
            "stderr_chars",
            "stdout_chars",
        }:
            raise HostCodexAdapterError("bridge audit record fields differ from the contract")
        audited.append(record)

    observed: list[tuple[Mapping[str, object], str]] = []
    steps = trajectory.get("steps")
    if not isinstance(steps, list):
        raise HostCodexAdapterError("ATIF steps are unavailable for audit matching")
    for step in steps:
        if not isinstance(step, Mapping) or not step.get("tool_calls"):
            continue
        calls = step.get("tool_calls")
        observation = step.get("observation")
        if not isinstance(calls, list) or len(calls) != 1 or not isinstance(observation, Mapping):
            raise HostCodexAdapterError("ATIF task-tool step shape differs from the contract")
        call = calls[0]
        results = observation.get("results")
        if not isinstance(call, Mapping) or not isinstance(results, list) or len(results) != 1:
            raise HostCodexAdapterError("ATIF task-tool observation shape differs from the contract")
        result = results[0]
        if (
            call.get("function_name") != f"{MCP_SERVER_NAME}.{MCP_TOOL_NAME}"
            or not isinstance(result, Mapping)
            or result.get("source_call_id") != call.get("tool_call_id")
            or not isinstance(result.get("content"), str)
        ):
            raise HostCodexAdapterError("ATIF task-tool identity differs from the audit contract")
        observed.append((call, str(result["content"])))

    if not observed or len(observed) != len(audited):
        raise HostCodexAdapterError("authenticated audit and ATIF tool-call counts differ")
    for record, (call, output) in zip(audited, observed, strict=True):
        arguments = call.get("arguments")
        if not isinstance(arguments, Mapping) or set(arguments) not in (
            {"command"},
            {"command", "timeout_seconds"},
        ):
            raise HostCodexAdapterError("ATIF task-tool arguments differ from the MCP schema")
        requested_timeout = arguments.get("timeout_seconds", 120)
        command = arguments.get("command")
        if type(requested_timeout) is not int or not isinstance(command, str):
            raise HostCodexAdapterError("ATIF task-tool arguments have invalid types")
        output_identity = re.match(
            r"^bridge_call_id=([0-9a-f]{32})\nexit_code=(-?\d+)(?:\n|$)",
            output,
        )
        if (
            record.get("command") != command
            or record.get("requested_timeout_seconds") != requested_timeout
            or record.get("bounded_timeout_seconds")
            != min(requested_timeout, DEFAULT_MAX_TOOL_TIMEOUT_SECONDS)
            or output_identity is None
            or record.get("bridge_call_id") != output_identity.group(1)
            or record.get("exit_code") != int(output_identity.group(2))
            or record.get("output_sha256")
            != hashlib.sha256(output.encode("utf-8")).hexdigest()
        ):
            raise HostCodexAdapterError("ordered bridge audit content differs from ATIF")
    return len(observed)


def validate_task_command(command: str) -> None:
    """Apply only bounded-input checks; filesystem isolation is structural.

    Command-text matching is intentionally not the filesystem boundary. The
    Harbor wrapper executes every accepted command in a zero-mount snapshot.
    """

    if not isinstance(command, str) or not command.strip():
        raise HostCodexAdapterError("task_shell requires a non-empty command")
    if "\x00" in command or len(command) > MAX_TASK_COMMAND_CHARS:
        raise HostCodexAdapterError("task_shell command exceeds the bounded input contract")


def render_task_output(exit_code: int, stdout: str, stderr: str) -> str:
    sections = [f"exit_code={exit_code}"]
    if stdout:
        sections.append("stdout:\n" + stdout)
    if stderr:
        sections.append("stderr:\n" + stderr)
    rendered = "\n".join(sections)
    if len(rendered) > MAX_TOOL_OUTPUT_CHARS:
        rendered = rendered[:MAX_TOOL_OUTPUT_CHARS] + "\n[task output truncated by adapter]"
    return rendered


class TaskBridgeServer:
    """Private Unix-socket bridge from one MCP tool to one Harbor environment."""

    def __init__(
        self,
        socket_path: Path | None,
        executor: TaskExecutor,
        audit_path: Path,
        *,
        max_timeout_seconds: int = DEFAULT_MAX_TOOL_TIMEOUT_SECONDS,
        tcp_loopback: bool = False,
    ) -> None:
        self.socket_path = socket_path
        self.executor = executor
        self.audit_path = audit_path
        self.max_timeout_seconds = max_timeout_seconds
        self.tcp_loopback = tcp_loopback
        self.endpoint = ""
        self.auth_token = secrets.token_urlsafe(32)
        self._server: asyncio.AbstractServer | None = None

    async def __aenter__(self) -> "TaskBridgeServer":
        write_private_text(self.audit_path, "")
        if self.tcp_loopback:
            self._server = await asyncio.start_server(self._handle, host="127.0.0.1", port=0)
            address = self._server.sockets[0].getsockname()
            self.endpoint = f"tcp://127.0.0.1:{address[1]}"
        else:
            if self.socket_path is None:
                raise HostCodexAdapterError("Unix task bridge requires a socket path")
            self.socket_path.unlink(missing_ok=True)
            self.socket_path.parent.mkdir(parents=True, exist_ok=True)
            self._server = await asyncio.start_unix_server(self._handle, path=str(self.socket_path))
            os.chmod(self.socket_path, 0o600)
            self.endpoint = f"unix://{self.socket_path}"
        return self

    async def __aexit__(self, *_args: object) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
        if self.socket_path is not None:
            self.socket_path.unlink(missing_ok=True)

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        response: dict[str, object]
        try:
            raw = await asyncio.wait_for(reader.readline(), timeout=5)
            request = json.loads(raw)
            if not isinstance(request, dict) or set(request) != {
                "auth_token",
                "bridge_call_id",
                "command",
                "timeout_seconds",
            }:
                raise HostCodexAdapterError("task bridge request fields do not match the contract")
            supplied_token = request["auth_token"]
            if not isinstance(supplied_token, str) or not hmac.compare_digest(
                supplied_token, self.auth_token
            ):
                raise HostCodexAdapterError("task bridge authentication failed")
            bridge_call_id = request["bridge_call_id"]
            if (
                not isinstance(bridge_call_id, str)
                or not re.fullmatch(r"[0-9a-f]{32}", bridge_call_id)
            ):
                raise HostCodexAdapterError("task bridge call ID is invalid")
            command = request["command"]
            timeout = request["timeout_seconds"]
            validate_task_command(command)
            if contains_credential_material(command):
                raise HostCodexAdapterError("task command cannot be persisted safely")
            if type(timeout) is not int or timeout < 1:
                raise HostCodexAdapterError("task bridge timeout must be a positive integer")
            bounded_timeout = min(timeout, self.max_timeout_seconds)
            exit_code, stdout, stderr = await self.executor(command, bounded_timeout)
            if contains_credential_material(stdout + "\n" + stderr):
                raise HostCodexAdapterError("task output cannot enter persistent model events")
            rendered_output = (
                f"bridge_call_id={bridge_call_id}\n"
                + render_task_output(exit_code, stdout, stderr)
            )
            response = {
                "ok": True,
                "exit_code": exit_code,
                "output": rendered_output,
            }
            audit = {
                "command": command,
                "requested_timeout_seconds": timeout,
                "bounded_timeout_seconds": bounded_timeout,
                "bridge_call_id": bridge_call_id,
                "exit_code": exit_code,
                "output_sha256": hashlib.sha256(rendered_output.encode("utf-8")).hexdigest(),
                "stdout_chars": len(stdout),
                "stderr_chars": len(stderr),
            }
            append_private_text(
                self.audit_path, json.dumps(audit, sort_keys=True) + "\n"
            )
        except Exception as exc:  # The MCP caller receives only a bounded class message.
            response = {"ok": False, "error": f"{type(exc).__name__}: task bridge rejected request"}
        writer.write((json.dumps(response, sort_keys=True) + "\n").encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()


def _mcp_response(request_id: object, result: object) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _proxy_bridge_call(
    endpoint: str,
    auth_token: str,
    bridge_call_id: str,
    command: str,
    timeout_seconds: int,
) -> dict[str, object]:
    async def call() -> dict[str, object]:
        if endpoint.startswith("unix://"):
            reader, writer = await asyncio.open_unix_connection(endpoint.removeprefix("unix://"))
        elif endpoint.startswith("tcp://127.0.0.1:"):
            port = int(endpoint.rsplit(":", 1)[1])
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
        else:
            raise HostCodexAdapterError("task bridge endpoint must be private Unix or loopback TCP")
        writer.write(
            (
                json.dumps(
                    {
                        "auth_token": auth_token,
                        "bridge_call_id": bridge_call_id,
                        "command": command,
                        "timeout_seconds": timeout_seconds,
                    },
                    sort_keys=True
                )
                + "\n"
            ).encode()
        )
        await writer.drain()
        raw = await reader.readline()
        writer.close()
        await writer.wait_closed()
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise HostCodexAdapterError("task bridge response must be an object")
        return value

    return asyncio.run(call())


def run_mcp_proxy(endpoint: str) -> int:
    """Serve the one-tool MCP protocol over JSONL stdio."""

    auth_token = os.environ.pop("ARTIFACT_MEMORY_BRIDGE_TOKEN", "")
    if not auth_token:
        raise HostCodexAdapterError("task bridge capability is absent")
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                continue
            method = request.get("method")
            request_id = request.get("id")
            if method == "initialize":
                response = _mcp_response(
                    request_id,
                    {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": MCP_SERVER_NAME, "version": "1.0.0"},
                    },
                )
            elif method == "tools/list":
                response = _mcp_response(
                    request_id,
                    {
                        "tools": [
                            {
                                "name": MCP_TOOL_NAME,
                                "description": (
                                    "Run one shell command only inside the isolated public benchmark "
                                    "task container. The working directory is /app."
                                ),
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "command": {"type": "string"},
                                        "timeout_seconds": {
                                            "type": "integer",
                                            "minimum": 1,
                                            "maximum": DEFAULT_MAX_TOOL_TIMEOUT_SECONDS,
                                            "default": 120,
                                        },
                                    },
                                    "required": ["command"],
                                    "additionalProperties": False,
                                },
                            }
                        ]
                    },
                )
            elif method == "tools/call":
                params = request.get("params") or {}
                arguments = params.get("arguments") or {}
                if params.get("name") != MCP_TOOL_NAME or not isinstance(arguments, dict):
                    raise HostCodexAdapterError("unknown MCP tool")
                command = arguments.get("command")
                timeout = arguments.get("timeout_seconds", 120)
                validate_task_command(command)
                if type(timeout) is not int:
                    raise HostCodexAdapterError("timeout_seconds must be an integer")
                bridge_call_id = secrets.token_hex(16)
                bridge = _proxy_bridge_call(
                    endpoint, auth_token, bridge_call_id, command, timeout
                )
                text = str(bridge.get("output") or bridge.get("error") or "task bridge failed")
                response = _mcp_response(
                    request_id,
                    {"content": [{"type": "text", "text": text}], "isError": bridge.get("ok") is not True},
                )
            else:
                if request_id is None:  # Notification, including notifications/initialized.
                    continue
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": "method not supported"},
                }
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
        except Exception as exc:
            request_id = request.get("id") if isinstance(request, dict) else None
            if request_id is not None:
                sys.stdout.write(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {"code": -32000, "message": f"{type(exc).__name__}: rejected"},
                        },
                        separators=(",", ":"),
                    )
                    + "\n"
                )
                sys.stdout.flush()
    return 0


def render_adapter_instruction(instruction: str) -> str:
    return ADAPTER_TASK_TOOL_PROMPT.rstrip() + "\n\n" + instruction.strip() + "\n"


def build_codex_command(
    *,
    instruction: str,
    endpoint: str,
    python_executable: str,
    module_root: Path,
) -> list[str]:
    proxy_args = [
        "-m",
        "artifact_memory.host_codex_adapter",
        "mcp-proxy",
        "--endpoint",
        endpoint,
    ]
    return [
        "codex",
        "--ask-for-approval",
        "never",
        "--sandbox",
        "read-only",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--strict-config",
        "--model",
        CODEX_MODEL_ID,
        "--json",
        "--disable",
        "shell_tool",
        "--disable",
        "unified_exec",
        "--disable",
        "apps",
        "--disable",
        "browser_use",
        "--disable",
        "computer_use",
        "--disable",
        "image_generation",
        "-c",
        'web_search="disabled"',
        "-c",
        'approval_policy="never"',
        "-c",
        f'mcp_servers.{MCP_SERVER_NAME}.command={json.dumps(python_executable)}',
        "-c",
        f'mcp_servers.{MCP_SERVER_NAME}.args={json.dumps(proxy_args, separators=(",", ":"))}',
        "-c",
        f'mcp_servers.{MCP_SERVER_NAME}.env.PYTHONPATH={json.dumps(str(module_root))}',
        "-c",
        f'mcp_servers.{MCP_SERVER_NAME}.env_vars=["ARTIFACT_MEMORY_BRIDGE_TOKEN"]',
        "-c",
        f'mcp_servers.{MCP_SERVER_NAME}.required=true',
        "-c",
        f'mcp_servers.{MCP_SERVER_NAME}.enabled_tools=[{json.dumps(MCP_TOOL_NAME)}]',
        "-c",
        f'mcp_servers.{MCP_SERVER_NAME}.default_tools_approval_mode="approve"',
        "-c",
        f'mcp_servers.{MCP_SERVER_NAME}.tool_timeout_sec={DEFAULT_MAX_TOOL_TIMEOUT_SECONDS}',
        "-C",
        "/",
        "--",
        render_adapter_instruction(instruction),
    ]


def _item_text(item: Mapping[str, object]) -> str:
    error = item.get("error")
    if isinstance(error, Mapping) and isinstance(error.get("message"), str):
        return str(error["message"])
    for field in ("text", "output", "result"):
        value = item.get(field)
        if isinstance(value, str):
            return value
        if isinstance(value, Mapping):
            content = value.get("content")
            if isinstance(content, list):
                parts = [str(block.get("text")) for block in content if isinstance(block, Mapping) and block.get("text")]
                if parts:
                    return "\n".join(parts)
    return ""


def codex_events_to_atif(
    event_lines: Sequence[str],
    *,
    instruction: str,
) -> dict[str, object]:
    events: list[Mapping[str, object]] = []
    for line in event_lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HostCodexAdapterError("Codex JSON event stream contained invalid JSON") from exc
        if not isinstance(value, Mapping):
            raise HostCodexAdapterError("Codex JSON event must be an object")
        events.append(value)
    event_types = [str(event.get("type") or "") for event in events]
    permitted_event_types = {
        "thread.started",
        "turn.started",
        "item.started",
        "item.completed",
        "turn.completed",
    }
    if any(event_type not in permitted_event_types for event_type in event_types):
        raise HostCodexAdapterError("Codex event stream contains an unsupported lifecycle event")
    if (
        event_types.count("thread.started") != 1
        or event_types.count("turn.started") != 1
        or event_types.count("turn.completed") != 1
        or event_types[0] != "thread.started"
        or event_types[1] != "turn.started"
        or event_types[-1] != "turn.completed"
    ):
        raise HostCodexAdapterError("Codex event lifecycle is incomplete or ambiguous")
    thread = events[0]
    thread_id = thread.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id.strip():
        raise HostCodexAdapterError("Codex thread.started must contain a real thread ID")
    session_id = thread_id

    started_tool_ids: list[str] = []
    started_tool_positions: dict[str, int] = {}
    for event_position, event in enumerate(events):
        if event.get("type") != "item.started":
            continue
        item = event.get("item")
        if not isinstance(item, Mapping):
            raise HostCodexAdapterError("Codex item.started must contain an item")
        server = item.get("server") or item.get("server_name")
        tool = item.get("tool") or item.get("tool_name") or item.get("name")
        if (
            item.get("type") != "mcp_tool_call"
            or f"{server}.{tool}" != f"{MCP_SERVER_NAME}.{MCP_TOOL_NAME}"
            or item.get("status") != "in_progress"
            or not isinstance(item.get("id"), str)
        ):
            raise HostCodexAdapterError("Codex started an unqualified or unsupported item")
        started_id = str(item["id"])
        if started_id in started_tool_ids:
            raise HostCodexAdapterError("Codex repeated a started task-tool call ID")
        started_tool_ids.append(started_id)
        started_tool_positions[started_id] = event_position
    steps: list[dict[str, object]] = [
        {
            "step_id": 1,
            "source": "user",
            "message": instruction,
        }
    ]
    allowed_tool_name = f"{MCP_SERVER_NAME}.{MCP_TOOL_NAME}"
    forbidden_items: list[str] = []
    completed_tool_ids: list[str] = []
    completed_item_types: list[str] = []
    final_completed_agent_text = ""
    for event_position, event in enumerate(events):
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, Mapping):
            continue
        item_type = str(item.get("type") or "")
        if item_type:
            completed_item_types.append(item_type)
        if item_type in {"agent_message", "reasoning"}:
            text = _item_text(item)
            if item_type == "agent_message":
                final_completed_agent_text = text
            if text:
                steps.append(
                    {
                        "step_id": len(steps) + 1,
                        "source": "agent",
                        "message": text,
                        "model_name": CODEX_MODEL_ID,
                        "llm_call_count": 1,
                    }
                )
            continue
        if item_type in {"mcp_tool_call", "tool_call"}:
            server = item.get("server") or item.get("server_name")
            tool = item.get("tool") or item.get("tool_name") or item.get("name")
            qualified = f"{server}.{tool}" if server and tool else str(tool or "")
            if qualified != allowed_tool_name:
                forbidden_items.append(qualified or item_type)
                continue
            if (
                item.get("status") != "completed"
                or item.get("error") is not None
                or not isinstance(item.get("result"), Mapping)
                or not isinstance(item.get("id"), str)
            ):
                forbidden_items.append("unsuccessful_task_tool_call")
                continue
            completed_id = str(item["id"])
            if (
                completed_id not in started_tool_positions
                or started_tool_positions[completed_id] >= event_position
            ):
                forbidden_items.append("task_tool_completed_before_matching_start")
                continue
            if completed_id in completed_tool_ids:
                forbidden_items.append("duplicate_completed_task_tool_call_id")
                continue
            completed_tool_ids.append(completed_id)
            arguments = item.get("arguments") or item.get("input") or {}
            if not isinstance(arguments, Mapping):
                arguments = {"value": arguments}
            call_id = str(item.get("id") or f"tool-{len(steps) + 1}")
            steps.append(
                {
                    "step_id": len(steps) + 1,
                    "source": "agent",
                    "message": "",
                    "model_name": CODEX_MODEL_ID,
                    "llm_call_count": 1,
                    "tool_calls": [
                        {
                            "tool_call_id": call_id,
                            "function_name": allowed_tool_name,
                            "arguments": dict(arguments),
                        }
                    ],
                    "observation": {
                        "results": [
                            {"source_call_id": call_id, "content": _item_text(item)}
                        ]
                    },
                }
            )
            continue
        if item_type:
            forbidden_items.append(item_type)
    if forbidden_items:
        raise HostCodexAdapterError(
            "Codex attempted a non-task-scoped tool or unsupported event: "
            + ", ".join(sorted(set(forbidden_items)))
        )
    if not completed_tool_ids or started_tool_ids != completed_tool_ids:
        raise HostCodexAdapterError(
            "Codex trajectory requires ordered one-to-one task-tool lifecycle pairs"
        )
    if (
        not completed_item_types
        or completed_item_types[-1] != "agent_message"
        or not final_completed_agent_text.strip()
    ):
        raise HostCodexAdapterError(
            "Codex final completed item must be a nonempty agent message"
        )

    completed = events[-1]
    usage = completed.get("usage") if isinstance(completed, Mapping) else None
    usage = usage if isinstance(usage, Mapping) else {}
    return {
        "schema_version": ATIF_SCHEMA_VERSION,
        "session_id": session_id,
        "agent": {
            "name": ADAPTER_ID,
            "version": CODEX_VERSION,
            "model_name": CODEX_MODEL_ID,
        },
        "steps": steps,
        "final_metrics": {
            "total_prompt_tokens": usage.get("input_tokens"),
            "total_completion_tokens": usage.get("output_tokens"),
            "total_cached_tokens": usage.get("cached_input_tokens"),
            "total_steps": len(steps),
            "extra": {
                "credential_material_forwarded": False,
                "task_tool": allowed_tool_name,
                "task_tool_call_count": len(completed_tool_ids),
            },
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Host Codex task MCP helper.")
    sub = parser.add_subparsers(dest="command", required=True)
    proxy = sub.add_parser("mcp-proxy")
    proxy.add_argument("--endpoint", required=True)
    args = parser.parse_args(argv)
    if args.command == "mcp-proxy":
        return run_mcp_proxy(args.endpoint)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
