import unittest
from plans import Plan, PlanError

def command(cid):
    return {"protocol_version": "1.0", "command_id": cid,
            "target": "windows", "action": "press",
            "arguments": {"key": "enter"}}

class PlanTests(unittest.TestCase):
    def test_valid(self):
        p = Plan.parse({"plan_id": "build-1", "commands": [command("one"), command("two")]})
        self.assertEqual(len(p.commands), 2)

    def test_duplicate_ids(self):
        with self.assertRaises(PlanError):
            Plan.parse({"plan_id": "build-1", "commands": [command("one"), command("one")]})

    def test_empty(self):
        with self.assertRaises(PlanError):
            Plan.parse({"plan_id": "build-1", "commands": []})

    def test_oversize(self):
        with self.assertRaises(PlanError):
            Plan.parse({"plan_id": "build-1", "commands": [command(str(i)) for i in range(101)]})

    def test_mixed_target(self):
        c = command("one")
        c["target"] = "android"
        c["action"] = "click"
        c["arguments"] = {"x": 1, "y": 2}
        with self.assertRaises(PlanError):
            Plan.parse({"plan_id": "build-1", "commands": [c]})

    def test_invalid_envelope(self):
        with self.assertRaises(ValueError):
            Plan.parse({"plan_id": "build-1", "commands": [{"action": "press"}]})

if __name__ == "__main__":
    unittest.main()
