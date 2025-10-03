"""
Esup-Pod IP Restriction Middleware test cases.

Run tests with:
    python manage.py test pod.authentication.tests.test_IPRestrictionMiddleware
"""

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from unittest import mock


def check_ip_in_allowed_range(ip, allowed, expected) -> None:
    """Helper function to test if a given IP is within allowed ranges."""
    with mock.patch("django.conf.settings") as settings:
        from pod.authentication.IPRestrictionMiddleware import ip_in_allowed_range
        settings.ALLOWED_SUPERUSER_IPS = allowed
        assert ip_in_allowed_range(ip) is expected


class IPRestrictionMiddlewareTestCase(TestCase):
    """IP Restriction Middleware Test Case."""

    def setUp(self) -> None:
        """Tnitializes test users and request factory.."""

        self.admin = User.objects.create(
            first_name="pod",
            last_name="Admin",
            username="admin",
            is_superuser=True,
        )

        self.simple_user = User.objects.create(
            first_name="Pod",
            last_name="User",
            username="pod",
        )

        self.factory = RequestFactory()

    def test_ip_in_allowed_ranges(self) -> None:
        """Tests IP range matching logic."""
        for params in [
            ("192.168.1.10", ["192.168.1.0/24"], True),
            ("192.168.1.10", ["10.0.0.0/8"], False),
            ("10.0.0.1", ["10.0.0.1"], True),
            ("invalid_ip", ["192.168.1.0/24"], False),
            ("10.11.12.13", [], True),
            ("10.11.12.13", [""], False),
        ]:
            check_ip_in_allowed_range(*params)

    def test_simpleuser(self) -> None:
        """Ensures regular users are not affected by IP restrictions."""
        from pod.authentication.IPRestrictionMiddleware import IPRestrictionMiddleware
        get_response = mock.MagicMock()
        middleware = IPRestrictionMiddleware(get_response)

        request = self.factory.get('/')
        request.user = self.simple_user
        response = middleware(request)

        # ensure get_response has been returned
        self.assertEqual(get_response.return_value, response)
        self.assertFalse(request.user.is_superuser)
        self.assertEqual(request.user.last_name, self.simple_user.last_name)

    @override_settings(
        ALLOWED_SUPERUSER_IPS=['127.0.0.1/24'],
    )
    def test_superuser_ip_allowed(self) -> None:
        """Verifies superuser access when IP is allowed."""
        from pod.authentication.IPRestrictionMiddleware import IPRestrictionMiddleware
        get_response = mock.MagicMock()
        middleware = IPRestrictionMiddleware(get_response)

        request = self.factory.get('/')
        request.user = self.admin
        self.assertTrue(request.user.is_superuser)
        response = middleware(request)

        # ensure get_response has been returned
        self.assertEqual(get_response.return_value, response)
        self.assertTrue(request.user.is_superuser)
        self.assertEqual(request.user.last_name, self.admin.last_name)

    @override_settings(
        ALLOWED_SUPERUSER_IPS=['10.0.0.0/8'],
    )
    def test_superuser_ip_not_allowed(self) -> None:
        """Verifies superuser access is revoked when IP is not allowed."""
        from pod.authentication.IPRestrictionMiddleware import IPRestrictionMiddleware
        get_response = mock.MagicMock()
        middleware = IPRestrictionMiddleware(get_response)

        request = self.factory.get('/')
        request.user = self.admin
        self.assertTrue(request.user.is_superuser)

        middleware(request)
        self.assertFalse(request.user.is_superuser)
        self.assertTrue("127.0.0.1" in request.user.last_name)
