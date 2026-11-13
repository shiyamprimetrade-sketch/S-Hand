"""Windows keyboard actions with exact Unicode clipboard paste and focus guards."""
import ctypes
import os
import time

class KeyboardError(RuntimeError):
    pass

def active_window_title():
    if os.name != "nt":
        raise KeyboardError("Windows focus API is unavailable")
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        raise KeyboardError("No foreground window")
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value

def check_focus(expected_title):
    if expected_title is None:
        return
    if not isinstance(expected_title, str) or not expected_title.strip():
        raise ValueError("Invalid expected window title")
    actual = active_window_title()
    if expected_title.casefold() not in actual.casefold():
        raise KeyboardError("Foreground window does not match requested target")

def type_exact(text, driver, expected_title=None):
    """Paste exact UTF-8/Unicode text through Windows clipboard; restore prior text if possible."""
    if not isinstance(text, str) or len(text.encode("utf-8")) > 2_000_000:
        raise ValueError("Invalid text")
    check_focus(expected_title)
    if not text:
        return {"method": "noop", "characters": 0}
    if os.name != "nt":
        raise KeyboardError("Exact paste requires Windows")
    import ctypes.wintypes
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    CF_UNICODETEXT, GMEM_MOVEABLE = 13, 0x0002
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.GetClipboardData.argtypes = [ctypes.c_uint]
    user32.GetClipboardData.restype = ctypes.c_void_p
    previous = None
    for attempt in range(5):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        raise KeyboardError("Clipboard is busy")
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if handle:
            pointer = kernel32.GlobalLock(handle)
            if pointer:
                try:
                    previous = ctypes.wstring_at(pointer)
                finally:
                    kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()

    def set_clipboard(value):
        data = ctypes.create_unicode_buffer(value)
        size = ctypes.sizeof(data)
        memory = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
        if not memory:
            raise KeyboardError("Clipboard allocation failed")
        pointer = kernel32.GlobalLock(memory)
        if not pointer:
            kernel32.GlobalFree(memory)
            raise KeyboardError("Clipboard lock failed")
        ctypes.memmove(pointer, ctypes.addressof(data), size)
        kernel32.GlobalUnlock(memory)
        if not user32.OpenClipboard(None):
            kernel32.GlobalFree(memory)
            raise KeyboardError("Clipboard unavailable")
        try:
            if not user32.EmptyClipboard() or not user32.SetClipboardData(CF_UNICODETEXT, memory):
                kernel32.GlobalFree(memory)
                raise KeyboardError("Clipboard update failed")
        finally:
            user32.CloseClipboard()

    set_clipboard(text)
    try:
        check_focus(expected_title)
        driver.hotkey("ctrl", "v")
        time.sleep(0.15)
    finally:
        if previous is not None:
            try:
                set_clipboard(previous)
            except KeyboardError:
                pass
    return {"method": "clipboard_paste", "characters": len(text)}
