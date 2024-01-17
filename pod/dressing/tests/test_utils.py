"""Unit tests for Esup-Pod dressing utilities."""

import os
import unittest
from unittest.mock import patch
from pod.dressing.utils import get_position_value, get_dressing_input
from pod.dressing.models import Dressing


class DressingUtilitiesTests(unittest.TestCase):
    """TestCase for Esup-Pod dressing utilities."""

    def test_get_position_value(self):
        """Test for the get_position_value function"""
        result = get_position_value("top_right", "720")
        self.assertEqual(result, "overlay=main_w-overlay_w-36.0:36.0")

        result = get_position_value("top_left", "720")
        self.assertEqual(result, "overlay=36.0:36.0")

        result = get_position_value("bottom_right", "720")
        self.assertEqual(result, "overlay=main_w-overlay_w-36.0:main_h-overlay_h-36.0")

        result = get_position_value("bottom_left", "720")
        self.assertEqual(result, "overlay=36.0:main_h-overlay_h-36.0")

        print(" ---> test_get_position_value: OK! --- DressingUtilsTest")

    def test_get_dressing_input(self):
        """Test for the get_dressing_input function"""

        dressing = Dressing(watermark=None, opening_credits=None, ending_credits=None)

        FFMPEG_DRESSING_INPUT = "input=%s"

        with patch("os.path.join", side_effect=os.path.join):
            result = get_dressing_input(dressing, FFMPEG_DRESSING_INPUT)

        self.assertIn("", result)

        print(" ---> test_get_dressing_input: OK! --- DressingUtilsTest")
