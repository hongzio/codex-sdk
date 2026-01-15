from __future__ import annotations

import asyncio
import contextlib
import os
import shutil
from dataclasses import dataclass
from typing import AsyncIterator

from .options import ApprovalMode, ModelReasoningEffort, SandboxMode, WebSearchMode

INTERNAL_ORIGINATOR_ENV = "CODEX_INTERNAL_ORIGINATOR_OVERRIDE"
PYTHON_SDK_ORIGINATOR = "codex_sdk_py"


@dataclass(slots=True)
class CodexExecArgs:
    input_text: str
    base_url: str | None = None
    api_key: str | None = None
    thread_id: str | None = None
    images: list[str] | None = None
    model: str | None = None
    sandbox_mode: SandboxMode | None = None
    working_directory: str | None = None
    additional_directories: list[str] | None = None
    skip_git_repo_check: bool | None = None
    output_schema_file: str | None = None
    model_reasoning_effort: ModelReasoningEffort | None = None
    signal: asyncio.Event | None = None
    network_access_enabled: bool | None = None
    web_search_mode: WebSearchMode | None = None
    web_search_enabled: bool | None = None
    approval_policy: ApprovalMode | None = None


class CodexExec:
    def __init__(
        self, executable_path: str | None = None, env: dict[str, str] | None = None
    ) -> None:
        self._executable_path = executable_path or _find_codex_path()
        self._env_override = env

    async def run(self, args: CodexExecArgs) -> AsyncIterator[str]:
        command_args = ["exec", "--experimental-json"]

        if args.model:
            command_args.extend(["--model", args.model])
        if args.sandbox_mode:
            command_args.extend(["--sandbox", args.sandbox_mode])
        if args.working_directory:
            command_args.extend(["--cd", args.working_directory])
        if args.additional_directories:
            for directory in args.additional_directories:
                command_args.extend(["--add-dir", directory])
        if args.skip_git_repo_check:
            command_args.append("--skip-git-repo-check")
        if args.output_schema_file:
            command_args.extend(["--output-schema", args.output_schema_file])
        if args.model_reasoning_effort:
            command_args.extend(
                ["--config", f'model_reasoning_effort="{args.model_reasoning_effort}"']
            )
        if args.network_access_enabled is not None:
            command_args.extend(
                [
                    "--config",
                    f"sandbox_workspace_write.network_access={args.network_access_enabled}",
                ]
            )
        if args.web_search_mode:
            command_args.extend(["--config", f'web_search="{args.web_search_mode}"'])
        elif args.web_search_enabled is True:
            command_args.extend(["--config", 'web_search="live"'])
        elif args.web_search_enabled is False:
            command_args.extend(["--config", 'web_search="disabled"'])
        if args.approval_policy:
            command_args.extend(
                ["--config", f'approval_policy="{args.approval_policy}"']
            )
        if args.images:
            for image in args.images:
                command_args.extend(["--image", image])
        if args.thread_id:
            command_args.extend(["resume", args.thread_id])

        env = self._build_env(args)

        process = await asyncio.create_subprocess_exec(
            self._executable_path,
            *command_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stderr_task: asyncio.Task[bytes] | None = None
        try:
            if process.stdin is None or process.stdout is None:
                raise RuntimeError("Codex exec subprocess missing stdin/stdout")

            process.stdin.write(args.input_text.encode("utf-8"))
            await process.stdin.drain()
            process.stdin.close()

            if process.stderr is not None:
                stderr_task = asyncio.create_task(_read_stream(process.stderr))

            async for line in _iter_lines(process.stdout, args.signal):
                yield line

            returncode = await process.wait()
            stderr_bytes = b""
            if stderr_task is not None:
                stderr_bytes = await stderr_task

            if returncode != 0:
                detail = (
                    f"signal {-returncode}" if returncode < 0 else f"code {returncode}"
                )
                raise RuntimeError(
                    f"Codex Exec exited with {detail}: {stderr_bytes.decode('utf-8', 'replace')}"
                )
        finally:
            if stderr_task is not None and not stderr_task.done():
                stderr_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await stderr_task
            if process.returncode is None:
                process.kill()
                with contextlib.suppress(ProcessLookupError):
                    await process.wait()

    def _build_env(self, args: CodexExecArgs) -> dict[str, str]:
        env: dict[str, str] = {}
        if self._env_override is not None:
            env.update(self._env_override)
        else:
            env.update(
                {key: value for key, value in os.environ.items() if value is not None}
            )

        if INTERNAL_ORIGINATOR_ENV not in env:
            env[INTERNAL_ORIGINATOR_ENV] = PYTHON_SDK_ORIGINATOR
        if args.base_url:
            env["OPENAI_BASE_URL"] = args.base_url
        if args.api_key:
            env["CODEX_API_KEY"] = args.api_key
        return env


async def _read_stream(stream: asyncio.StreamReader) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = await stream.read(8192)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


async def _iter_lines(
    stream: asyncio.StreamReader, signal: asyncio.Event | None
) -> AsyncIterator[str]:
    while True:
        if signal is None:
            line = await stream.readline()
        else:
            line_task = asyncio.create_task(stream.readline())
            signal_task = asyncio.create_task(signal.wait())
            done, pending = await asyncio.wait(
                [line_task, signal_task], return_when=asyncio.FIRST_COMPLETED
            )
            if signal_task in done:
                line_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await line_task
                raise asyncio.CancelledError("Codex exec cancelled")
            signal_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await signal_task
            line = line_task.result()

        if not line:
            break
        yield line.decode("utf-8", "replace").rstrip("\r\n")


def _find_codex_path() -> str:
    installed = shutil.which("codex")
    if installed:
        return installed
    raise RuntimeError(
        "Could not find `codex` on PATH; set codex_path_override to override."
    )
