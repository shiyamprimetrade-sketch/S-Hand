"""Versioned S-Hand command envelope with strict validation."""
from dataclasses import dataclass
import hashlib
import json
import re

VERSION = "1.0"
FIELDS = {"protocol_version", "command_id", "target", "action", "arguments"}
ARGS = {"type_text": {"text"}, "press": {"key"}, "hotkey": {"keys"},
        "click": {"x", "y"}, "move": {"x", "y"}, "scroll": {"amount"},
        "write_file": {"path", "text"}, "read_file": {"path"}}

class ProtocolError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code

@dataclass(frozen=True)
class Command:
    command_id: str
    target: str
    action: str
    arguments: dict

    @classmethod
    def parse(cls, payload):
        if not isinstance(payload, dict) or set(payload) != FIELDS:
            raise ProtocolError("invalid_envelope", "Expected exact envelope fields")
        if payload["protocol_version"] != VERSION:
            raise ProtocolError("unsupported_version", "Unsupported protocol version")
        cid = payload["command_id"]
        if not isinstance(cid, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", cid):
            raise ProtocolError("invalid_id", "Invalid command identifier")
        target, action, args = payload["target"], payload["action"], payload["arguments"]
        if not isinstance(target, str) or target not in ("windows", "android"):
            raise ProtocolError("invalid_target", "Unknown target")
        if not isinstance(action, str) or action not in ARGS:
            raise ProtocolError("unsupported_action", "Unknown action")
        if not isinstance(args, dict) or (action == "type_text" and not ({"text"} <= set(args) <= {"text", "expected_window"})) or (action != "type_text" and set(args) != ARGS[action]):
            raise ProtocolError("invalid_arguments", "Wrong action arguments")
        if action == "type_text" and "expected_window" in args and (not isinstance(args["expected_window"], str) or not 1 <= len(args["expected_window"]) <= 200):
            raise ProtocolError("invalid_arguments", "Invalid window target")
        if action in ("type_text", "write_file"):
            value = args["text"]
            if not isinstance(value, str) or len(value.encode("utf-8")) > 2_000_000:
                raise ProtocolError("invalid_arguments", "Invalid text")
        if action in ("write_file", "read_file"):
            p = args["path"]
            if not isinstance(p, str) or not p or len(p) > 4096:
                raise ProtocolError("invalid_arguments", "Invalid path")
        if action == "press" and (not isinstance(args["key"], str) or not 1 <= len(args["key"]) <= 32):
            raise ProtocolError("invalid_arguments", "Invalid key")
        if action == "hotkey" and (not isinstance(args["keys"], list) or not 1 <= len(args["keys"]) <= 5 or any(not isinstance(k, str) or not 1 <= len(k) <= 32 for k in args["keys"])):
            raise ProtocolError("invalid_arguments", "Invalid hotkey")
        if action in ("click", "move") and any(type(args[k]) is not int or args[k] < 0 for k in ("x", "y")):
            raise ProtocolError("invalid_arguments", "Invalid coordinates")
        if action == "scroll" and (type(args["amount"]) is not int or not -20 <= args["amount"] <= 20):
            raise ProtocolError("invalid_arguments", "Invalid scroll")
        if target == "android" and action not in ("type_text", "click"):
            raise ProtocolError("unsupported_target_action", "Not yet implemented on Android")
        return cls(cid, target, action, dict(args))

    def legacy_action(self):
        return {"action": self.action, **self.arguments}

    def fingerprint(self):
        payload = {"target": self.target, "action": self.action, "arguments": self.arguments}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def receipt(command_id, status, code=None, detail=None):
    if status not in ("accepted", "completed", "failed", "rejected"):
        raise ValueError("Invalid status")
    return {"protocol_version": VERSION, "command_id": command_id, "status": status,
            "error_code": code, "detail": detail}
