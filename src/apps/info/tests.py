"""
Esup-Pod - Info app unit tests.
"""

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.encoding.conf import encoding_settings


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

    def test_config_info_view_exposes_encoding_upload_settings(self):
        """Encoding upload settings are public under their API names only."""
        response = self.client.get(reverse("config_info"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        encoding_config = response.data["encoding"]
        self.assertEqual(
            set(encoding_config),
            {
                "max_upload_size_gb",
                "video_allowed_extensions",
                "img_allowed_extensions",
                "subtitle_allowed_extensions",
                "video_required_fields",
                "user_quota_size_gb",
            },
        )
        self.assertEqual(
            tuple(encoding_config["video_allowed_extensions"]),
            encoding_settings.allowed_extensions,
        )
        self.assertEqual(
            tuple(encoding_config["img_allowed_extensions"]),
            encoding_settings.allowed_image_extensions,
        )
        self.assertEqual(
            tuple(encoding_config["subtitle_allowed_extensions"]),
            encoding_settings.allowed_subtitle_extensions,
        )
        self.assertEqual(
            encoding_config["video_required_fields"],
            encoding_settings.video_required_fields,
        )
        self.assertEqual(
            encoding_config["max_upload_size_gb"],
            encoding_settings.max_upload_size_gb,
        )
        self.assertEqual(
            encoding_config["user_quota_size_gb"],
            encoding_settings.user_quota_size_gb,
        )
