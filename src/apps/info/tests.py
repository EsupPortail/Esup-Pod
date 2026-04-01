"""
Esup-Pod - Info app unit tests.
"""

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class InfoViewsTests(APITestCase):
    """
    Test suite for public information and configuration views.
    """

    def test_system_info_view(self):
        """Verifies the system info endpoint returns basic project metadata."""
        url = reverse("system_info")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("project", response.data)
        self.assertIn("version", response.data)
        self.assertEqual(response.data["project"], settings.POD_PROJECT_NAME)

    def test_config_info_view(self):
        """Verifies the config info endpoint returns authentication settings."""
        url = reverse("config_info")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn("authentication", response.data)
        self.assertIn("use_cas", response.data["authentication"])
