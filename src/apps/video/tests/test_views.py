"""
Esup-Pod - Video application views tests.
"""

from unittest.mock import patch
import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.video.models import Video, Subtitle

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

# ggignore-start
# gitguardian:ignore
PWD = "password"
# ggignore-end


@override_settings(
    MEDIA_ROOT=TEMP_MEDIA_ROOT,
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ],
)
class VideoViewSetTests(APITestCase):
    """
    Esup-Pod - Tests for the VideoViewSet.
    """

    @classmethod
    def tearDownClass(cls):
        """Cleans up temporary media directory after tests."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """Sets up test users and various video types for API verification."""
        self.user = User.objects.create_user(username="testuser", password=PWD)  # nosec
        self.other_user = User.objects.create_user(
            username="other", password=PWD
        )  # nosec
        self.superuser = User.objects.create_superuser(
            username="admin", password=PWD
        )  # nosec

        self.video_content = SimpleUploadedFile(
            "test.mp4", b"file_content", content_type="video/mp4"
        )
        self.video = Video.objects.create(
            title="My Video",
            owner=self.user,
            video_file=self.video_content,
            status=Video.Status.PUBLISHED,
        )

        self.restricted_video = Video.objects.create(
            title="Restricted Video",
            owner=self.user,
            video_file=self.video_content,
            status=Video.Status.RESTRICTED,
            is_auth_required=True,
            password=PWD,
        )

    def test_get_queryset_unauthenticated(self):
        """Verifies that unauthenticated users only see published videos."""
        url = reverse("video-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_list = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(response_list), 1)
        self.assertEqual(response_list[0]["title"], "My Video")

    def test_get_queryset_superuser(self):
        """Verifies that superusers see all videos regardless of status."""
        self.client.force_authenticate(user=self.superuser)
        url = reverse("video-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_list = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(response_list), 2)

    @patch("src.apps.video.views.VideoViewSet.encoding_settings")
    def test_perform_create_quota_exceeded(self, mock_settings):
        """Verifies that exceeding the user quota returns a 400 error."""
        mock_settings.user_quota_size_gb = 0

        self.client.force_authenticate(user=self.user)
        url = reverse("video-list")
        data = {
            "title": "New Video",
            "video_file": SimpleUploadedFile(
                "test2.mp4", b"large content", content_type="video/mp4"
            ),
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video_file", response.data)

    def test_stream_video_owner(self):
        """Verifies that the owner can successfully stream their video."""
        self.client.force_authenticate(user=self.user)
        url = reverse("video-stream", kwargs={"slug": self.video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "video/mp4")

    def test_stream_video_unauthenticated_restricted(self):
        """Verifies that unauthenticated users cannot stream restricted videos."""
        url = reverse("video-stream", kwargs={"slug": self.restricted_video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_view(self):
        """Verifies that the register-view endpoint correctly increments view counts."""
        url = reverse("video-register-view", kwargs={"slug": self.video.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_count"], 1)

        self.video.refresh_from_db()
        self.assertEqual(self.video.view_count, 1)

    def test_unlock_restricted_video_success(self):
        """Verifies that a correct password unlocks a restricted video for a visitor."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("video-unlock", kwargs={"slug": self.restricted_video.slug})
        data = {"password": PWD}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("video_url", response.data)

    def test_unlock_restricted_video_wrong_password(self):
        """Verifies that a wrong password fails to unlock a restricted video."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("video-unlock", kwargs={"slug": self.restricted_video.slug})
        data = {"password": "wrongpassword"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SubtitleViewSetTests(APITestCase):
    """
    Esup-Pod - Tests for the SubtitleViewSet.
    """

    @classmethod
    def tearDownClass(cls):
        """Cleans up temporary media directory after tests."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """Sets up a video and a subtitle for serialization testing."""
        self.user = User.objects.create_user(username="testuser", password=PWD)  # nosec
        self.other_user = User.objects.create_user(
            username="other", password=PWD
        )  # nosec

        self.video = Video.objects.create(
            title="My Video",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )

        self.subtitle_content = SimpleUploadedFile(
            "sub.vtt",
            b"WEBVTT\n\n00:00.000 --> 00:05.000\nHello",
            content_type="text/vtt",
        )
        self.subtitle = Subtitle.objects.create(
            video=self.video, language="en", file=self.subtitle_content
        )

    def test_get_queryset_filter_by_video(self):
        """Verifies that subtitles can be filtered by video ID in the API."""
        url = f"{reverse('subtitle-list')}?video_id={self.video.id}"
        response = self.client.get(url)
        response_list = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(response_list), 1)

    def test_create_subtitle_owner(self):
        """Verifies that the video owner can upload new subtitles."""
        self.client.force_authenticate(user=self.user)
        url = reverse("subtitle-list")
        data = {
            "video": self.video.id,
            "language": "fr",
            "file": SimpleUploadedFile(
                "fr.vtt", b"WEBVTT\n\nBonjour", content_type="text/vtt"
            ),
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_subtitle_not_owner(self):
        """Verifies that a non-owner cannot upload subtitles to someone else's video."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("subtitle-list")
        data = {
            "video": self.video.id,
            "language": "es",
            "file": SimpleUploadedFile(
                "es.vtt", b"WEBVTT\n\nHola", content_type="text/vtt"
            ),
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
