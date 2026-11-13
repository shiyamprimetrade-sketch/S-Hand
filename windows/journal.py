"""Durable command replay journal. SQLite transactions survive process restarts.

A command is reserved before any side effect. Uncertain interrupted commands are
never automatically replayed. Explicit recovery must be handled by S.
"""
import sqlite3
import threading
from pathlib import Path

class Journal:
    def __init__(self, filename):
        self.filename = str(Path(filename).expanduser())
        self.lock = threading.Lock()
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS commands (
                command_id TEXT PRIMARY KEY,
                fingerprint TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT
            )""")

    def _db(self):
        return sqlite3.connect(self.filename, timeout=10)

    def reserve(self, command):
        with self.lock, self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT fingerprint, status FROM commands WHERE command_id=?",
                             (command.command_id,)).fetchone()
            if row:
                return "duplicate" if row[0] == command.fingerprint() else "conflict"
            db.execute("INSERT INTO commands VALUES (?, ?, 'reserved', NULL)",
                       (command.command_id, command.fingerprint()))
            return "new"

    def finish(self, command_id, status, detail=None):
        if status not in ("completed", "failed"):
            raise ValueError("Invalid terminal status")
        with self.lock, self._db() as db:
            updated = db.execute(
                "UPDATE commands SET status=?, detail=? WHERE command_id=? AND status='reserved'",
                (status, detail, command_id))
            if updated.rowcount != 1:
                raise ValueError("Unknown or already finalized command")

    def get(self, command_id):
        with self.lock, self._db() as db:
            row = db.execute("SELECT status, detail FROM commands WHERE command_id=?",
                             (command_id,)).fetchone()
            return None if row is None else {"status": row[0], "detail": row[1]}
