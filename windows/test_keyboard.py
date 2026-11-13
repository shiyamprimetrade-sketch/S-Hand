import unittest
from unittest.mock import Mock, patch
import keyboard

class KeyboardTests(unittest.TestCase):
    def test_invalid_text(self):
        with self.assertRaises(ValueError):
            keyboard.type_exact(None, Mock())
    def test_large_text(self):
        with self.assertRaises(ValueError):
            keyboard.type_exact("a" * 2_000_001, Mock())
    def test_empty_text_no_action(self):
        result = keyboard.type_exact("", Mock())
        self.assertEqual(result["characters"], 0)
    def test_wrong_window_rejected(self):
        with patch.object(keyboard, "active_window_title", return_value="Calculator"):
            with self.assertRaises(keyboard.KeyboardError):
                keyboard.check_focus("Notepad")
    def test_correct_window(self):
        with patch.object(keyboard, "active_window_title", return_value="main.py - Visual Studio Code"):
            keyboard.check_focus("Visual Studio Code")
    def test_non_windows_rejected(self):
        with patch.object(keyboard.os, "name", "posix"):
            with self.assertRaises(keyboard.KeyboardError):
                keyboard.type_exact("hello", Mock())

if __name__ == "__main__":
    unittest.main()
