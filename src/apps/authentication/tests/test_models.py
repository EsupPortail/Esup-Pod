"""
Esup-Pod - Tests for authentication models and signals.

This module ensures that the Owner model and related signals (like automatic
creation of an Owner upon User creation) work correctly.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase


class TestOwnerModel(TestCase):
    """
    Test suite for the logic related to the Owner model and its interaction with User.
    """

    def setUp(self):
        """
        Retrieves the current User model.
        """
        self.User = get_user_model()

    def test_owner_creation_signal(self):
        """
        Verifies that an Owner instance is automatically created when a new User is saved.
        """
        user = self.User.objects.create(username="ownertest")
        self.assertTrue(hasattr(user, "owner"))
        self.assertEqual(user.owner.user, user)

    def test_hashkey_generation(self):
        """
        Ensures that a hashkey is generated for the owner and remains stable across saves.
        """
        user = self.User.objects.create(username="hashkeytest")
        owner = user.owner
        owner.save()
        self.assertTrue(len(owner.hashkey) > 0)

        old_hash = owner.hashkey
        owner.save()
        self.assertEqual(owner.hashkey, old_hash)

    def test_str_representation(self):
        """
        Validates the string representation of the Owner model.
        """
        user = self.User.objects.create(
            username="strtest", first_name="John", last_name="Doe"
        )
        self.assertIn("John Doe", str(user.owner))

    def test_user_str(self):
        """
        Validates the string representation of the custom User model.
        """
        user = self.User.objects.create(
            username="userstr", first_name="Admin", last_name="User"
        )
        self.assertIn("Admin User (userstr)", str(user))
