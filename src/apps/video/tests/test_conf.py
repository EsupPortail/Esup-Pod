import os
from unittest import mock

from django.test import SimpleTestCase

from src.apps.video.conf import VideoConfig


class VideoSettingsTests(SimpleTestCase):
    def test_load_from_env(self):
        """
        Test that VideoConfig reads env vars correctly when Django settings
        do not override the value.

        VideoConfig uses DjangoSettingsSource which can shadow env vars if
        the setting is defined in Django settings. We patch the source to
        isolate the env-reading behavior.
        """
        # Case 1: Set to True — we bypass DjangoSettingsSource by patching it
        # to return nothing, so only env_settings contributes.
        with mock.patch(
            "src.apps.utils.conf.DjangoSettingsSource.__call__",
            return_value={},
        ):
            with mock.patch.dict(os.environ, {"USE_STATS_VIEW": "True"}):
                config = VideoConfig()
                self.assertTrue(config.use_stats_view)

        # Case 2: Set to False
        with mock.patch(
            "src.apps.utils.conf.DjangoSettingsSource.__call__",
            return_value={},
        ):
            with mock.patch.dict(os.environ, {"USE_STATS_VIEW": "False"}):
                config = VideoConfig()
                self.assertFalse(config.use_stats_view)

    def test_default_values(self):
        """Test default values when env vars are not set."""
        # Ensure env var is NOT set
        with mock.patch.dict(os.environ):
            if "HIDE_USER_FILTER" in os.environ:
                del os.environ["HIDE_USER_FILTER"]

            config = VideoConfig()
            # Default value as per src/apps/video/conf.py is False
            self.assertFalse(config.hide_user_filter)
