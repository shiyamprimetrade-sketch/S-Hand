import unittest
from unittest.mock import Mock
from key_actions import chord, press_key, KeyActionError

class KeyActionTests(unittest.TestCase):
    def test_chord_order(self):
        driver = Mock()
        self.assertEqual(chord(driver, ["ctrl", "shift", "s"])["keys"], ["ctrl", "shift", "s"])
        self.assertEqual([c.args[0] for c in driver.keyDown.call_args_list], ["ctrl", "shift", "s"])
        self.assertEqual([c.args[0] for c in driver.keyUp.call_args_list], ["s", "shift", "ctrl"])

    def test_release_after_failure(self):
        driver = Mock()
        def fail_on_s(key):
            if key == "s":
                raise RuntimeError("driver failure")
        driver.keyDown.side_effect = fail_on_s
        with self.assertRaises(RuntimeError):
            chord(driver, ["ctrl", "s"])
        driver.keyUp.assert_called_once_with("ctrl")

    def test_emergency_stop_releases_held_modifier(self):
        driver = Mock()
        checks = iter([True, False])
        with self.assertRaises(RuntimeError):
            chord(driver, ["ctrl", "s"], is_armed=lambda: next(checks))
        driver.keyDown.assert_called_once_with("ctrl")
        driver.keyUp.assert_called_once_with("ctrl")

    def test_reject_duplicates(self):
        with self.assertRaises(KeyActionError):
            chord(Mock(), ["ctrl", "ctrl", "s"])

    def test_reject_invalid_order(self):
        with self.assertRaises(KeyActionError):
            chord(Mock(), ["s", "ctrl"])

    def test_reject_unknown_key(self):
        with self.assertRaises(KeyActionError):
            press_key(Mock(), "not-a-key")

    def test_press(self):
        driver = Mock()
        press_key(driver, "enter")
        driver.press.assert_called_once_with("enter")

if __name__ == "__main__":
    unittest.main()
