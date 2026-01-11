import json
import unittest

from codex_sdk.exec import CodexExec
from codex_sdk.options import CodexOptions, ThreadOptions
from codex_sdk.thread import LocalImageInput, TextInput, Thread, UserInput


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


class ThreadRunTests(unittest.IsolatedAsyncioTestCase):
    async def test_run_collects_items_and_usage(self):
        exec_stub = StubExec(make_basic_events())
        thread = Thread(exec_stub, CodexOptions(), ThreadOptions())

        result = await thread.run("hello")

        self.assertEqual(thread.id, "thread-1")
        self.assertEqual(result.final_response, "Hi!")
        self.assertEqual(
            result.items,
            [{"id": "item-1", "type": "agent_message", "text": "Hi!"}],
        )
        self.assertEqual(
            result.usage,
            {"cached_input_tokens": 1, "input_tokens": 2, "output_tokens": 3},
        )

    async def test_run_streamed_yields_events(self):
        events = make_basic_events()
        exec_stub = StubExec(events)
        thread = Thread(exec_stub, CodexOptions(), ThreadOptions())

        streamed = await thread.run_streamed("hello")
        received = [event async for event in streamed.events]

        self.assertEqual(received, events)
        self.assertEqual(thread.id, "thread-1")

    async def test_normalizes_structured_input_and_images(self):
        exec_stub = StubExec(make_basic_events())
        thread = Thread(exec_stub, CodexOptions(), ThreadOptions())

        first: TextInput = {"type": "text", "text": "Describe file changes"}
        second: TextInput = {"type": "text", "text": "Focus on impacted tests"}
        image: LocalImageInput = {"type": "local_image", "path": "/tmp/image.png"}
        inputs: list[UserInput] = [first, second, image]
        await thread.run(inputs)

        args = exec_stub.calls[0]
        self.assertEqual(
            args.input_text, "Describe file changes\n\nFocus on impacted tests"
        )
        self.assertEqual(args.images, ["/tmp/image.png"])
