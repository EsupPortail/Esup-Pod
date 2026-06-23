"""
Esup-Pod - Tests for encoding webhooks.

This module validates the processing of callbacks from the runner manager,
ensuring that video status and files are correctly updated upon task completion.
"""

import tempfile
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files import File
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.video.models import Video

User = get_user_model()


class EncodingWebhookViewTests(APITestCase):
    """
    Test suite for the runner manager webhook endpoint.
    """

    def setUp(self):
        """
        Setup a video in DRAFT status (encoding tracked via encoding_status).
        """
        self.user = User.objects.create_user(username="testuser", password="password")
        video_content = SimpleUploadedFile(
            "test.mp4", b"file_content", content_type="video/mp4"
        )
        self.video = Video.objects.create(
            title="Webhook Test Video",
            owner=self.user,
            status=Video.Status.DRAFT,
            video_file=video_content,
        )
        self.url = reverse("encoding:webhook")
        self.url_with_secret = f"{self.url}?secret=mysecret"

    @patch("src.apps.encoding.views.webhook.env")
    @patch("src.apps.encoding.views.webhook.get_runner_client")
    def test_webhook_success(self, mock_get_client, mock_env):
        """Verifies successful processing of a 'completed' status webhook."""
        mock_env.return_value = "mysecret"

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.get_task_manifest.return_value = {
            "task_id": "test-task-123",
            "files": ["720p_video.mp4", "test_0.png", "task_metadata.json"],
        }

        def mock_download(task_id, file_path):
            """Internal helper to mock media downloads during encoded video processing."""
            lf = tempfile.NamedTemporaryFile(delete=False)
            lf.write(b"dummy content")
            lf.flush()
            lf.seek(0)
            filename = file_path.split("/")[-1]
            return File(lf, name=filename)

        mock_client.download_task_file_to_temp.side_effect = mock_download

        data = {
            "task_id": "test-task-123",
            "video_id": self.video.id,
            "status": "completed",
        }

        original_file_name = self.video.video_file.name

        response = self.client.post(self.url_with_secret, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        # Visibility remains DRAFT (encoding does not publish automatically anymore).
        self.assertEqual(self.video.status, Video.Status.DRAFT)
        self.assertEqual(self.video.encoding_status, Video.EncodingStatus.DONE)

        self.assertEqual(self.video.video_file.name, original_file_name)
        self.assertTrue(self.video.overview.name.endswith(".png"))

        from src.apps.encoding.models import EncodingVideo

        encodings = EncodingVideo.objects.filter(video=self.video)
        self.assertEqual(encodings.count(), 1)
        self.assertEqual(encodings.first().resolution, "720p")

    @patch("src.apps.encoding.views.webhook.env")
    def test_webhook_error_status(self, mock_env):
        """Verifies that an 'error' status in the webhook updates the video status accordingly."""
        mock_env.return_value = "mysecret"

        data = {
            "task_id": "test-task-123",
            "video_id": self.video.id,
            "status": "error",
            "error": "Encoding failed.",
        }

        response = self.client.post(self.url_with_secret, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "error_recorded")
        self.video.refresh_from_db()
        # Visibility (DRAFT) is preserved; only encoding_status is set to ERROR.
        self.assertEqual(self.video.status, Video.Status.DRAFT)
        self.assertEqual(self.video.encoding_status, Video.EncodingStatus.ERROR)

    @patch("src.apps.encoding.views.webhook.env")
    def test_webhook_missing_video_id(self, mock_env):
        """Verifies that a 400 error is returned when video_id is missing."""
        mock_env.return_value = "mysecret"

        data = {
            "task_id": "test-task-123",
            "status": "success",
        }

        response = self.client.post(self.url_with_secret, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("src.apps.encoding.views.webhook.env")
    def test_webhook_invalid_secret(self, mock_env):
        """Verifies that a 401 error is returned when the secret is invalid."""
        mock_env.return_value = "mysecret"

        data = {
            "task_id": "test-task-123",
            "video_id": self.video.id,
            "status": "success",
        }

        response = self.client.post(self.url + "?secret=wrongsecret", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
