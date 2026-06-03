"""
Esup-Pod - Tests for URLs legacy compatibility between V4 and V5.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from src.apps.video.models import Video

User = get_user_model()


class MigrationURLTest(TestCase):
    """
    Tests for legacy URL formats.
    """

    def setUp(self):
        """
        Setup test data.
        """
        self.user = User.objects.create_user(
            username="migrationuser", password="password"
        )

    def test_slug_format_matches_v4(self):
        """
        Slug must follow the V4 format: "%04d-<slugified-title>".

        V4 reference (models2.py L.924-925):
            newid = "%04d" % newid          # e.g. 42 → "0042"
            self.slug = "%s-%s" % (newid, slugify(self.title))
        """
        video = Video.objects.create(
            title="Washington Landlord",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )
        id_padded = "%04d" % video.pk
        expected_slug = f"{id_padded}-washington-landlord"
        video.refresh_from_db()
        self.assertEqual(video.slug, expected_slug)

    def test_get_absolute_url_v4_format(self):
        """
        get_absolute_url() must return /video/<slug>/.
        The slug already contains the zero-padded ID, so no double-ID.
        """
        video = Video.objects.create(
            title="Washington Landlord",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )
        video.refresh_from_db()
        id_padded = "%04d" % video.pk
        expected_slug = f"{id_padded}-washington-landlord"
        expected_url = f"/video/{expected_slug}/"
        self.assertEqual(video.get_absolute_url(), expected_url)
        # Ensure pk does NOT appear twice (old bug: /video/42-0042-titre/)
        self.assertEqual(video.get_absolute_url().count(str(video.pk)), 1)

    def test_api_video_detail_accessible_by_slug(self):
        """
        The V5 API endpoint /api/videos/<slug>/ must return 200
        when called with the V4-format slug.
        """
        video = Video.objects.create(
            title="Washington Landlord",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )
        video.refresh_from_db()
        response = self.client.get(f"/api/videos/{video.slug}/")
        self.assertEqual(response.status_code, 200)
