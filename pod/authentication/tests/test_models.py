"""Esup-Pod authentication models test cases."""

from django.test import TestCase, Client, override_settings
from django.test.client import RequestFactory
from pod.authentication.models import Owner, AccessGroup
from pod.authentication.IPRestrictionMiddleware import ip_in_allowed_range
from django.contrib.auth.models import User
from django.conf import settings

import hashlib

SECRET_KEY = getattr(settings, "SECRET_KEY", "")

# ggignore-start
# gitguardian:ignore
PWD = "pod1234pod"  # nosec
# ggignore-end


class OwnerTestCase(TestCase):
    """Owner Test Case."""

    def setUp(self) -> None:
        """Set up OwnerTestCase create user Pod."""
        User.objects.create(username="pod", password=PWD)
        # Owner.objects.create(user=user)

    def test_creation_owner(self) -> None:
        """Check if owner exist with username pod and check hashkey."""
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        hashkey = hashlib.sha256((SECRET_KEY + "pod").encode("utf-8")).hexdigest()
        self.assertEqual(owner.hashkey, hashkey)
        print("test_creation_owner OwnerTestCase OK")

    def test_suppression_owner(self) -> None:
        owner = Owner.objects.get(user__username="pod")
        owner.delete()
        self.assertEqual(Owner.objects.filter(user__username="pod").count(), 0)
        print("test_suppression_owner OwnerTestCase OK")


class AccessGroupTestCase(TestCase):
    """Acess Group Test Case."""

    def setUp(self) -> None:
        """Set up AcessGroupTestCase create user Pod."""
        User.objects.create(username="pod", password=PWD)

        AccessGroup.objects.create(code_name="group1", display_name="Group 1")

    def test_creation_accessgroup(self) -> None:
        """Check if owner exist with username pod and check hashkey."""
        accessgroup = AccessGroup.objects.get(code_name="group1")
        self.assertEqual(accessgroup.code_name, "group1")
        self.assertEqual(accessgroup.display_name, "Group 1")
        print("test_creation_accessgroup AccessGroupTestCase OK")

    def test_suppression_accessgroup(self) -> None:
        accessgroup = AccessGroup.objects.get(code_name="group1")
        accessgroup.delete()
        self.assertEqual(AccessGroup.objects.filter(code_name="group1").count(), 0)
        print("test_suppression_accessgroup AccessGroupTestCase OK")


class IPRestrictionTestCase(TestCase):

    def setUp(self) -> None:
        """Set up IPRestrictionTestCase create user Pod."""
        # Every test needs access to the client.
        self.client = Client()

        self.admin = User.objects.create(
            first_name="pod",
            last_name="Admin",
            username="admin",
            password=PWD,
            is_superuser=True,
        )
        self.simple_user = User.objects.create(
            first_name="Pod",
            last_name="User",
            username="pod",
            password=PWD
        )

    @override_settings(
        ALLOWED_SUPERUSER_IPS=[],
    )
    def test_connect_without_restriction(self) -> None:
        """Check that admin has superuser access when no restriction defined."""

        # Simple User
        self.client.force_login(self.simple_user)
        response = self.client.get("/")
        self.assertFalse('href="/admin/"' in response.content.decode())
        self.assertTrue(self.simple_user.is_authenticated)
        self.client.logout()

        # Admin
        self.client.force_login(self.admin)
        response = self.client.get("/")
        self.assertTrue('href="/admin/"' in response.content.decode())
        admin = User.objects.get(username="admin")
        self.assertTrue(admin.is_authenticated)
        self.client.logout()

        print("test_connect_without_restriction OK")

    @override_settings(
        ALLOWED_SUPERUSER_IPS=["127.0.0.1"],
    )
    def test_connect_with_local_restriction(self) -> None:
        """Check that admin has superuser access when restriction defined to localhost."""

        # Simple User
        self.client.force_login(self.simple_user)
        self.assertTrue(self.simple_user.is_authenticated)
        response = self.client.get("/")
        self.assertFalse('href="/admin/"' in response.content.decode())
        self.client.logout()

        # Admin
        self.client.force_login(self.admin)
        self.assertTrue(self.admin.is_authenticated)
        response = self.client.get("/")
        self.assertTrue('href="/admin/"' in response.content.decode())
        self.client.logout()

        print("test_connect_with_local_restriction OK")

    @override_settings(
        ALLOWED_SUPERUSER_IPS=["123.456.789.10"],
    )
    def test_connect_with_other_restriction(self) -> None:
        """Check that admin no more has superuser access when restriction defined to other IP."""
        # Simple User
        self.client.force_login(self.simple_user)
        self.assertTrue(self.simple_user.is_authenticated)
        response = self.client.get("/")
        self.assertFalse('href="/admin/"' in response.content.decode())
        self.client.logout()

        # Admin
        self.client.force_login(self.admin)
        self.assertTrue(self.admin.is_authenticated)
        response = self.client.get("/")
        self.assertFalse('href="/admin/"' in response.content.decode())
        self.client.logout()

        print("test_connect_with_other_restriction OK")

    @override_settings(
        ALLOWED_SUPERUSER_IPS=["123.123.123.123", "200.200.200.0/24", "100.100.100.100/32"],
    )
    def test_ip_in_allowed_range(self) -> None:
        """Check that ip_in_allowed_range works as expected."""
        self.assertFalse(ip_in_allowed_range("127.0.0.1"))
        self.assertTrue(ip_in_allowed_range("123.123.123.123"))
        self.assertTrue(ip_in_allowed_range("200.200.200.200"))
        self.assertTrue(ip_in_allowed_range("100.100.100.100"))
        self.assertFalse(ip_in_allowed_range("100.100.100.101"))
