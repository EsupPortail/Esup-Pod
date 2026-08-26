"""
Esup-Pod - VideoAccessToken tests.
"""

import sys
from importlib import reload
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.urls import clear_url_caches
from django.utils import timezone
from rest_framework.test import APITestCase

from src.apps.video.apps import sync_metadata
from src.apps.video.conf import video_settings
from src.apps.video.models import Video, VideoAccessToken


def reload_urlconf():
    """Reloads URL configurations after a settings change."""
    clear_url_caches()
    video_urls = "src.apps.video.urls"
    if video_urls in sys.modules:
        reload(sys.modules[video_urls])
    if settings.ROOT_URLCONF in sys.modules:
        reload(sys.modules[settings.ROOT_URLCONF])


User = get_user_model()


class VideoAccessTokenTests(APITestCase):
    """Tests for the VideoAccessToken API endpoints."""

    def setUp(self):
        """Sets up a video and users for token testing."""
        sync_metadata(sender=None)

        # Save original settings to restore in tearDown
        self.original_use_token = video_settings.use_video_access_token

        video_settings.use_video_access_token = True
        reload_urlconf()

        self.site = Site.objects.get_current()
        self.owner = User.objects.create_user(
            username="owner", password="password"
        )  # nosec
        self.other_user = User.objects.create_user(
            username="other", password="password"
        )  # nosec
        self.video = Video.objects.create(
            title="Token Test Video",
            owner=self.owner,
            status=Video.Status.RESTRICTED,
        )
        self.video.sites.add(self.site)

    def tearDown(self):
        """Restore original settings and reload URLs to prevent test leakage."""
        video_settings.use_video_access_token = self.original_use_token
        reload_urlconf()

    def test_owner_can_create_token(self):
        """Owner can create an access token for their own video."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            "/api/tokens/",
            {"video": self.video.id, "label": "Shared with John"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            VideoAccessToken.objects.filter(
                video=self.video, created_by=self.owner
            ).exists()
        )
        self.assertIn("token", response.data)

    def test_non_owner_cannot_create_token(self):
        """A user who is not owner/co-owner cannot create a token for the video."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            "/api/tokens/",
            {"video": self.video.id, "label": "Unauthorized"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(VideoAccessToken.objects.filter(video=self.video).exists())

    def test_resolve_valid_token(self):
        """Resolving a valid token returns video info."""
        token = VideoAccessToken.objects.create(video=self.video, created_by=self.owner)

        response = self.client.get(f"/api/tokens/resolve/{token.token}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["video_slug"], self.video.slug)

        token.refresh_from_db()
        self.assertEqual(token.use_count, 1)
        self.assertIsNotNone(token.last_used_at)

    def test_resolve_invalid_token(self):
        """Resolving a non-existent token returns 404."""
        response = self.client.get(
            "/api/tokens/resolve/00000000-0000-0000-0000-000000000000/"
        )
        self.assertEqual(response.status_code, 404)

    def test_resolve_revoked_token(self):
        """Resolving a revoked token returns 403."""
        token = VideoAccessToken.objects.create(
            video=self.video, created_by=self.owner, is_active=False
        )

        response = self.client.get(f"/api/tokens/resolve/{token.token}/")
        self.assertEqual(response.status_code, 403)

    def test_resolve_expired_token(self):
        """Resolving an expired token returns 403."""
        token = VideoAccessToken.objects.create(
            video=self.video,
            created_by=self.owner,
            expires_at=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(f"/api/tokens/resolve/{token.token}/")
        self.assertEqual(response.status_code, 403)

    def test_revoke_token(self):
        """Owner can revoke their own token."""
        token = VideoAccessToken.objects.create(video=self.video, created_by=self.owner)

        self.client.force_authenticate(user=self.owner)
        response = self.client.post(f"/api/tokens/{token.id}/revoke/")

        self.assertEqual(response.status_code, 200)
        token.refresh_from_db()
        self.assertFalse(token.is_active)

    def test_user_only_sees_own_tokens(self):
        """A user only sees tokens they created, not others'."""
        VideoAccessToken.objects.create(video=self.video, created_by=self.owner)
        VideoAccessToken.objects.create(video=self.video, created_by=self.other_user)

        self.client.force_authenticate(user=self.owner)
        response = self.client.get("/api/tokens/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_expiry_in_the_past_rejected(self):
        """Creating a token with a past expiry date is rejected."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            "/api/tokens/",
            {
                "video": self.video.id,
                "expires_at": (timezone.now() - timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_expiry_exceeding_max_validity_rejected(self):
        """Creating a token with expiry exceeding max validity is rejected."""
        self.client.force_authenticate(user=self.owner)
        far_future = timezone.now() + timedelta(days=400)
        response = self.client.post(
            "/api/tokens/",
            {"video": self.video.id, "expires_at": far_future.isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_feature_disabled_blocks_creation(self):
        """When the feature is disabled, token creation is blocked."""
        video_settings.use_video_access_token = False

        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            "/api/tokens/",
            {"video": self.video.id},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        video_settings.use_video_access_token = True

    def test_unauthenticated_cannot_list_tokens(self):
        """Unauthenticated users cannot list tokens."""
        response = self.client.get("/api/tokens/")
        self.assertEqual(response.status_code, 401)
