from __future__ import annotations

from typing import NotRequired, TypedDict, Unpack

from .exec import CodexExec
from .options import (
    ApprovalMode,
    CodexOptions,
    ModelReasoningEffort,
    SandboxMode,
    ThreadOptions,
)
from .thread import Thread


class ThreadOptionsKwargs(TypedDict, total=False):
    model: NotRequired[str | None]
    sandbox_mode: NotRequired[SandboxMode | None]
    working_directory: NotRequired[str | None]
    skip_git_repo_check: NotRequired[bool | None]
    model_reasoning_effort: NotRequired[ModelReasoningEffort | None]
    network_access_enabled: NotRequired[bool | None]
    web_search_enabled: NotRequired[bool | None]
    approval_policy: NotRequired[ApprovalMode | None]
    additional_directories: NotRequired[list[str] | None]


class Codex:
    """Main entrypoint for interacting with the Codex agent."""

    def __init__(self, options: CodexOptions | None = None) -> None:
        self._options = options or CodexOptions()
        self._exec = CodexExec(self._options.codex_path_override, self._options.env)

    def start_thread(
        self,
        options: ThreadOptions | None = None,
        **kwargs: Unpack[ThreadOptionsKwargs],
    ) -> Thread:
        return Thread(
            self._exec, self._options, _normalize_thread_options(options, **kwargs)
        )

    def resume_thread(
        self,
        thread_id: str,
        options: ThreadOptions | None = None,
        **kwargs: Unpack[ThreadOptionsKwargs],
    ) -> Thread:
        return Thread(
            self._exec,
            self._options,
            _normalize_thread_options(options, **kwargs),
            thread_id,
        )


def _normalize_thread_options(
    options: ThreadOptions | None, **kwargs: Unpack[ThreadOptionsKwargs]
) -> ThreadOptions:
    if options is not None:
        if kwargs:
            raise ValueError("Pass either ThreadOptions or keyword arguments, not both")
        return options
    return ThreadOptions(**kwargs)
