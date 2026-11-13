import tempfile
import unittest
from pathlib import Path
from journal import Journal
from plans import Plan
from scheduler import PlanRunner

def plan():
    return Plan.parse({"plan_id": "demo", "commands": [
        {"protocol_version": "1.0", "command_id": f"step-{i}",
         "target": "windows", "action": "press", "arguments": {"key": "enter"}}
        for i in range(3)
    ]})

class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.journal = Journal(Path(self.temp.name) / "steps.db")

    def test_three_steps(self):
        seen = []
        results = PlanRunner(self.journal, lambda c: seen.append(c.command_id), lambda: True).run(plan())
        self.assertEqual(len(seen), 3)
        self.assertEqual([r.status for r in results], ["completed"] * 3)

    def test_stopped_before_first_step(self):
        seen = []
        results = PlanRunner(self.journal, lambda c: seen.append(c), lambda: False).run(plan())
        self.assertEqual(seen, [])
        self.assertEqual(results[0].status, "stopped")
        self.assertIsNone(self.journal.get("step-0"))

    def test_stop_between_steps(self):
        armed = [True]
        def execute(command):
            armed[0] = False
        results = PlanRunner(self.journal, execute, lambda: armed[0]).run(plan())
        self.assertEqual([r.status for r in results], ["completed", "stopped"])

    def test_fail_stops_plan(self):
        def fail(command):
            raise OSError("device")
        results = PlanRunner(self.journal, fail, lambda: True).run(plan())
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, "failed")
        self.assertEqual(self.journal.get("step-0")["status"], "failed")

    def test_restart_does_not_replay(self):
        calls = []
        runner = PlanRunner(self.journal, lambda c: calls.append(c.command_id), lambda: True)
        runner.run(plan())
        results = runner.run(plan())
        self.assertEqual(len(calls), 3)
        self.assertEqual(results[0].status, "blocked")

    def test_reserved_interruption_is_blocked(self):
        p = plan()
        self.journal.reserve(p.commands[0])
        results = PlanRunner(self.journal, lambda c: None, lambda: True).run(p)
        self.assertEqual(results[0].status, "blocked")
        self.assertEqual(self.journal.get("step-0")["status"], "reserved")

if __name__ == "__main__":
    unittest.main()
