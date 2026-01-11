import json
import unittest

from codex_sdk.exec import CodexExec
from codex_sdk.options import CodexOptions, ThreadOptions
from codex_sdk.thread import Thread


class StubExec(CodexExec):
    def __init__(self, events):
        super().__init__(executable_path="codex")
        self._events = [json.dumps(event) for event in events]
        self.calls = []

    async def run(self, args):
        self.calls.append(args)
        for line in self._events:
            yield line


def make_basic_events(thread_id="thread-1", message="Hi!"):
    return [
        {"type": "thread.started", "thread_id": thread_id},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"id": "item-1", "type": "agent_message", "text": message},
        },
        {
            "type": "turn.completed",
            "usage": {"cached_input_tokens": 1, "input_tokens": 2, "output_tokens": 3},
        },
    ]


class ThreadOptionTests(unittest.IsolatedAsyncioTestCase):
    async def test_thread_options_forwarded_to_exec(self):
        exec_stub = StubExec(make_basic_events())
        options = ThreadOptions(
            model="gpt-test-1",
            sandbox_mode="workspace-write",
            working_directory="/tmp/work",
            skip_git_repo_check=True,
            model_reasoning_effort="high",
            network_access_enabled=True,
            web_search_enabled=False,
            approval_policy="on-request",
            additional_directories=["/tmp/a", "/tmp/b"],
        )
        thread = Thread(exec_stub, CodexOptions(), options)

        await thread.run("apply options")

        args = exec_stub.calls[0]
        self.assertEqual(args.model, "gpt-test-1")
        self.assertEqual(args.sandbox_mode, "workspace-write")
        self.assertEqual(args.working_directory, "/tmp/work")
        self.assertTrue(args.skip_git_repo_check)
        self.assertEqual(args.model_reasoning_effort, "high")
        self.assertTrue(args.network_access_enabled)
        self.assertFalse(args.web_search_enabled)
        self.assertEqual(args.approval_policy, "on-request")
        self.assertEqual(args.additional_directories, ["/tmp/a", "/tmp/b"])

    async def test_resume_thread_forwards_id(self):
        exec_stub = StubExec(make_basic_events(thread_id="thread-123"))
        thread = Thread(exec_stub, CodexOptions(), ThreadOptions(), "thread-123")

        await thread.run("resume")

        args = exec_stub.calls[0]
        self.assertEqual(args.thread_id, "thread-123")
