"""Esup-Pod authentication models test cases."""

from django.test import TestCase
from pod.authentication.models import Owner, AccessGroup
from django.contrib.auth.models import User
from django.conf import settings

import hashlib

SECRET_KEY = getattr(settings, "SECRET_KEY", "")


class OwnerTestCase(TestCase):
    """Owner Test Case."""

    def setUp(self):
        """Set up OwnerTestCase create user Pod."""
        User.objects.create(username="pod", password="pod1234pod")
        # Owner.objects.create(user=user)

    def test_creation_owner(self):
        """Check if owner exist with username pod and check hashkey."""
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        hashkey = hashlib.sha256((SECRET_KEY + "pod").encode("utf-8")).hexdigest()
        self.assertEqual(owner.hashkey, hashkey)
        print("test_creation_owner OwnerTestCase OK")

    def test_suppression_owner(self):
        owner = Owner.objects.get(user__username="pod")
        owner.delete()
        self.assertEqual(Owner.objects.filter(user__username="pod").count(), 0)
        print("test_suppression_owner OwnerTestCase OK")


class AccessGroupTestCase(TestCase):
    """Acess Group Test Case."""

    def setUp(self):
        """Set up AcessGroupTestCase create user Pod."""
        User.objects.create(username="pod", password="pod1234pod")

        AccessGroup.objects.create(code_name="group1", display_name="Group 1")

    def test_creation_accessgroup(self):
        """Check if owner exist with username pod and check hashkey."""
        accessgroup = AccessGroup.objects.get(code_name="group1")
        self.assertEqual(accessgroup.code_name, "group1")
        self.assertEqual(accessgroup.display_name, "Group 1")
        print("test_creation_accessgroup AccessGroupTestCase OK")

    def test_suppression_accessgroup(self):
        accessgroup = AccessGroup.objects.get(code_name="group1")
        accessgroup.delete()
        self.assertEqual(AccessGroup.objects.filter(code_name="group1").count(), 0)
        print("test_suppression_accessgroup AccessGroupTestCase OK")
