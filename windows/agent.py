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
from protocol import Command, ProtocolError, receipt
from journal import Journal
JOURNAL = Journal(os.environ.get('SHAND_JOURNAL', 'shand-commands.sqlite3'))


def execute(action, driver):
    if not isinstance(action, dict):
        raise ValueError("Action must be an object")
    name = action.get("action")
    if name == "type_text":
        value = action.get("text")
        if not isinstance(value, str) or len(value) > 100000:
            raise ValueError("Invalid text")
        driver.write(value, interval=0.001)
    elif name == "press":
        key = action.get("key")
        if not isinstance(key, str) or key not in driver.KEYBOARD_KEYS:
            raise ValueError("Unsupported key")
        driver.press(key)
    elif name == "hotkey":
        keys = action.get("keys")
        if not isinstance(keys, list) or not 1 <= len(keys) <= 5 or any(
            not isinstance(k, str) or k not in driver.KEYBOARD_KEYS for k in keys
        ):
            raise ValueError("Invalid shortcut")
        driver.hotkey(*keys)
    elif name in ("click", "move"):
        x, y = action.get("x"), action.get("y")
        width, height = driver.size()
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (x, y)) or not (0 <= x < width and 0 <= y < height):
            raise ValueError("Coordinates outside display")
        if name == "click":
            driver.click(x=x, y=y)
        else:
            driver.moveTo(x=x, y=y)
    elif name == "scroll":
        amount = action.get("amount")
        if not isinstance(amount, int) or isinstance(amount, bool) or not -20 <= amount <= 20:
            raise ValueError("Invalid scroll amount")
        driver.scroll(amount)
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
        if self.path != "/action":
            return self.respond(404, {"ok": False, "error": "Unknown route"})
        provided = self.headers.get("X-S-Hand-Token", "")
        if not secrets.compare_digest(provided, TOKEN):
            return self.respond(401, {"ok": False, "error": "Unauthorized"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= MAX_BODY:
                return self.respond(413, {"ok": False, "error": "Invalid body size"})
            payload = json.loads(self.rfile.read(size))
            command = None
            if "protocol_version" in payload or "command_id" in payload:
                command = Command.parse(payload)
                if command.target != "windows":
                    raise ProtocolError("invalid_target", "Windows agent cannot execute Android actions")
                payload = command.legacy_action()
            if command is not None:
                replay_state = JOURNAL.reserve(command)
                if replay_state != "new":
                    return self.respond(409, receipt(command.command_id, "rejected", "duplicate_command" if replay_state == "duplicate" else "command_id_conflict"))
            if payload.get("action") in ("write_file", "read_file"):
                if not WORKSPACE_ROOT:
                    raise ValueError("Set SHAND_WORKSPACE to enable file operations")
                from workspace import Workspace, WorkspaceError
                workspace = Workspace(WORKSPACE_ROOT)
                with LOCK:
                    if payload["action"] == "write_file":
                        result = workspace.write(payload.get("path"), payload.get("text"))
                    else:
                        result = workspace.read(payload.get("path"))
            else:
                import pyautogui
                pyautogui.FAILSAFE = True
                with LOCK:
                    result = execute(payload, pyautogui)
            if command is not None:
                JOURNAL.finish(command.command_id, "completed")
            return self.respond(200, receipt(command.command_id, "completed") if command is not None else result)
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
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
