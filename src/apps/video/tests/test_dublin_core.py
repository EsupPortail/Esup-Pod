"""
Esup-Pod - Dublin Core tests.
"""

import sys
from importlib import reload

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.urls import clear_url_caches
from rest_framework.test import APITestCase

from src.apps.video.apps import sync_metadata
from src.apps.video.conf import video_settings
from src.apps.video.models import Video


def reload_urlconf():
    """Reloads URL configurations after a settings change."""
    clear_url_caches()
    video_urls = "src.apps.video.urls"
    if video_urls in sys.modules:
        reload(sys.modules[video_urls])
    if settings.ROOT_URLCONF in sys.modules:
        reload(sys.modules[settings.ROOT_URLCONF])


User = get_user_model()


class DublinCoreTests(APITestCase):
    """Tests for the Dublin Core metadata endpoints."""

    def setUp(self):
        """Sets up published and non-published videos for Dublin Core testing."""
        sync_metadata(sender=None)

        # Save original settings to restore in tearDown
        self.original_use_dublin = video_settings.use_dublin_core

        video_settings.use_dublin_core = True
        reload_urlconf()

        self.site = Site.objects.get_current()
        self.owner = User.objects.create_user(username="owner", password="password")

        self.published_video = Video.objects.create(
            title="Public Video",
            description="A public description",
            owner=self.owner,
            status=Video.Status.PUBLISHED,
        )
        self.published_video.sites.add(self.site)

        self.draft_video = Video.objects.create(
            title="Draft Video",
            owner=self.owner,
            status=Video.Status.DRAFT,
        )
        self.draft_video.sites.add(self.site)

    def tearDown(self):
        """Restore original settings and reload URLs to prevent test leakage."""
        video_settings.use_dublin_core = self.original_use_dublin
        reload_urlconf()

    def test_get_dublin_core_returns_expected_fields(self):
        """Verifies get_dublin_core() returns all expected keys."""
        dc = self.published_video.get_dublin_core()

        expected_keys = {
            "title",
            "description",
            "creator",
            "publisher",
            "date",
            "format",
            "rights",
            "coverage",
            "subject",
            "type",
            "language",
            "identifier",
        }
        self.assertEqual(set(dc.keys()), expected_keys)
        self.assertEqual(dc["title"], "Public Video")
        self.assertEqual(dc["creator"], "owner")
        self.assertEqual(dc["format"], "video/mp4")

    def test_video_dublin_core_action_returns_200_for_published(self):
        """Verifies /api/videos/{slug}/dublin-core/ returns 200 for published video."""
        response = self.client.get(
            f"/api/videos/{self.published_video.slug}/dublin-core/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Public Video")

    def test_video_dublin_core_action_returns_404_or_403_for_draft(self):
        """Verifies /api/videos/{slug}/dublin-core/ blocks access to a draft video."""
        response = self.client.get(f"/api/videos/{self.draft_video.slug}/dublin-core/")

        self.assertIn(response.status_code, [403, 404])

    def test_video_dublin_core_action_disabled_returns_400(self):
        """Returns 400 when the Dublin Core feature is disabled."""
        video_settings.use_dublin_core = False
        response = self.client.get(
            f"/api/videos/{self.published_video.slug}/dublin-core/"
        )

        self.assertEqual(response.status_code, 400)
        video_settings.use_dublin_core = True

    def test_dublin_core_list_only_returns_published(self):
        """Verifies /api/dublin-core/ only lists published videos."""
        response = self.client.get("/api/dublin-core/")

        self.assertEqual(response.status_code, 200)
        titles = [record["title"] for record in response.data["results"]]
        self.assertIn("Public Video", titles)
        self.assertNotIn("Draft Video", titles)

    def test_dublin_core_list_disabled_returns_400(self):
        """Returns 400 for list endpoint when feature is disabled."""
        video_settings.use_dublin_core = False
        response = self.client.get("/api/dublin-core/")

        self.assertEqual(response.status_code, 400)
        video_settings.use_dublin_core = True

    def test_dublin_core_retrieve_published_video(self):
        """Verifies /api/dublin-core/{slug}/ returns metadata for a published video."""
        response = self.client.get(f"/api/dublin-core/{self.published_video.slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Public Video")

    def test_dublin_core_retrieve_draft_returns_404(self):
        """Verifies /api/dublin-core/{slug}/ returns 404 for a draft video."""
        response = self.client.get(f"/api/dublin-core/{self.draft_video.slug}/")

        self.assertEqual(response.status_code, 404)

    def test_dublin_core_retrieve_disabled_returns_400(self):
        """Returns 400 for retrieve endpoint when feature is disabled."""
        video_settings.use_dublin_core = False
        response = self.client.get(f"/api/dublin-core/{self.published_video.slug}/")

        self.assertEqual(response.status_code, 400)
        video_settings.use_dublin_core = True

    def test_dublin_core_is_public_no_auth_required(self):
        """Verifies Dublin Core endpoints are accessible without authentication."""
        response = self.client.get("/api/dublin-core/")
        self.assertNotEqual(response.status_code, 401)
