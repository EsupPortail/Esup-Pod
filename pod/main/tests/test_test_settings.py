"""Regression tests for Elasticsearch connection settings in test mode."""

from copy import deepcopy
from pathlib import Path
import runpy
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

import pod.custom
from pod import settings as base_settings


class ElasticsearchTestSettingsTests(SimpleTestCase):
    """Keep authentication and TLS options when loading test settings."""

    def load_test_settings(self, local_settings=None):
        """Execute test settings with isolated configuration and no HTTP request."""
        local_module = SimpleNamespace(USE_DOCKER=False, **(local_settings or {}))
        response = SimpleNamespace(
            text=(
                '<html><body><input id="input-custom-server-salt" '
                'value="test-secret"></body></html>'
            )
        )

        def path_exists(path):
            if path == "pod/custom/settings_local.py":
                return local_settings is not None
            # Treat the migration directory as present to prevent filesystem writes.
            return True

        with (
            patch.object(base_settings, "INSTALLED_APPS", []),
            patch.object(base_settings, "TEMPLATES", deepcopy(base_settings.TEMPLATES)),
            patch.object(pod.custom, "settings_local", local_module, create=True),
            patch("os.path.exists", side_effect=path_exists),
            patch("requests.get", return_value=response),
        ):
            return runpy.run_path(
                str(Path(__file__).resolve().parents[1] / "test_settings.py"),
                run_name="pod.main._test_settings_regression",
            )

    def test_preserves_local_elasticsearch_options(self):
        """Credentials and TLS settings must accompany the local server URL."""
        options = {
            "basic_auth": ("test-user", "test-password"),
            "verify_certs": False,
        }
        loaded = self.load_test_settings(
            {"ES_URL": ["https://search.example.invalid:9200"], "ES_OPTIONS": options}
        )

        self.assertEqual(loaded["ES_URL"], ["https://search.example.invalid:9200"])
        self.assertEqual(loaded["ES_OPTIONS"], options)

    def test_defaults_to_empty_options_when_local_option_is_absent(self):
        """Local configurations without authentication keep the client defaults."""
        loaded = self.load_test_settings({})

        self.assertEqual(loaded["ES_OPTIONS"], {})

    def test_defaults_to_empty_options_without_local_settings(self):
        """The CI configuration works without a settings_local.py file."""
        loaded = self.load_test_settings()

        self.assertEqual(loaded["ES_OPTIONS"], {})
