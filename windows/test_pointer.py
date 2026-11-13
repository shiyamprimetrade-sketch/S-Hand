import unittest
from unittest.mock import Mock
from pointer import click, move, scroll, drag, PointerError

class PointerTests(unittest.TestCase):
    def setUp(self):
        self.driver = Mock()
        self.driver.size.return_value = (1920, 1080)

    def test_click(self):
        click(self.driver, 10, 20)
        self.driver.click.assert_called_once_with(x=10, y=20, clicks=1, interval=0)

    def test_bounds(self):
        with self.assertRaises(PointerError):
            move(self.driver, 1920, 20)

    def test_boolean_coordinates(self):
        with self.assertRaises(PointerError):
            click(self.driver, True, 2)

    def test_scroll(self):
        scroll(self.driver, -3)
        self.driver.scroll.assert_called_once_with(-3)

    def test_cancelled_click(self):
        with self.assertRaises(RuntimeError):
            click(self.driver, 1, 2, is_armed=lambda: False)
        self.driver.click.assert_not_called()

    def test_drag_releases_button(self):
        drag(self.driver, 1, 2, 50, 60, steps=4)
        self.driver.mouseDown.assert_called_once()
        self.driver.mouseUp.assert_called_once()
        self.assertEqual(self.driver.moveTo.call_args.args, (50, 60))

    def test_drag_cancel_releases_button(self):
        states = iter([True, True, True, False])
        with self.assertRaises(RuntimeError):
            drag(self.driver, 1, 2, 50, 60, steps=4, is_armed=lambda: next(states))
        self.driver.mouseUp.assert_called_once()

    def test_drag_releases_after_driver_error(self):
        self.driver.moveTo.side_effect = [None, RuntimeError("failure")]
        with self.assertRaises(RuntimeError):
            drag(self.driver, 1, 2, 50, 60, steps=4)
        self.driver.mouseUp.assert_called_once()

if __name__ == "__main__":
    unittest.main()
