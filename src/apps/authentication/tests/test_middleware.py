"""
Esup-Pod - Tests for IP Restriction Middleware.

This module validates the behavior of the IPRestrictionMiddleware, ensuring that
superuser access is only granted from allowed IP ranges and that restricted
superusers are properly flagged.
"""

from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model

from ..IPRestrictionMiddleware import IPRestrictionMiddleware, ip_in_allowed_range

User = get_user_model()


class IPRestrictionMiddlewareTests(TestCase):
    """
    Test suite for IPRestrictionMiddleware and its helper functions.
    """

    def setUp(self):
        """
        Initializes the request factory, middleware, and test users.
        """
        self.factory = RequestFactory()
        self.get_response = lambda request: None
        self.middleware = IPRestrictionMiddleware(self.get_response)

        self.user = User.objects.create_user(username="normaluser", password="password")
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@test.local", password="password"
        )

    def test_ip_in_allowed_range_no_setting(self):
        """
        Tests that any IP is allowed if the ALLOWED_SUPERUSER_IPS setting is empty.
        """
        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.auth_settings"
        ) as mock_auth_settings:
            mock_auth_settings.allowed_superuser_ips = []
            self.assertTrue(ip_in_allowed_range("192.168.1.1"))

    def test_ip_in_allowed_range_empty_values(self):
        """
        Tests that any IP is allowed if ALLOWED_SUPERUSER_IPS contains only empty/whitespace values.
        """
        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.auth_settings"
        ) as mock_auth_settings:
            mock_auth_settings.allowed_superuser_ips = ["", "  "]
            self.assertTrue(ip_in_allowed_range("192.168.1.1"))

    def test_ip_in_allowed_range_invalid_ip(self):
        """
        Tests that an invalid IP string results in a denial of access.
        """
        self.assertFalse(ip_in_allowed_range("invalid_ip"))

    def test_ip_in_allowed_range_allowed(self):
        """
        Tests that IPs within the configured ranges are correctly identified as allowed.
        """
        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.auth_settings"
        ) as mock_auth_settings:
            mock_auth_settings.allowed_superuser_ips = ["192.168.1.0/24", "10.0.0.1"]
            self.assertTrue(ip_in_allowed_range("192.168.1.50"))
            self.assertTrue(ip_in_allowed_range("10.0.0.1"))
            self.assertFalse(ip_in_allowed_range("10.0.0.2"))

    def test_middleware_normal_user_unaffected(self):
        """
        Tests that non-superuser accounts are not affected by the IP restriction middleware.
        """
        request = self.factory.get("/")
        request.user = self.user
        request.META["REMOTE_ADDR"] = "8.8.8.8"

        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.auth_settings"
        ) as mock_auth_settings:
            mock_auth_settings.allowed_superuser_ips = ["127.0.0.1"]
            self.middleware(request)

        self.assertFalse(request.user.is_superuser)

    def test_middleware_superuser_allowed_ip(self):
        """
        Tests that a superuser accessing from an allowed IP retains their privileges.
        """
        request = self.factory.get("/")
        request.user = self.superuser
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.auth_settings"
        ) as mock_auth_settings:
            mock_auth_settings.allowed_superuser_ips = ["127.0.0.1"]
            self.middleware(request)

        self.assertTrue(request.user.is_superuser)

    def test_middleware_superuser_denied_ip(self):
        """
        Tests that a superuser accessing from a non-allowed IP has their privileges
        revoked during the request and is tagged with a warning.
        """
        request = self.factory.get("/")
        request.user = self.superuser
        request.META["REMOTE_ADDR"] = "8.8.8.8"

        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.auth_settings"
        ) as mock_auth_settings:
            mock_auth_settings.allowed_superuser_ips = ["127.0.0.1"]
            self.middleware(request)

        self.assertFalse(request.user.is_superuser)
        self.assertIn("(Restricted - IP 8.8.8.8 not allowed)", request.user.last_name)
