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
        with mock.patch(
            "src.apps.utils.conf.DjangoSettingsSource.__call__",
            return_value={},
        ):
            with mock.patch.dict(os.environ, {"USE_STATS_VIEW": "True"}):
                config = VideoConfig()
                self.assertTrue(config.use_stats_view)

        with mock.patch(
            "src.apps.utils.conf.DjangoSettingsSource.__call__",
            return_value={},
        ):
            with mock.patch.dict(os.environ, {"USE_STATS_VIEW": "False"}):
                config = VideoConfig()
                self.assertFalse(config.use_stats_view)

    def test_default_values(self):
        """Test default values when env vars are not set."""
        with mock.patch.dict(os.environ):
            if "HIDE_USER_FILTER" in os.environ:
                del os.environ["HIDE_USER_FILTER"]

            config = VideoConfig()
            self.assertFalse(config.hide_user_filter)
