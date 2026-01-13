from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class TestOwnerModel(TestCase):
    def test_owner_creation_signal(self):
        user = User.objects.create(username="ownertest")
        self.assertTrue(hasattr(user, "owner"))
        self.assertEqual(user.owner.user, user)

    def test_hashkey_generation(self):
        user = User.objects.create(username="hashkeytest")
        owner = user.owner
        # hashkey is generated on save if empty
        owner.save()
        self.assertTrue(len(owner.hashkey) > 0)

        old_hash = owner.hashkey
        owner.save()
        self.assertEqual(owner.hashkey, old_hash)

    def test_str_representation(self):
        user = User.objects.create(
            username="strtest", first_name="John", last_name="Doe"
        )
        # Depending on HIDE_USERNAME settings, output changes.
        # Default seems to be HIDE_USERNAME=False based on previous file read?
        # Let's just check it contains the name
        self.assertIn("John Doe", str(user.owner))
