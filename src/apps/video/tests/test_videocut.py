"""
Esup-Pod - Video Cut API tests.
"""

from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from src.apps.video.apps import sync_metadata
from src.apps.video.models import Video, VideoCut
from src.apps.video.views.VideoCutViewSet import VideoCutViewSet

User = get_user_model()


class VideoCutAPITests(APITestCase):
    """Test suite for VideoCut API endpoints."""

    def setUp(self):
        """Set up test data for VideoCut API endpoints."""
        sync_metadata(sender=None)
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(
            username="owner",
            password="password",
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="password",
        )
        self.video = Video.objects.create(
            title="Test Video", owner=self.owner, slug="test-video"
        )
        # Patch video_settings.use_cut to True
        patcher = patch(
            "src.apps.video.views.VideoCutViewSet.video_settings.use_cut", True
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_create_cut_unauthorized(self):
        """Non-owners cannot create a cut."""
        view = VideoCutViewSet.as_view({"post": "create"})
        data = {
            "video": self.video.id,
            "time_start": 5,
            "time_end": 20,
        }
        request = self.factory.post("/", data)
        force_authenticate(request, user=self.other_user)
        response = view(request, video_slug=self.video.slug)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_cut_owner(self):
        """Owner can create a cut."""
        view = VideoCutViewSet.as_view({"post": "create"})
        data = {
            "video": self.video.id,
            "time_start": 15,
            "time_end": 60,
        }
        request = self.factory.post("/", data)
        force_authenticate(request, user=self.owner)
        response = view(request, video_slug=self.video.slug)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VideoCut.objects.filter(video=self.video).count(), 1)

    def test_replace_cut(self):
        """Creating a new cut replaces the previous one."""
        VideoCut.objects.create(video=self.video, time_start=10, time_end=50)

        view = VideoCutViewSet.as_view({"post": "create"})
        data = {
            "video": self.video.id,
            "time_start": 20,
            "time_end": 70,
        }
        request = self.factory.post("/", data)
        force_authenticate(request, user=self.owner)
        response = view(request, video_slug=self.video.slug)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VideoCut.objects.filter(video=self.video).count(), 1)
        cut = VideoCut.objects.get(video=self.video)
        self.assertEqual(cut.time_start, 20)
        self.assertEqual(cut.time_end, 70)

    def test_create_cut_invalid_times(self):
        """Invalid time range should be rejected."""
        view = VideoCutViewSet.as_view({"post": "create"})
        data = {
            "video": self.video.id,
            "time_start": 50,
            "time_end": 10,
        }
        request = self.factory.post("/", data)
        force_authenticate(request, user=self.owner)
        response = view(request, video_slug=self.video.slug)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
