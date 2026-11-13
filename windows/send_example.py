"""Send one real typing action to the focused Windows application."""
import json
import os
import urllib.request

token = os.environ.get("SHAND_TOKEN")
if not token:
    raise SystemExit("Set SHAND_TOKEN to the token printed by agent.py")
payload = json.dumps({"action": "type_text", "text": "print('Hello from S-Hand')"}).encode()
request = urllib.request.Request(
    "http://127.0.0.1:8765/action",
    data=payload,
    headers={"Content-Type": "application/json", "X-S-Hand-Token": token},
)
with urllib.request.urlopen(request, timeout=10) as response:
    print(response.read().decode())
