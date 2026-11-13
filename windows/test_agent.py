import unittest
from unittest.mock import Mock
from agent import execute
from unittest.mock import patch


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.driver = Mock()
        self.driver.KEYBOARD_KEYS = ["ctrl", "s", "enter"]
        self.driver.size.return_value = (1920, 1080)

    def test_type(self):
        with patch("keyboard.type_exact", return_value={"method": "clipboard_paste", "characters": 5}) as typing:
            execute({"action": "type_text", "text": "hello"}, self.driver)
            typing.assert_called_once_with("hello", self.driver, None)

    def test_click(self):
        execute({"action": "click", "x": 10, "y": 20}, self.driver)
        self.driver.click.assert_called_once_with(x=10, y=20)

    def test_hotkey(self):
        execute({"action": "hotkey", "keys": ["ctrl", "s"]}, self.driver)
        self.driver.hotkey.assert_called_once_with("ctrl", "s")

    def test_out_of_bounds(self):
        with self.assertRaises(ValueError):
            execute({"action": "click", "x": 5000, "y": 20}, self.driver)

    def test_unknown(self):
        with self.assertRaises(ValueError):
            execute({"action": "shell", "command": "whoami"}, self.driver)


if __name__ == "__main__":
    unittest.main()
