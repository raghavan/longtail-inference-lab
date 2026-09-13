"""Harbor 0.20.0 entry point for the approved host-side Codex adapter.

This class is intentionally specific to Docker-backed public benchmark tasks.
Codex remains on the host with its existing subscription.  The only model tool
is the Unix-socket MCP bridge in :mod:`artifact_memory.host_codex_adapter`.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import uuid
from pathlib import Path
from typing import Any

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from .execution_ledger import reserve_attempt
from .preregistration import (
    DEVELOPMENT_TEACHER_TASK_IDS,
    PreregistrationError,
    teacher_environment_names,
    validate_teacher_execution_authorization,
)
from .host_codex_adapter import (
    ADAPTER_ID,
    CODEX_MODEL_ID,
    CODEX_VERSION,
    HostCodexAdapterError,
    TaskBridgeServer,
    _minimal_host_environment,
    build_codex_command,
    codex_events_to_atif,
    contains_credential_material,
    render_adapter_instruction,
    sensitive_environment_names,
    validate_bridge_audit,
    validate_host_codex,
    write_private_text,
)


ALLOWED_TASK_MOUNT_TARGETS = {
    "/logs/agent",
    "/logs/artifacts",
    "/logs/verifier",
}
MAX_STAGED_APP_ENTRIES = 500_000
MAX_STAGED_APP_BYTES = 10 * 1024 * 1024 * 1024
CONTAINER_ID_RE = re.compile(r"[0-9a-f]{12,64}")
QUIESCENT_PROCESS_INVENTORIES = {
    (
        ("sh", "sh -c sleep infinity"),
        ("sleep", "sleep infinity"),
    ),
    (
        (
            "sh",
            "/run/rosetta/rosetta /usr/bin/sh sh -c sleep infinity",
        ),
    ),
}


class HostCodexTeacherAgent(BaseAgent):
    """One fresh host Codex session for one isolated public Harbor task."""

    SUPPORTS_ATIF = True
    SUPPORTS_RESUME = False

    def __init__(
        self,
        *args: object,
        execution_mode: str | None = None,
        task_id: str | None = None,
        authorization_path: str | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.execution_mode = execution_mode
        self.task_id = task_id
        self.authorization_path = authorization_path

    @staticmethod
    def name() -> str:
        return ADAPTER_ID

    def version(self) -> str:
        return CODEX_VERSION

    def _validate_execution_gate(self) -> dict[str, object]:
        if not self.task_id:
            raise HostCodexAdapterError("adapter task_id is required")
        if self.execution_mode == "development":
            if self.task_id not in DEVELOPMENT_TEACHER_TASK_IDS:
                raise HostCodexAdapterError("development adapter is restricted to frozen development tasks")
            if self.authorization_path:
                raise HostCodexAdapterError("development adapter must not receive measured authorization")
            return {"execution_mode": "development", "task_id": self.task_id}
        if self.execution_mode == "measured":
            if not self.authorization_path:
                raise HostCodexAdapterError("measured adapter requires a private authorization record")
            try:
                authorization = validate_teacher_execution_authorization(
                    Path(self.authorization_path), task_id=self.task_id
                )
            except PreregistrationError as exc:
                raise HostCodexAdapterError(str(exc)) from exc
            return {"execution_mode": "measured", **authorization}
        raise HostCodexAdapterError("adapter execution_mode must be development or measured")

    @staticmethod
    async def _host_docker_output(
        *arguments: str,
        timeout_seconds: int = 20,
    ) -> str:
        process = await asyncio.create_subprocess_exec(
            "docker",
            *arguments,
            env=_minimal_host_environment(),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout_seconds
        )
        if process.returncode != 0:
            raise HostCodexAdapterError("Docker identity inspection failed closed")
        return stdout.decode("utf-8", errors="strict").strip()

    async def _active_container_id(self, environment: BaseEnvironment) -> str:
        compose = getattr(environment, "_run_docker_compose_command", None)
        if not callable(compose):
            raise HostCodexAdapterError("pinned Harbor Docker identity API is unavailable")
        result = await compose(["ps", "-q", "main"], check=False, timeout_sec=15)
        container_id = (result.stdout or "").strip()
        if result.return_code != 0 or not CONTAINER_ID_RE.fullmatch(container_id):
            raise HostCodexAdapterError("exactly one active Harbor main container is required")
        return container_id

    async def _validate_active_container(
        self,
        environment: BaseEnvironment,
        execution_gate: dict[str, object],
    ) -> str:
        task_config = getattr(environment, "task_env_config", None)
        configured_image = getattr(task_config, "docker_image", None)
        expected_digest = execution_gate.get("task_container_digest")
        if expected_digest and (
            not isinstance(configured_image, str)
            or not configured_image.endswith("@" + str(expected_digest))
        ):
            raise HostCodexAdapterError("configured task image differs from measured authorization")

        container_id = await self._active_container_id(environment)
        template = (
            "{{println .Image}}{{println .Config.Image}}"
            "{{range .Config.Env}}{{println (index (split . \"=\") 0)}}{{end}}"
            "{{println \"--MOUNTS--\"}}{{json .Mounts}}"
        )
        inspection = await self._host_docker_output(
            "container", "inspect", "--format", template, container_id
        )
        lines = inspection.splitlines()
        if len(lines) < 3 or "--MOUNTS--" not in lines:
            raise HostCodexAdapterError("active container inspection contract mismatch")
        active_image_id, active_configured_image = lines[0], lines[1]
        marker = lines.index("--MOUNTS--")
        environment_names = [name for name in lines[2:marker] if name]
        try:
            mounts = json.loads("\n".join(lines[marker + 1 :]))
        except json.JSONDecodeError as exc:
            raise HostCodexAdapterError("active container mount inventory was not JSON") from exc
        if not isinstance(mounts, list):
            raise HostCodexAdapterError("active container mount inventory must be a list")
        observed_mounts: dict[str, Path] = {}
        for mount in mounts:
            if (
                not isinstance(mount, dict)
                or mount.get("Type") != "bind"
                or mount.get("RW") is not True
                or not isinstance(mount.get("Destination"), str)
                or not isinstance(mount.get("Source"), str)
            ):
                raise HostCodexAdapterError("task container mount is not a writable Harbor bind")
            observed_mounts[str(mount["Destination"]).rstrip("/")] = Path(
                str(mount["Source"])
            ).resolve()
        expected_mounts = {
            "/logs/agent": self.logs_dir.resolve(),
            "/logs/artifacts": (
                self.logs_dir.parent / "artifacts" / "logs" / "artifacts"
            ).resolve(),
            "/logs/verifier": (self.logs_dir.parent / "verifier").resolve(),
        }
        if observed_mounts != expected_mounts:
            raise HostCodexAdapterError("task container mount sources differ from Harbor trial logs")
        if expected_digest and active_configured_image != configured_image:
            raise HostCodexAdapterError("active container was not created from the configured image")
        resolved_image = str(configured_image if expected_digest else active_configured_image)
        if not resolved_image:
            raise HostCodexAdapterError("Harbor task image identity is unavailable")
        expected_image_id = await self._host_docker_output(
            "image", "inspect", "--format", "{{.Id}}", resolved_image
        )
        if active_image_id != expected_image_id:
            raise HostCodexAdapterError("active container image ID differs from the pinned image")
        sensitive_names = sensitive_environment_names(environment_names)
        if sensitive_names:
            raise HostCodexAdapterError(
                "credential-like environment names reached the task container"
            )
        if self.task_id is None:
            raise HostCodexAdapterError("task ID is unavailable for environment validation")
        try:
            expected_environment_names = teacher_environment_names(self.task_id)
        except PreregistrationError as exc:
            raise HostCodexAdapterError(str(exc)) from exc
        if (
            len(environment_names) != len(set(environment_names))
            or set(environment_names) != expected_environment_names
        ):
            raise HostCodexAdapterError(
                "task container environment names differ from the closed inventory"
            )
        if set(observed_mounts) != ALLOWED_TASK_MOUNT_TARGETS:
            raise HostCodexAdapterError("task container mounts differ from the closed allowlist")
        return container_id

    async def _validate_environment(
        self,
        environment: BaseEnvironment,
        execution_gate: dict[str, object],
    ) -> str:
        if environment.type() != "docker":
            raise HostCodexAdapterError("host Codex adapter requires Harbor Docker isolation")
        return await self._validate_active_container(environment, execution_gate)

    async def _validate_active_process_inventory(self, active_container_id: str) -> None:
        output = await self._host_docker_output(
            "container", "top", active_container_id, "-eo", "pid,comm,args"
        )
        lines = [line for line in output.splitlines() if line.strip()]
        inventory: list[tuple[str, str]] = []
        for line in lines[1:]:
            fields = line.split(None, 2)
            if len(fields) != 3:
                raise HostCodexAdapterError(
                    "verifier-visible process inventory could not be parsed"
                )
            inventory.append((fields[1], fields[2]))
        if tuple(inventory) not in QUIESCENT_PROCESS_INVENTORIES:
            raise HostCodexAdapterError(
                "verifier-visible container has a non-quiescent process inventory"
            )

    async def _create_task_boundary(self, active_container_id: str) -> tuple[str, str]:
        await self._validate_active_process_inventory(active_container_id)
        nonce = uuid.uuid4().hex
        image_name = f"artifact-memory-boundary:{nonce}"
        container_name = f"artifact-memory-boundary-{nonce}"
        snapshot_id = await self._host_docker_output(
            "container", "commit", active_container_id, image_name
        )
        if not snapshot_id.startswith("sha256:"):
            raise HostCodexAdapterError("isolated task snapshot creation failed")
        try:
            created_id = await self._host_docker_output(
                "container",
                "create",
                "--name",
                container_name,
                "--network",
                f"container:{active_container_id}",
                "--entrypoint",
                "/bin/bash",
                image_name,
                "-lc",
                "while :; do sleep 3600; done",
            )
            if not CONTAINER_ID_RE.fullmatch(created_id):
                raise HostCodexAdapterError("isolated task container creation failed")
            await self._host_docker_output("container", "start", created_id)
            boundary = await self._host_docker_output(
                "container",
                "inspect",
                "--format",
                "{{println .Image}}{{println (len .Mounts)}}{{println .HostConfig.Privileged}}",
                created_id,
            )
            if boundary.splitlines() != [snapshot_id, "0", "false"]:
                raise HostCodexAdapterError("isolated task container boundary mismatch")
            absent = await self._host_docker_output(
                "container",
                "exec",
                created_id,
                "/bin/bash",
                "-lc",
                (
                    "test ! -S /var/run/docker.sock && "
                    "test ! -e /tests && test ! -e /solution && test ! -e /verifier && "
                    "test ! -e /root/.codex && "
                    "test -z \"$(find /logs/verifier -mindepth 1 -print -quit 2>/dev/null)\""
                ),
            )
            if absent:
                raise HostCodexAdapterError("isolated task container preflight emitted output")
            return created_id, image_name
        except Exception:
            await self._cleanup_task_boundary(container_name, image_name)
            raise

    async def _cleanup_task_boundary(self, container: str, image: str) -> None:
        for arguments in (
            ("container", "rm", "--force", container),
            ("image", "rm", "--force", image),
        ):
            try:
                await self._host_docker_output(*arguments)
            except Exception:
                pass

    async def _execute_in_task_boundary(
        self,
        container_id: str,
        command: str,
        timeout_seconds: int,
    ) -> tuple[int, str, str]:
        process = await asyncio.create_subprocess_exec(
            "docker",
            "container",
            "exec",
            "--workdir",
            "/app",
            "--env",
            "HOME=/tmp/artifact-memory-home",
            container_id,
            "/usr/bin/timeout",
            "--signal=KILL",
            str(timeout_seconds),
            "/bin/bash",
            "-lc",
            command,
            env=_minimal_host_environment(),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout_seconds + 10
            )
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.wait()
            raise HostCodexAdapterError("isolated task command exceeded its hard timeout") from exc
        return (
            process.returncode or 0,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )

    @staticmethod
    def _validate_staged_app(root: Path) -> None:
        if not root.is_dir() or root.is_symlink():
            raise HostCodexAdapterError("staged task state must be a real /app directory")
        resolved_root = root.resolve()
        entries = 0
        total_bytes = 0
        for current, directories, files in os.walk(root, followlinks=False):
            for name in [*directories, *files]:
                path = Path(current) / name
                metadata = path.lstat()
                entries += 1
                total_bytes += metadata.st_size
                mode = metadata.st_mode
                if stat.S_ISLNK(mode):
                    target = (path.parent / os.readlink(path)).resolve(strict=False)
                    try:
                        target.relative_to(resolved_root)
                    except ValueError as exc:
                        raise HostCodexAdapterError(
                            "staged /app symlink escapes the task-state root"
                        ) from exc
                elif not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                    raise HostCodexAdapterError(
                        "staged /app contains a socket, device, FIFO, or unsupported file"
                    )
                if entries > MAX_STAGED_APP_ENTRIES or total_bytes > MAX_STAGED_APP_BYTES:
                    raise HostCodexAdapterError("staged /app exceeds the bounded state contract")

    async def _sync_task_boundary(self, boundary_id: str, active_id: str) -> None:
        nonce = uuid.uuid4().hex
        # The trial root itself is not mounted; only its agent, verifier, and
        # artifacts descendants are. Staging beside those mounts prevents the
        # active container from racing host-side validation.
        staging_root = self.logs_dir.parent / f".task-state-staging-{nonce}"
        staged_app = staging_root / "app"
        active_staging = f"/artifact-memory-task-state-{nonce}"
        active_previous = f"/app.artifact-memory-previous-{nonce}"
        staging_root.mkdir(mode=0o700, parents=True)
        staged_app.mkdir(mode=0o700)
        try:
            # Stop first: docker cp can read a stopped container, so no process
            # can mutate /app while the complete candidate state is staged.
            await self._host_docker_output(
                "container", "stop", "--time", "10", boundary_id, timeout_seconds=30
            )
            await self._host_docker_output(
                "container",
                "cp",
                f"{boundary_id}:/app/.",
                str(staged_app),
                timeout_seconds=600,
            )
            self._validate_staged_app(staged_app)
            await self._validate_active_process_inventory(active_id)
            await self._host_docker_output(
                "container", "cp", str(staged_app), f"{active_id}:{active_staging}",
                timeout_seconds=600,
            )
            swap = (
                "set -eu; "
                f"rm -rf {active_previous}; "
                f"mv /app {active_previous}; "
                f"if mv {active_staging} /app; then "
                f"rm -rf {active_previous}; "
                "else "
                "rm -rf /app; "
                f"mv {active_previous} /app; "
                "exit 1; "
                "fi"
            )
            await self._host_docker_output(
                "container", "exec", active_id, "/bin/bash", "-lc", swap,
                timeout_seconds=120,
            )
        finally:
            shutil.rmtree(staging_root, ignore_errors=True)

    async def setup(self, environment: BaseEnvironment) -> None:
        execution_gate = self._validate_execution_gate()
        validate_host_codex(str(self.model_name or ""))
        await self._validate_environment(environment, execution_gate)

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        # Revalidate immediately before every cloud request.  No task command has
        # executed if model, CLI, login mode, or isolation differs from the pin.
        execution_gate = self._validate_execution_gate()
        preflight = validate_host_codex(str(self.model_name or ""))
        active_container_id = await self._validate_environment(environment, execution_gate)
        expected_instruction_hash = execution_gate.get("effective_instruction_sha256")
        if expected_instruction_hash:
            observed_instruction_hash = hashlib.sha256(
                render_adapter_instruction(instruction).encode()
            ).hexdigest()
            if observed_instruction_hash != expected_instruction_hash:
                raise HostCodexAdapterError(
                    "actual model-visible instruction does not match measured authorization"
                )
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        write_private_text(
            self.logs_dir / "adapter-preflight.json",
            json.dumps({**preflight.__dict__, **execution_gate}, indent=2, sort_keys=True)
            + "\n",
        )

        audit_path = self.logs_dir / "task-bridge-audit.jsonl"
        events_path = self.logs_dir / "codex-events.jsonl"
        stderr_path = self.logs_dir / "codex-stderr.txt"
        trajectory_path = self.logs_dir / "trajectory.json"
        module_root = Path(__file__).resolve().parent.parent

        boundary_container_id, boundary_image = await self._create_task_boundary(
            active_container_id
        )
        try:
            if self.execution_mode == "measured":
                reserve_attempt("teacher", str(self.task_id))

            async def task_executor(
                command: str, timeout_seconds: int
            ) -> tuple[int, str, str]:
                return await self._execute_in_task_boundary(
                    boundary_container_id, command, timeout_seconds
                )

            host_env = _minimal_host_environment()
            # The approved private storage prefix exceeds the Unix-domain socket
            # length limit on macOS, so the bridge binds an ephemeral loopback-only
            # TCP port. It never listens on a non-loopback interface.
            async with TaskBridgeServer(
                None, task_executor, audit_path, tcp_loopback=True
            ) as bridge:
                host_env["ARTIFACT_MEMORY_BRIDGE_TOKEN"] = bridge.auth_token
                command = build_codex_command(
                    instruction=instruction,
                    endpoint=bridge.endpoint,
                    python_executable=sys.executable,
                    module_root=module_root,
                )
                process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd="/",
                    env=host_env,
                    stdin=asyncio.subprocess.DEVNULL,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout_bytes, stderr_bytes = await process.communicate()

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            if contains_credential_material(stdout) or contains_credential_material(stderr):
                raise HostCodexAdapterError(
                    "Codex output matched credential-material guards; unsafe bytes were not persisted"
                )
            if process.returncode != 0:
                # Persist only credential-scanned diagnostics in private run storage.
                write_private_text(stderr_path, stderr)
                raise HostCodexAdapterError(f"host Codex exited with code {process.returncode}")
            if any(
                marker in stderr.lower()
                for marker in ("apply_patch", "tools::router", "shell tool")
            ):
                write_private_text(stderr_path, stderr)
                raise HostCodexAdapterError("Codex attempted a disabled host-side tool")

            event_lines = [line for line in stdout.splitlines() if line.strip()]
            trajectory = codex_events_to_atif(
                event_lines, instruction=render_adapter_instruction(instruction)
            )
            metrics = trajectory.get("final_metrics")
            extra = metrics.get("extra") if isinstance(metrics, dict) else None
            tool_call_count = extra.get("task_tool_call_count") if isinstance(extra, dict) else None
            audit_lines = [line for line in audit_path.read_text().splitlines() if line]
            verified_tool_calls = validate_bridge_audit(audit_lines, trajectory)
            if (
                type(tool_call_count) is not int
                or tool_call_count != verified_tool_calls
                or audit_path.stat().st_mode & 0o077
            ):
                raise HostCodexAdapterError(
                    "authenticated bridge audit does not match qualified ATIF tool calls"
                )
            # Persist every required safe provenance artifact before touching
            # verifier-visible state. A write or context-conversion failure thus
            # leaves the active /app unchanged.
            write_private_text(events_path, "\n".join(event_lines) + "\n")
            write_private_text(stderr_path, stderr)
            write_private_text(
                trajectory_path, json.dumps(trajectory, indent=2, sort_keys=True) + "\n"
            )
            if isinstance(metrics, dict):
                context.n_input_tokens = int(metrics.get("total_prompt_tokens") or 0)
                context.n_output_tokens = int(metrics.get("total_completion_tokens") or 0)
                context.n_cache_tokens = int(metrics.get("total_cached_tokens") or 0)
            # This is deliberately the final potentially failing operation in
            # the successful run path.
            await self._sync_task_boundary(boundary_container_id, active_container_id)
        finally:
            await self._cleanup_task_boundary(boundary_container_id, boundary_image)

    def populate_context_post_run(self, context: AgentContext) -> None:
        # Host-side run() writes the final ATIF file directly into the mounted
        # host trial directory.  No credential-bearing session file is copied.
        return None
