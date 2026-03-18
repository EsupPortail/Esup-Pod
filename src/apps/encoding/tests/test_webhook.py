from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.video.models import Video

User = get_user_model()


class EncodingWebhookViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        video_content = SimpleUploadedFile(
            "test.mp4", b"file_content", content_type="video/mp4"
        )
        self.video = Video.objects.create(
            title="Webhook Test Video",
            owner=self.user,
            status=Video.Status.ENCODING,
            video_file=video_content,
        )
        self.url = reverse("encoding:webhook")
        self.url_with_secret = f"{self.url}?secret=mysecret"

    @patch("src.apps.encoding.views.webhook.env")
    def test_webhook_success(self, mock_env):
        mock_env.return_value = "mysecret"

        data = {
            "video_id": self.video.id,
            "status": "success",
            "results": {
                "duration": 120,
                "thumbnail_path": "test_thumb.jpg",
                "video_path": "test_video.mp4",
            },
        }

        response = self.client.post(self.url_with_secret, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.status, Video.Status.PUBLISHED)
        self.assertEqual(self.video.duration, 120)
        self.assertEqual(self.video.thumbnail.name, "test_thumb.jpg")
        self.assertEqual(self.video.video_file.name, "test_video.mp4")

    @patch("src.apps.encoding.views.webhook.env")
    def test_webhook_error_status(self, mock_env):
        mock_env.return_value = "mysecret"

        data = {
            "video_id": self.video.id,
            "status": "error",
            "error": "Encoding failed.",
        }

        response = self.client.post(self.url_with_secret, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "error_recorded")
        self.video.refresh_from_db()
        self.assertEqual(self.video.status, Video.Status.ERROR)

    @patch("src.apps.encoding.views.webhook.env")
    def test_webhook_missing_video_id(self, mock_env):
        mock_env.return_value = "mysecret"

        data = {
            "status": "success",
        }

        response = self.client.post(self.url_with_secret, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("src.apps.encoding.views.webhook.env")
    def test_webhook_invalid_secret(self, mock_env):
        mock_env.return_value = "mysecret"

        data = {
            "video_id": self.video.id,
            "status": "success",
        }

        response = self.client.post(self.url + "?secret=wrongsecret", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
