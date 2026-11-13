import tempfile
import unittest
from pathlib import Path
from journal import Journal
from protocol import Command

def cmd(text="hello"):
    return Command.parse({"protocol_version": "1.0", "command_id": "job-1",
        "target": "windows", "action": "type_text", "arguments": {"text": text}})

class JournalTests(unittest.TestCase):
    def test_restart_does_not_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.db"
            first = Journal(path)
            self.assertEqual(first.reserve(cmd()), "new")
            first.finish("job-1", "completed")
            second = Journal(path)
            self.assertEqual(second.reserve(cmd()), "duplicate")
            self.assertEqual(second.get("job-1")["status"], "completed")
            self.assertEqual(second.reserve(cmd("changed")), "conflict")

    def test_interrupted_command_stays_reserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.db"
            Journal(path).reserve(cmd())
            reopened = Journal(path)
            self.assertEqual(reopened.reserve(cmd()), "duplicate")
            self.assertEqual(reopened.get("job-1")["status"], "reserved")

    def test_cannot_finish_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = Journal(Path(tmp) / "journal.db")
            journal.reserve(cmd())
            journal.finish("job-1", "failed", "device unavailable")
            with self.assertRaises(ValueError):
                journal.finish("job-1", "completed")

if __name__ == "__main__":
    unittest.main()
