"""Bounded mouse operations; check cancellation before every input event."""

class PointerError(ValueError):
    pass

def point(driver, x, y):
    if type(x) is not int or type(y) is not int:
        raise PointerError("Coordinates must be integers")
    width, height = driver.size()
    if not 0 <= x < width or not 0 <= y < height:
        raise PointerError("Coordinates outside primary display")
    return x, y

def ensure_armed(is_armed):
    if not is_armed():
        raise RuntimeError("Emergency stop activated")

def click(driver, x, y, is_armed=lambda: True, count=1):
    point(driver, x, y)
    if type(count) is not int or not 1 <= count <= 2:
        raise PointerError("Click count must be 1 or 2")
    ensure_armed(is_armed)
    driver.click(x=x, y=y, clicks=count, interval=0.12 if count == 2 else 0)
    return {"x": x, "y": y, "clicks": count}

def move(driver, x, y, is_armed=lambda: True):
    point(driver, x, y)
    ensure_armed(is_armed)
    driver.moveTo(x=x, y=y)
    return {"x": x, "y": y}

def scroll(driver, amount, is_armed=lambda: True):
    if type(amount) is not int or not -20 <= amount <= 20:
        raise PointerError("Scroll amount must be between -20 and 20")
    ensure_armed(is_armed)
    driver.scroll(amount)
    return {"amount": amount}

def drag(driver, x1, y1, x2, y2, is_armed=lambda: True, steps=12):
    point(driver, x1, y1)
    point(driver, x2, y2)
    if type(steps) is not int or not 2 <= steps <= 50:
        raise PointerError("Invalid drag step count")
    ensure_armed(is_armed)
    driver.moveTo(x1, y1)
    down_attempted = False
    try:
        ensure_armed(is_armed)
        down_attempted = True
        driver.mouseDown()
        for i in range(1, steps + 1):
            ensure_armed(is_armed)
            ratio = i / steps
            x = round(x1 + (x2 - x1) * ratio)
            y = round(y1 + (y2 - y1) * ratio)
            driver.moveTo(x, y)
    finally:
        if down_attempted:
            driver.mouseUp()
    return {"from": [x1, y1], "to": [x2, y2], "steps": steps}
