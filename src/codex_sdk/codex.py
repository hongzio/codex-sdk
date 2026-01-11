from __future__ import annotations

from .exec import CodexExec
from .options import CodexOptions, ThreadOptions
from .thread import Thread


class Codex:
    """Main entrypoint for interacting with the Codex agent."""

    def __init__(self, options: CodexOptions | None = None) -> None:
        self._options = options or CodexOptions()
        self._exec = CodexExec(self._options.codex_path_override, self._options.env)

    def start_thread(self, options: ThreadOptions | None = None, **kwargs: object) -> Thread:
        return Thread(self._exec, self._options, _normalize_thread_options(options, **kwargs))

    def resume_thread(
        self, thread_id: str, options: ThreadOptions | None = None, **kwargs: object
    ) -> Thread:
        return Thread(self._exec, self._options, _normalize_thread_options(options, **kwargs), thread_id)


def _normalize_thread_options(options: ThreadOptions | None, **kwargs: object) -> ThreadOptions:
    if options is not None:
        if kwargs:
            raise ValueError("Pass either ThreadOptions or keyword arguments, not both")
        return options
    return ThreadOptions(**kwargs)
