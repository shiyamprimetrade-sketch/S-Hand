"""Controller endpoint tests without real mouse or keyboard devices."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
import agent
from journal import Journal

class FakeHandler(agent.Handler):
    def __init__(self, route, token, body):
        encoded = json.dumps(body).encode()
        self.path = route
        self.headers = {"X-S-Hand-Token": token, "Content-Length": str(len(encoded))}
        self.rfile = io.BytesIO(encoded)
        self.code = None
        self.data = None
    def respond(self, code, obj):
        self.code, self.data = code, obj

def plan():
    return {"plan_id": "test-plan", "commands": [
        {"protocol_version": "1.0", "command_id": "step-1", "target": "windows",
         "action": "press", "arguments": {"key": "enter"}}]}

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.old_journal = agent.JOURNAL
        self.old_armed = agent.ARMED.is_set()
        agent.JOURNAL = Journal(Path(self.temp.name) / "test.db")
        agent.ARMED.set()
    def tearDown(self):
        agent.JOURNAL = self.old_journal
        if self.old_armed:
            agent.ARMED.set()
        else:
            agent.ARMED.clear()

    def test_plan_requires_token(self):
        h = FakeHandler("/plan", "bad", plan())
        h.do_POST()
        self.assertEqual(h.code, 401)

    def test_plan_disarmed(self):
        agent.ARMED.clear()
        h = FakeHandler("/plan", agent.TOKEN, plan())
        h.do_POST()
        self.assertEqual(h.code, 423)

    def test_plan_executes_once(self):
        with patch.dict("sys.modules", {"pyautogui": Mock()}), patch("agent.execute", return_value={"ok": True}) as execute:
            h = FakeHandler("/plan", agent.TOKEN, plan())
            h.do_POST()
            self.assertEqual(h.code, 200)
            self.assertEqual(h.data["results"][0]["status"], "completed")
            execute.assert_called_once()
            again = FakeHandler("/plan", agent.TOKEN, plan())
            again.do_POST()
            self.assertEqual(again.data["results"][0]["status"], "blocked")
            execute.assert_called_once()

    def test_bad_plan_rejected(self):
        h = FakeHandler("/plan", agent.TOKEN, {"plan_id": "invalid", "commands": []})
        h.do_POST()
        self.assertEqual(h.code, 400)

if __name__ == "__main__":
    unittest.main()
