# Codex SDK (Python) - Development Guide

This repository contains the Python SDK for the Codex CLI plus a submodule with the Codex implementation sources.

## Project layout

- `src/codex_sdk/`: Python SDK implementation (async client, thread handling, exec wrapper, types).
- `README.md`: Python SDK usage and examples; keep in sync with API surface changes.
- `pyproject.toml`: Python package metadata and dependencies.
- `codex/`: Git submodule pinned to a specific commit of https://github.com/openai/codex.git for migration traceability.
  - TypeScript SDK migration source: `codex/sdk/typescript/`.

## Prerequisites

- Python version is pinned via `.python-version` (currently 3.11.x).
- Use `uv` for environment syncs.

## Setup

```bash
uv sync
```

This installs the package in the current environment and prepares dependencies.

## Running a quick smoke test

The SDK drives the installed `codex` binary (first found in `PATH`, then falls back to a bundled vendor path).
Make sure `codex --version` works in your terminal.

```bash
python - <<'PY'
import asyncio
from codex_sdk import Codex

async def main():
    thread = Codex().start_thread()
    turn = await thread.run("Say hello")
    print(turn.final_response)

asyncio.run(main())
PY
```

Note: `codex exec --experimental-json` can fail inside sandboxed environments due to macOS SystemConfiguration
restrictions. Run outside sandbox if you see panics from `system-configuration` or `reqwest`.

## Common tasks

- Update dependencies: `uv sync`
- Update README examples after API changes.
- Ensure `codex/` submodule remains pinned unless you intentionally update the migration baseline.
- Commit messages must follow Conventional Commits.

## Testing

- Type checking: `ty check`
- Linting: `ruff check`
- Unit tests: `uv run python -m unittest discover -s tests`
- If you add tests, document the commands here.

## Code conventions

- Keep Python code async-first (uses asyncio).
- Use `typing` (TypedDict/Literal/Union) for structured event/item models.
- Keep comments minimal and focused on non-obvious logic.
