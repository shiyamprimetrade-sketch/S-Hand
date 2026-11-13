import unittest
from protocol import Command, ProtocolError, receipt
from replay import ReplayGuard

def example(**changes):
    data = {"protocol_version": "1.0", "command_id": "task-1", "target": "windows",
            "action": "type_text", "arguments": {"text": "hello"}}
    data.update(changes)
    return data

class ProtocolTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(Command.parse(example()).legacy_action()["text"], "hello")
    def test_bad_version(self):
        with self.assertRaises(ProtocolError):
            Command.parse(example(protocol_version="2.0"))
    def test_bad_id(self):
        with self.assertRaises(ProtocolError):
            Command.parse(example(command_id="../escape"))
    def test_bad_action(self):
        with self.assertRaises(ProtocolError):
            Command.parse(example(action="shell", arguments={}))
    def test_bad_target(self):
        with self.assertRaises(ProtocolError):
            Command.parse(example(target="unknown"))
    def test_bad_arguments(self):
        with self.assertRaises(ProtocolError):
            Command.parse(example(arguments={"text": "hi", "extra": 1}))
    def test_bad_coordinates(self):
        with self.assertRaises(ProtocolError):
            Command.parse(example(action="click", arguments={"x": True, "y": 2}))
    def test_bad_android_action(self):
        with self.assertRaises(ProtocolError):
            Command.parse(example(target="android", action="press", arguments={"key": "enter"}))
    def test_replay(self):
        guard = ReplayGuard()
        command = Command.parse(example())
        self.assertEqual(guard.claim(command), "new")
        self.assertEqual(guard.claim(command), "duplicate")
    def test_replay_conflict(self):
        guard = ReplayGuard()
        guard.claim(Command.parse(example()))
        self.assertEqual(guard.claim(Command.parse(example(arguments={"text": "different"})), "conflict")
    def test_receipt(self):
        self.assertEqual(receipt("task-1", "completed")["status"], "completed")

if __name__ == "__main__":
    unittest.main()
