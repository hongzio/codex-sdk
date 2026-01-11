from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


@dataclass(slots=True)
class OutputSchemaFile:
    schema_path: str | None
    cleanup: Callable[[], Awaitable[None]]


async def create_output_schema_file(schema: Any | None) -> OutputSchemaFile:
    if schema is None:

        async def _noop() -> None:
            return None

        return OutputSchemaFile(schema_path=None, cleanup=_noop)

    if not _is_json_object(schema):
        raise ValueError("output_schema must be a plain JSON object")

    schema_dir = tempfile.mkdtemp(prefix="codex-output-schema-")
    schema_path = os.path.join(schema_dir, "schema.json")

    async def cleanup() -> None:
        try:
            shutil.rmtree(schema_dir, ignore_errors=True)
        except Exception:
            pass

    try:
        with open(schema_path, "w", encoding="utf-8") as handle:
            json.dump(schema, handle)
        return OutputSchemaFile(schema_path=schema_path, cleanup=cleanup)
    except Exception:
        await cleanup()
        raise


def _is_json_object(value: Any) -> bool:
    return isinstance(value, dict)
