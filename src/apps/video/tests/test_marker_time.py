"""
Esup-Pod - UserMarkerTime tests.
"""

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from rest_framework.test import APITestCase

from unittest.mock import patch

from src.apps.video.apps import sync_metadata
from src.apps.video.models import UserMarkerTime, Video
from src.apps.video.conf import video_settings

User = get_user_model()


class UserMarkerTimeTests(APITestCase):
    """Tests for the UserMarkerTime API endpoints."""

    def setUp(self):
        """Sets up a video and a user for marker time testing."""
        sync_metadata(sender=None)
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(
            username="viewer", password="password"
        )  # nosec
        self.other_user = User.objects.create_user(
            username="other", password="password"
        )  # nosec
        self.video = Video.objects.create(
            title="Marker Test Video",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )
        self.video.sites.add(self.site)

    def test_get_marker_no_existing_marker(self):
        """Returns 0 if no marker exists yet for the user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/marker/{self.video.slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["marker"], 0)

    def test_save_marker_creates_new(self):
        """Saving a marker creates a new UserMarkerTime entry."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f"/api/marker/{self.video.slug}/save/",
            {"marker": 42},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["marker"], 42)
        self.assertTrue(
            UserMarkerTime.objects.filter(video=self.video, user=self.user).exists()
        )

    def test_save_marker_updates_existing(self):
        """Saving a marker again updates the existing entry instead of duplicating."""
        UserMarkerTime.objects.create(video=self.video, user=self.user, marker=10)

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f"/api/marker/{self.video.slug}/save/",
            {"marker": 99},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["marker"], 99)
        self.assertEqual(
            UserMarkerTime.objects.filter(video=self.video, user=self.user).count(), 1
        )

    def test_get_marker_after_save(self):
        """Verifies the saved marker is correctly returned via GET."""
        self.client.force_authenticate(user=self.user)
        self.client.post(
            f"/api/marker/{self.video.slug}/save/",
            {"marker": 77},
            format="json",
        )
        response = self.client.get(f"/api/marker/{self.video.slug}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["marker"], 77)

    def test_reset_marker_deletes_entry(self):
        """Resetting the marker deletes the UserMarkerTime entry."""
        UserMarkerTime.objects.create(video=self.video, user=self.user, marker=50)

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/marker/{self.video.slug}/reset/")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            UserMarkerTime.objects.filter(video=self.video, user=self.user).exists()
        )

    def test_marker_isolation_between_users(self):
        """Each user's marker is isolated from other users."""
        UserMarkerTime.objects.create(video=self.video, user=self.user, marker=20)
        UserMarkerTime.objects.create(video=self.video, user=self.other_user, marker=80)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/marker/{self.video.slug}/")
        self.assertEqual(response.data["marker"], 20)

        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f"/api/marker/{self.video.slug}/")
        self.assertEqual(response.data["marker"], 80)

    def test_unauthenticated_cannot_access_marker(self):
        """Unauthenticated users cannot access the marker endpoints."""
        response = self.client.get(f"/api/marker/{self.video.slug}/")
        self.assertEqual(response.status_code, 401)

    def test_get_marker_video_not_found(self):
        """Returns 404 when the video does not exist."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/marker/nonexistent-slug/")
        self.assertEqual(response.status_code, 404)

    @patch.object(video_settings, "use_marker_time", False)
    def test_marker_disabled_returns_400(self):
        """Returns 400 when the marker time feature is disabled."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/marker/{self.video.slug}/")

        self.assertEqual(response.status_code, 400)
