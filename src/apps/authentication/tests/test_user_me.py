"""
Esup-Pod - Tests for the 'me' user information endpoint.

This module ensures that the /api/auth/users/me/ endpoint returns the correct
information for the currently authenticated user, including profile details
from the associated Owner model.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import Owner

User = get_user_model()


class UserMeViewTests(APITestCase):
    """
    Test suite for the user information retrieval endpoint.
    """

    def setUp(self):
        """
        Initializes a test user and their owner profile, then authenticates the client.
        """
        self.username = "testuser"
        # ggignore-start
        # gitguardian:ignore
        self.password = "testpass123"  # nosec
        # ggignore-end
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )
        Owner.objects.filter(user=self.user).update(
            affiliation="student", establishment="Etab_1"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("user_me")

    def test_user_me_success(self):
        """
        Tests that the /me/ endpoint returns correct data for the authenticated user.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.username)
        self.assertEqual(response.data["affiliation"], "student")
        self.assertEqual(response.data["establishment"], "Etab_1")

    def test_user_me_unauthenticated(self):
        """
        Tests that the /me/ endpoint is restricted to authenticated users.
        """
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_detail_still_works(self):
        """
        Ensures that the standard DRF user detail view still functions correctly.
        """
        detail_url = reverse("user-detail", kwargs={"pk": self.user.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.username)
