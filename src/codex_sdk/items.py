from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict, Union

McpContentBlock = dict[str, Any]

CommandExecutionStatus = Literal["in_progress", "completed", "failed"]
PatchChangeKind = Literal["add", "delete", "update"]
PatchApplyStatus = Literal["completed", "failed"]
McpToolCallStatus = Literal["in_progress", "completed", "failed"]


class CommandExecutionItem(TypedDict):
    id: str
    type: Literal["command_execution"]
    command: str
    aggregated_output: str
    exit_code: NotRequired[int]
    status: CommandExecutionStatus


class FileUpdateChange(TypedDict):
    path: str
    kind: PatchChangeKind


class FileChangeItem(TypedDict):
    id: str
    type: Literal["file_change"]
    changes: list[FileUpdateChange]
    status: PatchApplyStatus


class McpToolCallResult(TypedDict):
    content: list[McpContentBlock]
    structured_content: Any


class McpToolCallError(TypedDict):
    message: str


class McpToolCallItem(TypedDict):
    id: str
    type: Literal["mcp_tool_call"]
    server: str
    tool: str
    arguments: Any
    result: NotRequired[McpToolCallResult]
    error: NotRequired[McpToolCallError]
    status: McpToolCallStatus


class AgentMessageItem(TypedDict):
    id: str
    type: Literal["agent_message"]
    text: str


class ReasoningItem(TypedDict):
    id: str
    type: Literal["reasoning"]
    text: str


class WebSearchItem(TypedDict):
    id: str
    type: Literal["web_search"]
    query: str


class ErrorItem(TypedDict):
    id: str
    type: Literal["error"]
    message: str


class TodoItem(TypedDict):
    text: str
    completed: bool


class TodoListItem(TypedDict):
    id: str
    type: Literal["todo_list"]
    items: list[TodoItem]


ThreadItem = Union[
    AgentMessageItem,
    ReasoningItem,
    CommandExecutionItem,
    FileChangeItem,
    McpToolCallItem,
    WebSearchItem,
    TodoListItem,
    ErrorItem,
]
