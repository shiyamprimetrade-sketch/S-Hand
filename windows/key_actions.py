"""Safe keyboard shortcut execution with guaranteed modifier release."""

class KeyActionError(ValueError):
    pass

# Conservative default. Add keys only after platform testing.
ALLOWED = frozenset({
    "ctrl", "alt", "shift", "win", "enter", "esc", "tab", "space",
    "backspace", "delete", "up", "down", "left", "right",
    "home", "end", "pageup", "pagedown",
    "a", "c", "v", "x", "z", "y", "s", "f", "n", "o", "p",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"
})
MODIFIERS = frozenset({"ctrl", "alt", "shift", "win"})

def validate_keys(keys):
    if not isinstance(keys, (list, tuple)) or not 1 <= len(keys) <= 5:
        raise KeyActionError("Expected 1 to 5 keys")
    if any(not isinstance(key, str) or key not in ALLOWED for key in keys):
        raise KeyActionError("Unsupported key")
    if len(set(keys)) != len(keys):
        raise KeyActionError("Duplicate keys forbidden")
    if len(keys) > 1 and any(key not in MODIFIERS for key in keys[:-1]):
        raise KeyActionError("Only modifiers may precede the final key")
    return tuple(keys)

def press_key(driver, key):
    validate_keys([key])
    driver.press(key)
    return {"key": key}

def chord(driver, keys, is_armed=lambda: True):
    keys = validate_keys(keys)
    pressed = []
    try:
        for key in keys:
            if not is_armed():
                raise RuntimeError('Emergency stop activated')
            driver.keyDown(key)
            pressed.append(key)
    finally:
        for key in reversed(pressed):
            driver.keyUp(key)
    return {"keys": list(keys)}
