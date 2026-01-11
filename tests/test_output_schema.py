import pathlib
import unittest

from codex_sdk.output_schema_file import create_output_schema_file


class OutputSchemaFileTests(unittest.IsolatedAsyncioTestCase):
    async def test_schema_file_lifecycle(self):
        schema = {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        }

        result = await create_output_schema_file(schema)
        self.assertIsNotNone(result.schema_path)
        assert result.schema_path is not None
        path = pathlib.Path(result.schema_path)
        self.assertTrue(path.exists())

        await result.cleanup()
        self.assertFalse(path.exists())

    async def test_rejects_non_object_schema(self):
        with self.assertRaises(ValueError):
            await create_output_schema_file(["not", "an", "object"])
