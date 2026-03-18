from django.contrib.auth import get_user_model
from django.test import TestCase


class TestOwnerModel(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_owner_creation_signal(self):
        user = self.User.objects.create(username="ownertest")
        self.assertTrue(hasattr(user, "owner"))
        self.assertEqual(user.owner.user, user)

    def test_hashkey_generation(self):
        user = self.User.objects.create(username="hashkeytest")
        owner = user.owner
        owner.save()
        self.assertTrue(len(owner.hashkey) > 0)

        old_hash = owner.hashkey
        owner.save()
        self.assertEqual(owner.hashkey, old_hash)

    def test_str_representation(self):
        user = self.User.objects.create(
            username="strtest", first_name="John", last_name="Doe"
        )
        self.assertIn("John Doe", str(user.owner))

    def test_user_str(self):
        user = self.User.objects.create(
            username="userstr", first_name="Admin", last_name="User"
        )
        self.assertIn("Admin User (userstr)", str(user))
