"""Unit tests for Esup-Pod dressing utilities."""

import unittest
from ..encoding_utils import get_dressing_position_value


class EncodingUtilitiesTests(unittest.TestCase):
    """TestCase for Esup-Pod encoding utilities."""

    def test_dressing_position_value(self) -> None:
        """Test for the get_position_value function."""
        result = get_dressing_position_value("top_right", "720")
        self.assertEqual(result, "overlay=main_w-overlay_w-36.0:36.0")

        result = get_dressing_position_value("top_left", "720")
        self.assertEqual(result, "overlay=36.0:36.0")

        result = get_dressing_position_value("bottom_right", "720")
        self.assertEqual(result, "overlay=main_w-overlay_w-36.0:main_h-overlay_h-36.0")

        result = get_dressing_position_value("bottom_left", "720")
        self.assertEqual(result, "overlay=36.0:main_h-overlay_h-36.0")

        print(" ---> get_dressing_position_value: OK! --- EncodginUtilsTest")
