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


@override_settings(
    MEDIA_ROOT=TEMP_MEDIA_ROOT,
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ],
)
class VideoViewSetTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(username="other", password="password")
        self.superuser = User.objects.create_superuser(
            username="admin", password="password"
        )

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
            password="secretpassword",
        )

    def test_get_queryset_unauthenticated(self):
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
        mock_settings.user_quota_size_gb = 0  # 0 GB quota

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
        self.client.force_authenticate(user=self.user)
        url = reverse("video-stream", kwargs={"slug": self.video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "video/mp4")

    def test_stream_video_unauthenticated_restricted(self):
        url = reverse("video-stream", kwargs={"slug": self.restricted_video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_view(self):
        url = reverse("video-register-view", kwargs={"slug": self.video.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_count"], 1)

        self.video.refresh_from_db()
        self.assertEqual(self.video.view_count, 1)

    def test_unlock_restricted_video_success(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse("video-unlock", kwargs={"slug": self.restricted_video.slug})
        data = {"password": "secretpassword"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("video_url", response.data)

    def test_unlock_restricted_video_wrong_password(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse("video-unlock", kwargs={"slug": self.restricted_video.slug})
        data = {"password": "wrongpassword"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SubtitleViewSetTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(username="other", password="password")

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
        url = f"{reverse('subtitle-list')}?video_id={self.video.id}"
        response = self.client.get(url)
        response_list = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(response_list), 1)

    def test_create_subtitle_owner(self):
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
