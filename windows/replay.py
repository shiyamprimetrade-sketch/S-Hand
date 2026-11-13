"""Reject duplicate command IDs and conflicting replays within one agent session."""
from collections import OrderedDict
from threading import Lock

class ReplayGuard:
    def __init__(self, capacity=4096):
        self.capacity = capacity
        self.seen = OrderedDict()
        self.lock = Lock()

    def claim(self, command):
        with self.lock:
            previous = self.seen.get(command.command_id)
            if previous is not None:
                return "duplicate" if previous == command.fingerprint() else "conflict"
            self.seen[command.command_id] = command.fingerprint()
            if len(self.seen) > self.capacity:
                self.seen.popitem(last=False)
            return "new"
