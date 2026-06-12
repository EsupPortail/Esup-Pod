"""
Esup-Pod - Video Hyperlink API tests.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from src.apps.video.models import Video, VideoHyperlink
from src.apps.video.views.HyperlinkViewSet import VideoHyperlinkViewSet

User = get_user_model()


class VideoHyperlinkAPITests(APITestCase):
    """Test suite for VideoHyperlink API endpoints."""

    def setUp(self):
        """Set up test data for VideoHyperlink API endpoints."""
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(username="owner", password="password")
        self.other_user = User.objects.create_user(username="other", password="password")
        self.video = Video.objects.create(
            title="Test Video", owner=self.owner, status=Video.Status.PUBLISHED
        )
        self.hyperlink = VideoHyperlink.objects.create(
            video=self.video, url="https://example.com", text="Example"
        )

    def test_list_hyperlinks(self):
        """Any user can list hyperlinks for a published video."""
        view = VideoHyperlinkViewSet.as_view({"get": "list_hyperlinks"})
        request = self.factory.get("/")
        response = view(request, video_slug=self.video.slug)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_add_hyperlink_unauthorized(self):
        """Non-owners cannot add hyperlinks."""
        view = VideoHyperlinkViewSet.as_view({"post": "add_hyperlink"})
        data = {"url": "https://test.com", "text": "Test", "video": self.video.id}
        request = self.factory.post("/", data)
        force_authenticate(request, user=self.other_user)
        response = view(request, video_slug=self.video.slug)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_hyperlink_owner(self):
        """Owners can add hyperlinks."""
        view = VideoHyperlinkViewSet.as_view({"post": "add_hyperlink"})
        data = {"url": "https://test.com", "text": "Test", "video": self.video.id}
        request = self.factory.post("/", data)
        force_authenticate(request, user=self.owner)
        response = view(request, video_slug=self.video.slug)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VideoHyperlink.objects.count(), 2)

    def test_delete_hyperlink_unauthorized(self):
        """Non-owners cannot delete hyperlinks."""
        view = VideoHyperlinkViewSet.as_view({"delete": "delete_hyperlink"})
        request = self.factory.delete("/")
        force_authenticate(request, user=self.other_user)
        response = view(
            request, video_slug=self.video.slug, hyperlink_id=self.hyperlink.id
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(VideoHyperlink.objects.filter(id=self.hyperlink.id).exists())

    def test_delete_hyperlink_owner(self):
        """Owners can delete hyperlinks."""
        view = VideoHyperlinkViewSet.as_view({"delete": "delete_hyperlink"})
        request = self.factory.delete("/")
        force_authenticate(request, user=self.owner)
        response = view(
            request, video_slug=self.video.slug, hyperlink_id=self.hyperlink.id
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(VideoHyperlink.objects.filter(id=self.hyperlink.id).exists())
