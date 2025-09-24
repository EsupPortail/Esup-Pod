"""
    Unit tests for Esup-Pod video encoding utilities.

    Run with `python manage.py test pod.video_encode_transcript.tests.EncodingUtilitiesTests`
"""

import unittest
from ..encoding_utils import get_dressing_position_value, sec_to_timestamp


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

    def test_sec_to_timestamp(self) -> None:
        """Test sec_to_timestamp return values."""
        self.assertEqual(sec_to_timestamp(-1), "00:00:00.000")
        self.assertEqual(sec_to_timestamp(60.000), "00:01:00.000")
        print(" ---> sec_to_timestamp: OK! --- EncodginUtilsTest")
