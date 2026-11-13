"""Validate an ordered action plan before execution.

This module intentionally does not execute actions. The scheduler will consume
validated plans only after authorization and cancellation checks.
"""
from dataclasses import dataclass
from protocol import Command, ProtocolError

MAX_STEPS = 100

class PlanError(ValueError):
    pass

@dataclass(frozen=True)
class Plan:
    plan_id: str
    commands: tuple

    @classmethod
    def parse(cls, payload):
        if not isinstance(payload, dict) or set(payload) != {"plan_id", "commands"}:
            raise PlanError("Expected plan_id and commands")
        pid = payload["plan_id"]
        if not isinstance(pid, str) or not 1 <= len(pid) <= 128 or not pid.replace("-", "").replace("_", "").isalnum():
            raise PlanError("Invalid plan ID")
        raw = payload["commands"]
        if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_STEPS:
            raise PlanError("Plan requires 1 to 100 commands")
        commands = tuple(Command.parse(item) for item in raw)
        if any(cmd.target != "windows" for cmd in commands):
            raise PlanError("Mixed or unsupported execution targets")
        ids = [cmd.command_id for cmd in commands]
        if len(set(ids)) != len(ids):
            raise PlanError("Duplicate command IDs in plan")
        return cls(pid, commands)
