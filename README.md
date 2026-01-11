# Codex SDK (Python)

Embed the Codex agent in your workflows and apps.

The Python SDK wraps the `codex` CLI. It spawns the CLI and exchanges JSONL events over stdin/stdout.
By default it uses the `codex` binary from your `PATH`; you can override the path when constructing `Codex`.

## Installation

```bash
pip install "codex-sdk @ git+https://github.com/hongzio/codex-sdk"
```

Or with `uv`:

```bash
uv add "codex-sdk @ git+https://github.com/hongzio/codex-sdk"
```

Requires Python 3.11+.

## Quickstart

```python
import asyncio

from codex_sdk import Codex


async def main() -> None:
    codex = Codex()
    thread = codex.start_thread()
    turn = await thread.run("Diagnose the test failure and propose a fix")

    print(turn.final_response)
    print(turn.items)


asyncio.run(main())
```

Call `run()` repeatedly on the same `Thread` instance to continue that conversation.

```python
next_turn = await thread.run("Implement the fix")
```

### Streaming responses

`run()` buffers events until the turn finishes. To react to intermediate progress—tool calls, streaming responses, and file
change notifications—use `run_streamed()` instead, which returns an async iterator of structured events.

```python
stream = await thread.run_streamed("Diagnose the test failure and propose a fix")

async for event in stream.events:
    if event["type"] == "item.completed":
        print("item", event["item"])
    elif event["type"] == "turn.completed":
        print("usage", event["usage"])
```

### Structured output

The Codex agent can produce a JSON response that conforms to a specified schema. The schema can be provided for each turn
as a plain JSON object.

```python
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "status": {"type": "string", "enum": ["ok", "action_required"]},
    },
    "required": ["summary", "status"],
    "additionalProperties": False,
}

turn = await thread.run("Summarize repository status", output_schema=schema)
print(turn.final_response)
```

### Attaching images

Provide structured input entries when you need to include images alongside text. Text entries are concatenated into the
final prompt while image entries are passed to the Codex CLI via `--image`.

```python
turn = await thread.run(
    [
        {"type": "text", "text": "Describe these screenshots"},
        {"type": "local_image", "path": "./ui.png"},
        {"type": "local_image", "path": "./diagram.jpg"},
    ]
)
```

### Resuming an existing thread

Threads are persisted in `~/.codex/sessions`. If you lose the in-memory `Thread` object, reconstruct it with
`resume_thread()` and keep going.

```python
thread = codex.resume_thread(saved_thread_id)
await thread.run("Implement the fix")
```

### Working directory controls

Codex runs in the current working directory by default. To avoid unrecoverable errors, Codex requires the working
directory to be a Git repository. You can skip the Git repository check by passing `skip_git_repo_check` when creating a
thread.

```python
thread = codex.start_thread(working_directory="/path/to/project", skip_git_repo_check=True)
```

### Controlling the Codex CLI environment

By default, the Codex CLI inherits the Python process environment. Provide the optional `env` parameter when
instantiating the `Codex` client to fully control which variables the CLI receives—useful for sandboxed hosts.

```python
codex = Codex(env={"PATH": "/usr/local/bin"})
```
