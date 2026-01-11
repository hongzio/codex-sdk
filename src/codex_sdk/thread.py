from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Literal, TypedDict, TypeGuard, Union

from .events import (
    ItemCompletedEvent,
    ThreadEvent,
    ThreadError,
    ThreadStartedEvent,
    TurnCompletedEvent,
    TurnFailedEvent,
    Usage,
)
from .exec import CodexExec, CodexExecArgs
from .items import ThreadItem
from .options import CodexOptions, ThreadOptions, TurnOptions
from .output_schema_file import create_output_schema_file


@dataclass(slots=True)
class Turn:
    items: list[ThreadItem]
    final_response: str
    usage: Usage | None


RunResult = Turn


@dataclass(slots=True)
class StreamedTurn:
    events: AsyncIterator[ThreadEvent]


RunStreamedResult = StreamedTurn


class TextInput(TypedDict):
    type: Literal["text"]
    text: str


class LocalImageInput(TypedDict):
    type: Literal["local_image"]
    path: str


UserInput = Union[TextInput, LocalImageInput]
Input = Union[str, list[UserInput]]


class Thread:
    def __init__(
        self,
        exec_: CodexExec,
        options: CodexOptions,
        thread_options: ThreadOptions,
        thread_id: str | None = None,
    ) -> None:
        self._exec = exec_
        self._options = options
        self._thread_options = thread_options
        self._id = thread_id

    @property
    def id(self) -> str | None:
        return self._id

    async def run_streamed(
        self,
        input_: Input,
        turn_options: TurnOptions | None = None,
        *,
        output_schema: Any | None = None,
        signal: asyncio.Event | None = None,
    ) -> StreamedTurn:
        return StreamedTurn(
            events=self._run_streamed_internal(
                input_,
                _normalize_turn_options(
                    turn_options, output_schema=output_schema, signal=signal
                ),
            )
        )

    async def _run_streamed_internal(
        self, input_: Input, turn_options: TurnOptions
    ) -> AsyncIterator[ThreadEvent]:
        schema_file = await create_output_schema_file(turn_options.output_schema)
        options = self._thread_options
        prompt, images = _normalize_input(input_)
        generator = self._exec.run(
            CodexExecArgs(
                input_text=prompt,
                base_url=self._options.base_url,
                api_key=self._options.api_key,
                thread_id=self._id,
                images=images,
                model=options.model,
                sandbox_mode=options.sandbox_mode,
                working_directory=options.working_directory,
                skip_git_repo_check=options.skip_git_repo_check,
                output_schema_file=schema_file.schema_path,
                model_reasoning_effort=options.model_reasoning_effort,
                signal=turn_options.signal,
                network_access_enabled=options.network_access_enabled,
                web_search_enabled=options.web_search_enabled,
                approval_policy=options.approval_policy,
                additional_directories=options.additional_directories,
            )
        )
        try:
            async for item in generator:
                try:
                    parsed = json.loads(item)
                except json.JSONDecodeError as error:
                    raise RuntimeError(f"Failed to parse item: {item}") from error
                event: ThreadEvent = parsed
                if _is_thread_started(event):
                    self._id = event["thread_id"]
                yield event
        finally:
            await schema_file.cleanup()

    async def run(
        self,
        input_: Input,
        turn_options: TurnOptions | None = None,
        *,
        output_schema: Any | None = None,
        signal: asyncio.Event | None = None,
    ) -> Turn:
        generator = self._run_streamed_internal(
            input_,
            _normalize_turn_options(
                turn_options, output_schema=output_schema, signal=signal
            ),
        )
        items: list[ThreadItem] = []
        final_response = ""
        usage: Usage | None = None
        turn_failure: ThreadError | None = None

        async for event in generator:
            if _is_item_completed(event):
                item = event["item"]
                if item["type"] == "agent_message":
                    final_response = item["text"]
                items.append(item)
            elif _is_turn_completed(event):
                usage = event["usage"]
            elif _is_turn_failed(event):
                turn_failure = event["error"]
                break

        if turn_failure is not None:
            raise RuntimeError(turn_failure["message"])

        return Turn(items=items, final_response=final_response, usage=usage)


def _normalize_input(input_: Input) -> tuple[str, list[str]]:
    if isinstance(input_, str):
        return input_, []
    prompt_parts: list[str] = []
    images: list[str] = []
    for item in input_:
        if item["type"] == "text":
            prompt_parts.append(item["text"])
        elif item["type"] == "local_image":
            images.append(item["path"])
    return "\n\n".join(prompt_parts), images


def _normalize_turn_options(
    turn_options: TurnOptions | None,
    *,
    output_schema: Any | None,
    signal: asyncio.Event | None,
) -> TurnOptions:
    if turn_options is not None:
        if output_schema is not None or signal is not None:
            raise ValueError("Pass either TurnOptions or keyword arguments, not both")
        return turn_options
    return TurnOptions(output_schema=output_schema, signal=signal)


def _is_thread_started(event: ThreadEvent) -> TypeGuard[ThreadStartedEvent]:
    return event["type"] == "thread.started"


def _is_item_completed(event: ThreadEvent) -> TypeGuard[ItemCompletedEvent]:
    return event["type"] == "item.completed"


def _is_turn_completed(event: ThreadEvent) -> TypeGuard[TurnCompletedEvent]:
    return event["type"] == "turn.completed"


def _is_turn_failed(event: ThreadEvent) -> TypeGuard[TurnFailedEvent]:
    return event["type"] == "turn.failed"
