"""
Esup-Pod - Video metadata API tests.
"""

from django.contrib.sites.models import Site
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.video.models import Type


def populate_test_metadata():
    """Populate Language, License, and Cursus default values for tests."""
    from src.apps.video.models import Language, License, Cursus
    from src.apps.video.conf import video_settings

    for order, item in enumerate(video_settings.languages):
        Language.objects.get_or_create(
            slug=item["value"],
            defaults={"name": item["label"], "order": order},
        )

    for order, item in enumerate(video_settings.licenses):
        License.objects.get_or_create(
            slug=item["value"],
            defaults={"name": item["label"], "order": order},
        )

    for order, item in enumerate(video_settings.cursus):
        Cursus.objects.get_or_create(
            slug=item["value"],
            defaults={"name": item["label"], "order": order},
        )


class MetadataAPITests(APITestCase):
    """
    Esup-Pod - Tests for the video metadata endpoints.
    """

    def setUp(self):
        """Set up the test environment."""
        populate_test_metadata()
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
