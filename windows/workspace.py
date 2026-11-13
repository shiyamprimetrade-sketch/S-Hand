"""Constrained file operations for S-Hand coding workflows.

S decides content; this module only applies explicit file operations.
No arbitrary command execution is exposed.
"""
from pathlib import Path
import os
import tempfile

MAX_TEXT = 2_000_000

class WorkspaceError(ValueError):
    pass

class Workspace:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        if not self.root.is_dir():
            raise WorkspaceError("Workspace root must exist")

    def resolve(self, relative):
        if not isinstance(relative, str) or not relative or "\\x00" in relative:
            raise WorkspaceError("Invalid path")
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise WorkspaceError("Absolute/traversal paths forbidden")
        destination = (self.root / path).resolve()
        if not destination.is_relative_to(self.root) or destination == self.root:
            raise WorkspaceError("Path escapes workspace")
        return destination

    def write(self, relative, text):
        if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_TEXT:
            raise WorkspaceError("Invalid or oversized text")
        destination = self.resolve(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Re-check after creating directories to catch symlink changes.
        destination = self.resolve(relative)
        fd, temporary = tempfile.mkstemp(prefix=".shand-", dir=destination.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
                out.write(text)
                out.flush()
                os.fsync(out.fileno())
            # Prevent writing through symlink; atomic replace changes link itself.
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return {"ok": True, "path": relative, "bytes": len(text.encode("utf-8"))}

    def read(self, relative):
        path = self.resolve(relative)
        if not path.is_file() or path.stat().st_size > MAX_TEXT:
            raise WorkspaceError("File missing or too large")
        return {"ok": True, "path": relative, "text": path.read_text(encoding="utf-8")}
