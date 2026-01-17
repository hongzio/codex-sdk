from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Literal

ApprovalMode = Literal["never", "on-request", "on-failure", "untrusted"]
SandboxMode = Literal["read-only", "workspace-write", "danger-full-access"]
ModelReasoningEffort = Literal["minimal", "low", "medium", "high", "xhigh"]
WebSearchMode = Literal["disabled", "cached", "live"]


@dataclass(slots=True)
class CodexOptions:
    codex_path_override: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    env: dict[str, str] | None = None


@dataclass(slots=True)
class ThreadOptions:
    model: str | None = None
    sandbox_mode: SandboxMode | None = None
    working_directory: str | None = None
    skip_git_repo_check: bool | None = None
    model_reasoning_effort: ModelReasoningEffort | None = None
    network_access_enabled: bool | None = None
    web_search_mode: WebSearchMode | None = None
    web_search_enabled: bool | None = None
    approval_policy: ApprovalMode | None = None
    additional_directories: list[str] | None = None


@dataclass(slots=True)
class TurnOptions:
    output_schema: Any | None = None
    signal: asyncio.Event | None = None
    stdout_idle_timeout_seconds: float | None = 60.0
