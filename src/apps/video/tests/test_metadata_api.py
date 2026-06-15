"""
Esup-Pod - Video metadata API tests.
"""

from django.contrib.sites.models import Site
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.video.models import Type
from src.apps.video.apps import sync_metadata


class MetadataAPITests(APITestCase):
    """
    Tests for the video metadata endpoints.
    """

    def setUp(self):
        """Set up the test environment."""
        sync_metadata(sender=None)
        self.site = Site.objects.get_current()
        self.type = Type.objects.create(title="Course")
        self.type.sites.add(self.site)

    def test_metadata_endpoint(self):
        """Test the /api/video/videos/metadata/ endpoint."""
        url = reverse("video-metadata")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn("licenses", data)
        self.assertIn("cursus", data)
        self.assertIn("statuses", data)
        self.assertIn("languages", data)

        # Verify some known choices
        license_values = [lic["value"] for lic in data["licenses"]]
        self.assertIn("COPYRIGHT", license_values)
        self.assertIn("CC-BY", license_values)

        cursus_values = [c["value"] for c in data["cursus"]]
        self.assertIn("L1", cursus_values)
        self.assertIn("M2", cursus_values)

    def test_types_list(self):
        """Test the /api/video/types/ endpoint."""
        url = reverse("type-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should contain the type we created in setUp
        if "results" in response.data:
            titles = [t["title"] for t in response.data["results"]]
        else:
            titles = [t["title"] for t in response.data]
        self.assertIn("Course", titles)
