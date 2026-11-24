import tempfile
import unittest
from pathlib import Path
from journal import Journal

class DatabaseLifecycleTests(unittest.TestCase):
    def test_close_and_rollback(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "steps.db"
            journal = Journal(path)
            for _ in range(100):
                with journal._db() as db:
                    db.execute("SELECT 1").fetchone()
            with self.assertRaises(RuntimeError):
                with journal._db() as db:
                    db.execute("INSERT INTO commands VALUES ('x','hash','reserved',NULL)")
                    raise RuntimeError("injected")
            self.assertIsNone(journal.get("x"))
            path.unlink()
            self.assertFalse(path.exists())
