"""
Esup-Pod - Tests for authentication scenarios and configuration switching.

This module contains tests that verify how different authentication settings
(CAS vs Local Auth) impact URL routing and available views.
"""

import sys
from importlib import reload
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.test import TestCase
from django.urls import clear_url_caches, resolve
from django_cas_ng import views as cas_views

from src.apps.authentication.conf import auth_settings


def reload_urlconf():
    """
    Reloads URL configurations after a settings change to ensure that changes
    to conditional URL patterns are correctly applied during tests.
    """
    clear_url_caches()
    auth_urls_module = "src.apps.authentication.urls"
    config_urls_module = settings.ROOT_URLCONF

    for mod in [auth_urls_module, config_urls_module]:
        if mod in sys.modules:
            reload(sys.modules[mod])


class AuthenticationScenariosTests(TestCase):
    """
    Test suite for verifying that URL routing adapts correctly to authentication
    configuration flags.
    """

    def tearDown(self):
        """
        Cleans up URL caches and reloads the URL configuration after each test.
        """
        reload_urlconf()

    @patch.object(auth_settings, "use_cas", True)
    @patch.object(auth_settings, "use_local_auth", False)
    def test_cas_only_mode(self):
        """
        Scenario: University / Production Mode
        - CAS is Enabled
        - Local Auth is Disabled

        Expectation:
        - /accounts/login resolves to CAS login view
        """
        reload_urlconf()

        resolver_match = resolve("/accounts/login")
        self.assertEqual(resolver_match.func.view_class, cas_views.LoginView)

        resolver_match_logout = resolve("/accounts/logout")
        self.assertEqual(resolver_match_logout.func.view_class, cas_views.LogoutView)

    @patch.object(auth_settings, "use_cas", False)
    @patch.object(auth_settings, "use_local_auth", True)
    def test_local_mode_default(self):
        """
        Scenario: Local Development Mode
        - CAS is Disabled
        - Local Auth is Enabled

        Expectation:
        - /accounts/login resolves to Django standard LoginView
        """
        reload_urlconf()

        resolver_match = resolve("/accounts/login")
        self.assertEqual(resolver_match.func.view_class, auth_views.LoginView)

        resolver_match_logout = resolve("/accounts/logout")
        self.assertEqual(resolver_match_logout.func.view_class, auth_views.LogoutView)
