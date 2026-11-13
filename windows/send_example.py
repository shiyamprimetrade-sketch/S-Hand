"""Send a versioned action to the focused Windows editor."""
import json
import os
import uuid
import urllib.request

token = os.environ.get("SHAND_TOKEN")
if not token:
    raise SystemExit("Set SHAND_TOKEN to the token printed by agent.py")
command = {
    "protocol_version": "1.0",
    "command_id": str(uuid.uuid4()),
    "target": "windows",
    "action": "type_text",
    "arguments": {"text": "print('Hello from S-Hand')"},
}
request = urllib.request.Request(
    "http://127.0.0.1:8765/action",
    data=json.dumps(command).encode("utf-8"),
    headers={"Content-Type": "application/json", "X-S-Hand-Token": token},
)
with urllib.request.urlopen(request, timeout=10) as response:
    print(response.read().decode("utf-8"))
