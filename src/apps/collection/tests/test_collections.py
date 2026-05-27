"""
Esup-Pod - Collection application tests (Refactored for 4 distinct models).
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.base import ContentFile
from src.apps.collection.models import (
    Channel,
    Theme,
    Playlist,
)
from src.apps.video.models import Video

User = get_user_model()


class CollectionTests(APITestCase):
    """
    Tests for the refactored collection models (Channel, Theme, Playlist, Favorite).
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", password="password")
        self.admin = User.objects.create_superuser(username="admin", password="password")
        self.other_user = User.objects.create_user(username="other", password="password")

        self.client.force_authenticate(user=self.user)

        self.video1 = Video.objects.create(title="Video 1", owner=self.user)
        self.video1.video_file.save("v1.mp4", ContentFile(b"test"), save=True)
        self.video2 = Video.objects.create(title="Video 2", owner=self.user)
        self.video2.video_file.save("v2.mp4", ContentFile(b"test"), save=True)

    def test_channel_creation_and_permissions(self):
        """Test channel creation and collaborator permissions."""
        url = reverse("channel-list")
        data = {
            "title": "My Channel",
            "description": "A cool channel",
            "is_public": True,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        channel = Channel.objects.get(slug="my-channel")
        self.assertEqual(channel.owner, self.user)

        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(
            reverse("channel-detail", kwargs={"slug": channel.slug}),
            {"title": "Hacked"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_theme_hierarchy_admin_only(self):
        """Test theme hierarchy (Admin only for creation)."""
        url = reverse("theme-list")
        response = self.client.post(url, {"title": "Science"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, {"title": "Science"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        parent_theme = Theme.objects.get(slug="science")

        response = self.client.post(url, {"title": "Physics", "parent": parent_theme.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        child_theme = Theme.objects.get(slug="physics")
        self.assertEqual(child_theme.parent, parent_theme)

    def test_playlist_video_management(self):
        """Test adding/removing/reordering videos in a playlist."""
        playlist = Playlist.objects.create(title="My Playlist", owner=self.user)

        url = reverse("playlist-add-video", kwargs={"slug": playlist.slug})
        response = self.client.post(url, {"video_id": self.video1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(url, {"video_id": self.video2.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(playlist.videos.count(), 2)

        url = reverse("playlist-reorder", kwargs={"slug": playlist.slug})
        data = {
            "positions": [
                {"video_id": self.video1.id, "position": 2},
                {"video_id": self.video2.id, "position": 1},
            ]
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        items = playlist.items.all().order_by("position")
        self.assertEqual(items[0].video, self.video2)
        self.assertEqual(items[1].video, self.video1)

    def test_playlist_password_protection(self):
        """Test playlist password protection hashing."""
        playlist = Playlist.objects.create(
            title="Secret", owner=self.user, is_public=False, password="secretpassword"
        )
        from django.contrib.auth.hashers import identify_hasher

        identify_hasher(playlist.password)

    def test_favorites(self):
        """Test adding and listing favorites."""
        url = reverse("favorite-list")
        response = self.client.post(url, {"video": self.video1.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["video"], self.video1.id)

    def test_channel_collaborator_video_edit(self):
        """Test that a channel collaborator can edit a video in that channel."""
        channel = Channel.objects.create(title="Collab Channel", owner=self.admin)
        channel.collaborators.add(self.user)

        video = Video.objects.create(
            title="Collab Video", owner=self.admin, channel=channel
        )
        video.video_file.save("collab.mp4", ContentFile(b"test"), save=True)

        self.client.force_authenticate(user=self.user)
        url = reverse("video-detail", kwargs={"slug": video.slug})
        response = self.client.patch(url, {"title": "Edited by Collab"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        video.refresh_from_db()
        self.assertEqual(video.title, "Edited by Collab")

    def test_cross_filtering(self):
        """Test GET /api/video/?channel={id}&themes={id}"""
        channel = Channel.objects.create(title="C1", owner=self.user)
        theme = Theme.objects.create(title="T1")
        video = Video.objects.create(
            title="V1", owner=self.user, channel=channel, status=Video.Status.PUBLISHED
        )
        theme.videos.add(video)

        url = reverse("video-list")
        response = self.client.get(f"{url}?channel={channel.id}&themes={theme.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], video.id)
