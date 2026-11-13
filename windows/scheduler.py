"""Sequential, fail-closed plan runner with durable per-command journal.

Not exposed as an HTTP endpoint. Call only from an authorized controller.
Interrupted commands are never replayed automatically.
"""
from dataclasses import dataclass
from plans import Plan

class PlanExecutionError(RuntimeError):
    pass

@dataclass(frozen=True)
class StepResult:
    command_id: str
    status: str
    detail: object = None

class PlanRunner:
    def __init__(self, journal, executor, is_armed):
        self.journal = journal
        self.executor = executor
        self.is_armed = is_armed

    def run(self, plan):
        if not isinstance(plan, Plan):
            raise TypeError("Expected a validated Plan")
        results = []
        for command in plan.commands:
            if not self.is_armed():
                results.append(StepResult(command.command_id, "stopped"))
                break
            state = self.journal.reserve(command)
            if state != "new":
                results.append(StepResult(command.command_id, "blocked", state))
                break
            try:
                if not self.is_armed():
                    raise PlanExecutionError("Emergency stop activated")
                output = self.executor(command)
            except Exception as exc:
                self.journal.finish(command.command_id, "failed", type(exc).__name__)
                results.append(StepResult(command.command_id, "failed", type(exc).__name__))
                break
            else:
                self.journal.finish(command.command_id, "completed")
                results.append(StepResult(command.command_id, "completed", output))
        return results
