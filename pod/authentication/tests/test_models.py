from django.test import TestCase
from pod.authentication.models import Owner
from django.contrib.auth.models import User
from django.conf import settings

import hashlib

SECRET_KEY = getattr(settings, 'SECRET_KEY', '')


class OwnerTestCase(TestCase):

    """OwnerTestCase"""

    def setUp(self):
        """setUp OwnerTestCase create user pod"""
        User.objects.create(username="pod", password="pod1234pod")
        # Owner.objects.create(user=user)

    def test_creation_owner(self):
        """check if owner exist with username pod and check hashkey"""
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        hashkey = hashlib.sha256(
            (SECRET_KEY + "pod").encode('utf-8')).hexdigest()
        self.assertEqual(owner.hashkey, hashkey)
        print("test_creation_owner OwnerTestCase OK")

    def test_suppression_owner(self):
        owner = Owner.objects.get(user__username="pod")
        owner.delete()
        self.assertEqual(Owner.objects.filter(user__username="pod").count(), 0)
        print("test_suppression_owner OwnerTestCase OK")
