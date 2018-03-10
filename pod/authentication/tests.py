from django.test import TestCase
from pod.authentication.models import Owner
from django.contrib.auth.models import User
from django.conf import settings
import hashlib

SECRET_KEY = getattr(settings, 'SECRET_KEY', '')


# Create your tests here.
class OwnerTestCase(TestCase):

    """OwnerTestCase"""

    def setUp(self):
        """setUp OwnerTestCase create user pod"""
        User.objects.create(username="pod", password="pod1234pod")
        # Owner.objects.create(user=user)

    def test_creation_owner(self):
        """check if owner exist with username pod and check hashkey"""
        owner = Owner.objects.get(user__username="pod")
        hashkey = hashlib.sha256(
            (SECRET_KEY + "pod").encode('utf-8')).hexdigest()
        # cat = Animal.objects.get(name="cat")
        self.assertEqual(owner.hashkey, hashkey)
        print("ok OwnerTestCase")
        # self.assertEqual(cat.speak(), 'The cat says "meow"')
