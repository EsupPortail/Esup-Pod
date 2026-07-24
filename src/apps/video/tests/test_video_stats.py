"""
Esup-Pod - Video statistics tests.
"""

import sys
from importlib import reload
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.urls import clear_url_caches
from rest_framework.test import APITestCase

from src.apps.video.apps import sync_metadata
from src.apps.video.conf import video_settings
from src.apps.video.models import Video, ViewCount


def reload_urlconf():
    """Reloads URL configurations after a settings change."""
    clear_url_caches()
    video_urls = "src.apps.video.urls"
    if video_urls in sys.modules:
        reload(sys.modules[video_urls])
    if settings.ROOT_URLCONF in sys.modules:
        reload(sys.modules[settings.ROOT_URLCONF])


User = get_user_model()


class VideoStatsTests(APITestCase):
    """Tests for the video stats endpoint and ViewCountViewSet."""

    def setUp(self):
        """Sets up a video with view counts for stats testing."""
        sync_metadata(sender=None)

        # Save original settings to restore in tearDown
        self.original_use_stats = video_settings.use_stats_view
        self.original_view_auth = video_settings.view_stats_auth

        video_settings.use_stats_view = True
        video_settings.view_stats_auth = False
        reload_urlconf()

        self.site = Site.objects.get_current()
        self.owner = User.objects.create_user(
            username="owner", password="password"
        )  # nosec
        self.other_user = User.objects.create_user(
            username="other", password="password"
        )  # nosec
        self.video = Video.objects.create(
            title="Stats Test Video",
            owner=self.owner,
            status=Video.Status.PUBLISHED,
            view_count=100,
        )
        self.video.sites.add(self.site)

        ViewCount.objects.create(video=self.video, date=date.today(), count=10)
        ViewCount.objects.create(
            video=self.video, date=date.today() - timedelta(days=3), count=5
        )
        ViewCount.objects.create(
            video=self.video, date=date.today() - timedelta(days=40), count=20
        )

    def tearDown(self):
        """Restore original settings and reload URLs to prevent test leakage."""
        video_settings.use_stats_view = self.original_use_stats
        video_settings.view_stats_auth = self.original_view_auth
        reload_urlconf()

    def test_stats_returns_aggregated_data(self):
        """Verifies stats endpoint returns correct aggregated data."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/api/videos/{self.video.slug}/stats/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["video_slug"], self.video.slug)
        self.assertEqual(response.data["total_views"], 100)
        self.assertEqual(response.data["views_last_7_days"], 15)
        self.assertEqual(response.data["views_last_30_days"], 15)

    def test_stats_peak_day(self):
        """Verifies the peak day is correctly identified."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/api/videos/{self.video.slug}/stats/")

        self.assertEqual(response.data["peak_count"], 20)

    def test_stats_daily_breakdown_respects_days_param(self):
        """Verifies the daily breakdown only includes entries within the days range."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/api/videos/{self.video.slug}/stats/?days=7")

        dates_in_breakdown = [entry["date"] for entry in response.data["daily_breakdown"]]
        self.assertEqual(len(dates_in_breakdown), 2)

    def test_stats_disabled_returns_400(self):
        """Returns 400 when the stats feature is disabled."""
        video_settings.use_stats_view = False
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f"/api/videos/{self.video.slug}/stats/")
        self.assertEqual(response.status_code, 400)
        video_settings.use_stats_view = True

    def test_stats_requires_auth_when_configured(self):
        """Returns 403 for anonymous users when VIEW_STATS_AUTH is enabled."""
        video_settings.view_stats_auth = True
        response = self.client.get(f"/api/videos/{self.video.slug}/stats/")
        self.assertEqual(response.status_code, 403)
        video_settings.view_stats_auth = False

    def test_stats_forbidden_for_non_owner(self):
        """Returns 403 for a user who is not owner, co-owner, or staff."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f"/api/videos/{self.video.slug}/stats/")

        self.assertEqual(response.status_code, 403)

    def test_stats_forbidden_for_staff(self):
        """Staff users cannot view stats if not owner (restricted)."""
        self.other_user.is_staff = True
        self.other_user.save()

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f"/api/videos/{self.video.slug}/stats/")

        self.assertEqual(response.status_code, 403)

    def test_view_count_list_filtered_by_video(self):
        """Verifies ViewCountViewSet filters by video slug."""
        response = self.client.get(f"/api/view-counts/?video={self.video.slug}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)

    def test_view_count_filtered_by_date_range(self):
        """Verifies ViewCountViewSet filters by date range."""
        response = self.client.get(
            f"/api/view-counts/?video={self.video.slug}"
            f"&date__gte={date.today() - timedelta(days=10)}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)

    def test_view_count_requires_auth_when_configured(self):
        """ViewCountViewSet requires authentication if VIEW_STATS_AUTH is enabled."""
        video_settings.view_stats_auth = True
        response = self.client.get(f"/api/view-counts/?video={self.video.slug}")
        self.assertEqual(response.status_code, 401)
        video_settings.view_stats_auth = False
