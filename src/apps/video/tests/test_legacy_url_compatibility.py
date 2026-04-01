"""
Esup-Pod - Tests for URLs legacy compatibility between V4 and V5.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from src.apps.video.models import Video

User = get_user_model()


class MigrationURLTest(TestCase):
    """
    Esup-Pod - Tests for legacy URL formats.
    """

    def setUp(self):
        """
        Esup-Pod - Setup test data.
        """
        self.user = User.objects.create_user(
            username="migrationuser", password="password"
        )

    def test_legacy_url_compatibility(self):
        """
        Esup-Pod - Ensure legacy V4 URLs are handled.
        """
        video = Video.objects.create(
            title="Washington Landlord",
            id=46859,
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )

        expected_absolute_url = f"/video/{video.pk}-{video.slug}/"

        self.assertEqual(video.get_absolute_url(), expected_absolute_url)
        self.assertIn("46859", video.get_absolute_url())
        legacy_api_url = f"/api/videos/{video.pk}-washingtonlandlordtenantlawmp4/"
        response = self.client.get(legacy_api_url)

        self.assertEqual(response.status_code, 200)
