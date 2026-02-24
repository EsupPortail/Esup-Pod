import os
from unittest import mock
from django.test import SimpleTestCase
from src.apps.video.conf import VideoConfig


class VideoSettingsTests(SimpleTestCase):
    def test_load_from_env(self):
        """Test that VideoConfig loads values from environment variables."""
        # Case 1: Set to True
        with mock.patch.dict(os.environ, {"POD_VIDEO_USE_STATS_VIEW": "True"}):
            config = VideoConfig()
            self.assertTrue(config.use_stats_view)

        # Case 2: Set to False
        with mock.patch.dict(os.environ, {"POD_VIDEO_USE_STATS_VIEW": "False"}):
            config = VideoConfig()
            self.assertFalse(config.use_stats_view)

    def test_default_values(self):
        """Test default values when env vars are not set."""
        # Ensure env var is NOT set
        with mock.patch.dict(os.environ):
            if "POD_VIDEO_HIDE_USER_FILTER" in os.environ:
                del os.environ["POD_VIDEO_HIDE_USER_FILTER"]

            config = VideoConfig()
            # Default value as per src/apps/video/conf.py is False
            self.assertFalse(config.hide_user_filter)
