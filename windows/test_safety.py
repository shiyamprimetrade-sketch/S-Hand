"""Tests for default-disarmed and emergency stop HTTP controls."""
import io
import json
import unittest
from unittest.mock import patch
import agent

class FakeHandler(agent.Handler):
    def __init__(self, path, token):
        self.path = path
        self.headers = {"X-S-Hand-Token": token, "Content-Length": "2"}
        self.rfile = io.BytesIO(b"{}")
        self.code = None
        self.data = None
    def respond(self, code, obj):
        self.code, self.data = code, obj

class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.original = agent.ARMED.is_set()
        agent.ARMED.clear()
    def tearDown(self):
        if self.original:
            agent.ARMED.set()
        else:
            agent.ARMED.clear()
    def test_default_disarmed(self):
        h = FakeHandler("/action", agent.TOKEN)
        h.do_POST()
        self.assertEqual(h.code, 423)
    def test_unauthorized_stop(self):
        h = FakeHandler("/stop", "incorrect")
        h.do_POST()
        self.assertEqual(h.code, 401)
    def test_authorized_stop(self):
        agent.ARMED.set()
        h = FakeHandler("/stop", agent.TOKEN)
        h.do_POST()
        self.assertEqual(h.code, 200)
        self.assertFalse(agent.ARMED.is_set())
    def test_disarmed_after_stop(self):
        agent.ARMED.set()
        FakeHandler("/stop", agent.TOKEN).do_POST()
        h = FakeHandler("/action", agent.TOKEN)
        h.do_POST()
        self.assertEqual(h.code, 423)
    def test_unknown_route(self):
        h = FakeHandler("/other", agent.TOKEN)
        h.do_POST()
        self.assertEqual(h.code, 404)

if __name__ == "__main__":
    unittest.main()
