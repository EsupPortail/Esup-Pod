import os
from unittest import mock
from django.test import SimpleTestCase
from src.apps.video.conf import VideoConfig


class VideoConfigTests(SimpleTestCase):
    def test_load_from_env(self):
        """Test that VideoConfig loads values from environment variables."""
        # Case 1: Set to True
        with mock.patch.dict(os.environ, {"POD_VIDEO_HIDE_USER_FILTER": "True"}):
            config = VideoConfig()
            self.assertTrue(config.hide_user_filter)

        # Case 2: Set to False
        with mock.patch.dict(os.environ, {"POD_VIDEO_HIDE_USER_FILTER": "False"}):
            config = VideoConfig()
            self.assertFalse(config.hide_user_filter)

    def test_default_values(self):
        """Test default values when env vars are not set."""
        # Ensure env var is NOT set
        with mock.patch.dict(os.environ):
            if "POD_VIDEO_HIDE_USER_FILTER" in os.environ:
                del os.environ["POD_VIDEO_HIDE_USER_FILTER"]

            config = VideoConfig()
            # Default value as per src/apps/video/conf.py is False
            self.assertFalse(config.hide_user_filter)

    def test_integer_conversion(self):
        """Test automatic conversion of types (int)."""
        with mock.patch.dict(os.environ, {"POD_VIDEO_MAX_UPLOAD_SIZE_GB": "10"}):
            config = VideoConfig()
            self.assertEqual(config.max_upload_size_gb, 10)
