"""S-Hand Windows local action receiver. Never bind to public interfaces."""
import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY = 2_200_000
WORKSPACE_ROOT = os.environ.get('SHAND_WORKSPACE')
TOKEN = os.environ.get("SHAND_TOKEN") or secrets.token_urlsafe(32)
LOCK = threading.Lock()
ARMED = threading.Event()
# Explicit opt-in required before any input or filesystem mutation.
if os.environ.get("SHAND_ARMED") == "1":
    ARMED.set()
from protocol import Command, ProtocolError, receipt
from journal import Journal
JOURNAL = Journal(os.environ.get('SHAND_JOURNAL', 'shand-commands.sqlite3'))


def execute(action, driver, is_armed=lambda: True):
    if not isinstance(action, dict):
        raise ValueError("Action must be an object")
    name = action.get("action")
    if name == "type_text":
        value = action.get("text")
        if not isinstance(value, str) or len(value) > 100000:
            raise ValueError("Invalid text")
        from keyboard import type_exact
        return {"ok": True, "action": name, **type_exact(value, driver, action.get("expected_window"))}
    elif name == "press":
        from key_actions import press_key
        press_key(driver, action.get("key"))
    elif name == "hotkey":
        from key_actions import chord
        chord(driver, action.get("keys"), is_armed=is_armed)
    elif name in ("click", "move", "scroll", "drag"):
        import pointer
        if name == "click":
            result = pointer.click(driver, action.get("x"), action.get("y"), is_armed=is_armed)
        elif name == "move":
            result = pointer.move(driver, action.get("x"), action.get("y"), is_armed=is_armed)
        elif name == "scroll":
            result = pointer.scroll(driver, action.get("amount"), is_armed=is_armed)
        else:
            result = pointer.drag(driver, action.get("x1"), action.get("y1"),
                                  action.get("x2"), action.get("y2"), is_armed=is_armed)
        return {"ok": True, "action": name, **result}
    else:
        raise ValueError("Unsupported action")
    return {"ok": True, "action": name}


class Handler(BaseHTTPRequestHandler):
    def respond(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path not in ("/action", "/stop"):
            return self.respond(404, {"ok": False, "error": "Unknown route"})
        provided = self.headers.get("X-S-Hand-Token", "")
        if not secrets.compare_digest(provided, TOKEN):
            return self.respond(401, {"ok": False, "error": "Unauthorized"})
        if self.path == "/stop":
            ARMED.clear()
            return self.respond(200, {"ok": True, "armed": False})
        if not ARMED.is_set():
            return self.respond(423, {"ok": False, "error": "S-Hand disarmed; set SHAND_ARMED=1 at startup"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= MAX_BODY:
                return self.respond(413, {"ok": False, "error": "Invalid body size"})
            payload = json.loads(self.rfile.read(size))
            command = None
            command = Command.parse(payload)
            if command.target != "windows":
                raise ProtocolError("invalid_target", "Windows agent cannot execute Android actions")
            payload = command.legacy_action()
            replay_state = JOURNAL.reserve(command)
            if replay_state != "new":
                return self.respond(409, receipt(command.command_id, "rejected", "duplicate_command" if replay_state == "duplicate" else "command_id_conflict"))
            if not ARMED.is_set():
                raise RuntimeError("Emergency stop activated")
            if payload.get("action") in ("write_file", "read_file"):
                if not WORKSPACE_ROOT:
                    raise ValueError("Set SHAND_WORKSPACE to enable file operations")
                from workspace import Workspace, WorkspaceError
                workspace = Workspace(WORKSPACE_ROOT)
                with LOCK:
                    if not ARMED.is_set():
                        raise RuntimeError("Emergency stop activated")
                    if payload["action"] == "write_file":
                        result = workspace.write(payload.get("path"), payload.get("text"))
                    else:
                        result = workspace.read(payload.get("path"))
            else:
                import pyautogui
                pyautogui.FAILSAFE = True
                with LOCK:
                    if not ARMED.is_set():
                        raise RuntimeError("Emergency stop activated")
                    result = execute(payload, pyautogui, is_armed=ARMED.is_set)
            JOURNAL.finish(command.command_id, "completed")
            return self.respond(200, receipt(command.command_id, "completed", detail=result))
        except ProtocolError as exc:
            return self.respond(400, receipt("unknown", "rejected", exc.code, str(exc)))
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            if "command" in locals() and command is not None and "replay_state" in locals() and replay_state == "new":
                JOURNAL.finish(command.command_id, "failed", str(exc))
            return self.respond(400, {"ok": False, "error": str(exc)})
        except Exception as exc:
            if "command" in locals() and command is not None and "replay_state" in locals() and replay_state == "new":
                JOURNAL.finish(command.command_id, "failed", type(exc).__name__)
            return self.respond(500, {"ok": False, "error": type(exc).__name__})

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print("S-Hand token:", TOKEN, flush=True)
    print("Listening at http://127.0.0.1:8765", flush=True)
    print("Armed:", ARMED.is_set(), flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
