import os
import unittest

from codex_sdk.exec import CodexExec, CodexExecArgs


class ExecEnvTests(unittest.TestCase):
    def test_env_override_is_respected(self):
        os.environ["CODEX_ENV_SHOULD_NOT_LEAK"] = "leak"
        try:
            exec_ = CodexExec(executable_path="codex", env={"CUSTOM_ENV": "custom"})
            args = CodexExecArgs(
                input_text="hi", base_url="http://example.test", api_key="test"
            )
            env = exec_._build_env(args)

            self.assertEqual(env["CUSTOM_ENV"], "custom")
            self.assertNotIn("CODEX_ENV_SHOULD_NOT_LEAK", env)
            self.assertEqual(env["OPENAI_BASE_URL"], "http://example.test")
            self.assertEqual(env["CODEX_API_KEY"], "test")
            self.assertIn("CODEX_INTERNAL_ORIGINATOR_OVERRIDE", env)
        finally:
            os.environ.pop("CODEX_ENV_SHOULD_NOT_LEAK", None)
