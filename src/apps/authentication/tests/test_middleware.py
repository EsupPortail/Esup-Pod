from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model

from ..IPRestrictionMiddleware import IPRestrictionMiddleware, ip_in_allowed_range

User = get_user_model()


class IPRestrictionMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.get_response = lambda request: None
        self.middleware = IPRestrictionMiddleware(self.get_response)

        self.user = User.objects.create_user(username="normaluser", password="password")
        self.superuser = User.objects.create_superuser(
            username="admin", email="admin@test.local", password="password"
        )

    def test_ip_in_allowed_range_no_setting(self):
        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.settings"
        ) as mock_settings:
            mock_settings.ALLOWED_SUPERUSER_IPS = []
            self.assertTrue(ip_in_allowed_range("192.168.1.1"))

    def test_ip_in_allowed_range_invalid_ip(self):
        self.assertFalse(ip_in_allowed_range("invalid_ip"))

    def test_ip_in_allowed_range_allowed(self):
        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.settings"
        ) as mock_settings:
            mock_settings.ALLOWED_SUPERUSER_IPS = ["192.168.1.0/24", "10.0.0.1"]
            self.assertTrue(ip_in_allowed_range("192.168.1.50"))
            self.assertTrue(ip_in_allowed_range("10.0.0.1"))
            self.assertFalse(ip_in_allowed_range("10.0.0.2"))

    def test_middleware_normal_user_unaffected(self):
        request = self.factory.get("/")
        request.user = self.user
        request.META["REMOTE_ADDR"] = "8.8.8.8"

        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.settings"
        ) as mock_settings:
            mock_settings.ALLOWED_SUPERUSER_IPS = ["127.0.0.1"]
            self.middleware(request)

        self.assertFalse(request.user.is_superuser)

    def test_middleware_superuser_allowed_ip(self):
        request = self.factory.get("/")
        request.user = self.superuser
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.settings"
        ) as mock_settings:
            mock_settings.ALLOWED_SUPERUSER_IPS = ["127.0.0.1"]
            self.middleware(request)

        self.assertTrue(request.user.is_superuser)

    def test_middleware_superuser_denied_ip(self):
        request = self.factory.get("/")
        request.user = self.superuser
        request.META["REMOTE_ADDR"] = "8.8.8.8"

        with patch(
            "src.apps.authentication.IPRestrictionMiddleware.settings"
        ) as mock_settings:
            mock_settings.ALLOWED_SUPERUSER_IPS = ["127.0.0.1"]
            self.middleware(request)

        self.assertFalse(request.user.is_superuser)
        self.assertIn("(Restricted - IP 8.8.8.8 not allowed)", request.user.last_name)
