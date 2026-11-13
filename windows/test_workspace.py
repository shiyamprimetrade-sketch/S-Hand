import tempfile
import unittest
from pathlib import Path
from workspace import Workspace, WorkspaceError

class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ws = Workspace(self.tmp.name)

    def test_write_read_unicode(self):
        result = self.ws.write("src/main.py", "print('হ্যালো')\n")
        self.assertTrue(result["ok"])
        self.assertEqual(self.ws.read("src/main.py")["text"], "print('হ্যালো')\n")

    def test_reject_traversal(self):
        with self.assertRaises(WorkspaceError):
            self.ws.write("../outside.txt", "x")

    def test_reject_absolute(self):
        with self.assertRaises(WorkspaceError):
            self.ws.write("/tmp/outside.txt", "x")

    def test_reject_oversize(self):
        with self.assertRaises(WorkspaceError):
            self.ws.write("big.txt", "a" * 2_000_001)

    def test_reject_symlink_escape(self):
        with tempfile.TemporaryDirectory() as external:
            (Path(self.tmp.name) / "link").symlink_to(external, target_is_directory=True)
            with self.assertRaises(WorkspaceError):
                self.ws.write("link/out.txt", "x")

if __name__ == "__main__":
    unittest.main()
