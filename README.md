# S-Hand — autonomous computer action engine

S-Hand is the **action layer** for S. S plans, S-Eye observes, and S-Hand executes permitted keyboard, mouse and touch actions.

## Components
- `windows/`: Windows 11 desktop agent with a loopback HTTP API and PyAutoGUI.
- `android/`: native Android AccessibilityService action engine (Kotlin).
- `protocol/`: shared action envelope.

## Windows quick start
Install Python 3.11+ and run:
```powershell
cd windows
py -m pip install -r requirements.txt
py agent.py
```
The agent binds to **127.0.0.1:8765 only**. It prints a session token. Open Notepad, focus its editing area, and send an action using the example client:
```powershell
$env:SHAND_TOKEN="PASTE_TOKEN_FROM_AGENT"
py send_example.py
```
Move the mouse to the top-left screen corner to trigger PyAutoGUI's emergency failsafe. Ctrl+C stops the server. No remote exposure is enabled.

## Android
Open `android/` in Android Studio, build/install the debug APK, then explicitly enable **S-Hand** in Android Accessibility settings. The service handles supported local action requests only after user authorization. The Android transport/UI integration is not yet complete.

## Trust boundaries
Never execute arbitrary shell commands from action payloads. Keep credentials outside Git. Do not expose the Windows HTTP receiver to the internet. Acknowledgement means the action driver returned, **not** that the desired application state was verified; S-Eye must check the outcome.

## Status
Source implementation, not a certified release. Physical Windows and Android device tests are outstanding.
