"""
Esup-Pod - Tests for access group management and owner linking.

This module contains tests for the API endpoints that handle setting and removing
users from access groups, either via the Owner model or the AccessGroup model directly.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import AccessGroup, Owner

User = get_user_model()


class AccessGroupTests(APITestCase):
    """
    Test suite for AccessGroup and Owner-related group actions.
    """

    def setUp(self):
        """
        Initializes test users, owners, and access groups for each test case.
        Authenticates with a superuser by default.
        """
        self.admin_user = User.objects.create_superuser(
            username="admin", password="password", email="admin@example.org"
        )
        self.test_user = User.objects.create_user(
            username="testuser", password="password"
        )
        self.owner = Owner.objects.get(user=self.test_user)
        self.access_group = AccessGroup.objects.create(
            display_name="Test Group", code_name="test_group"
        )

        self.client.force_authenticate(user=self.admin_user)

    def test_set_user_accessgroup(self):
        """
        Test adding an access group to a specific user via the Owner endpoint.
        """
        url = reverse("owner-set-user-accessgroup")
        data = {
            "username": self.test_user.username,
            "groups": [self.access_group.code_name],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.owner.accessgroups.filter(code_name="test_group").exists())

    def test_set_user_accessgroup_missing_data(self):
        """
        Test that setting a user's access group fails when required data is missing.
        """
        url = reverse("owner-set-user-accessgroup")
        response = self.client.post(url, {"username": "testuser"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_set_user_accessgroup_user_not_found(self):
        """
        Test that setting a user's access group fails when the user does not exist.
        """
        url = reverse("owner-set-user-accessgroup")
        data = {"username": "nonexistent", "groups": ["test_group"]}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_user_accessgroup(self):
        """
        Test removing an access group from a specific user via the Owner endpoint.
        """
        self.owner.accessgroups.add(self.access_group)
        url = reverse("owner-remove-user-accessgroup")
        data = {
            "username": self.test_user.username,
            "groups": [self.access_group.code_name],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.owner.accessgroups.filter(code_name="test_group").exists())

    def test_set_users_by_name(self):
        """
        Test adding users to an access group via the AccessGroup endpoint.
        """
        url = reverse("accessgroup-set-users-by-name")
        data = {
            "code_name": self.access_group.code_name,
            "users": [self.test_user.username],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            self.access_group.users.filter(
                user__username=self.test_user.username
            ).exists()
        )

    def test_remove_users_by_name(self):
        """
        Test removing users from an access group via the AccessGroup endpoint.
        """
        self.access_group.users.add(self.owner)
        url = reverse("accessgroup-remove-users-by-name")
        data = {
            "code_name": self.access_group.code_name,
            "users": [self.test_user.username],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            self.access_group.users.filter(
                user__username=self.test_user.username
            ).exists()
        )

    def test_accessgroup_not_found_actions(self):
        """
        Test that group actions fail when the target access group is not found.
        """
        url_set = reverse("accessgroup-set-users-by-name")
        url_remove = reverse("accessgroup-remove-users-by-name")
        data = {"code_name": "wrong_group", "users": ["testuser"]}

        response = self.client.post(url_set, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.post(url_remove, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
