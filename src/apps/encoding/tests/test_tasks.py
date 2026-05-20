"""
Esup-Pod - Tests for encoding tasks.

This module validates the Celery tasks responsible for triggering encoding
jobs on the remote runner manager.
"""

from unittest.mock import patch, MagicMock
from requests.exceptions import ConnectionError

from django.test import TestCase
from django.contrib.auth import get_user_model

from src.apps.video.models import Video
from src.apps.encoding.tasks import trigger_runner_encoding_task
import json

User = get_user_model()


class EncodingTaskTestCase(TestCase):
    """
    Test suite for encoded-related Celery tasks.
    """

    def setUp(self):
        """
        Setup a user and a video in DRAFT status (encoding tracked via encoding_status).
        """
        # ggignore-start
        # gitguardian:ignore
        self.user = User.objects.create_user(
            username="testuser", password="password"
        )  # nosec
        # ggignore-end
        self.video = Video.objects.create(
            title="Test Video",
            description="Testing the encoding task",
            status=Video.Status.DRAFT,
            owner=self.user,
        )

    @patch("src.apps.encoding.tasks.get_runner_client")
    def test_trigger_runner_encoding_success(self, mock_get_client):
        """Verifies that the encoding task is correctly triggered on the runner."""
        mock_client = MagicMock()
        mock_client.execute_task.return_value = {"task_id": "123", "status": "accepted"}
        mock_get_client.return_value = mock_client

        source_url = f"http://testserver/videos/{self.video.slug}.mp4"

        response = trigger_runner_encoding_task(
            video_id=self.video.id,
            source_url=source_url,
        )

        from django.conf import settings
        from config.env import env

        site_url = settings.SITE_URL.rstrip("/")
        webhook_secret = env("ENCODING_WEBHOOK_SECRET", default="")
        expected_notify_url = f"{site_url}/api/encoding/webhook/?secret={webhook_secret}&video_id={self.video.id}"

        rendition_config = {
            "360": {"resolution": "640x360", "encode_mp4": True},
            "720": {"resolution": "1280x720", "encode_mp4": True},
            "1080": {"resolution": "1920x1080", "encode_mp4": False},
        }

        mock_client.execute_task.assert_called_once_with(
            video_id=str(self.video.slug),
            source_url=source_url,
            notify_url=expected_notify_url,
            parameters={"rendition": json.dumps(rendition_config)},
        )
        self.assertEqual(response, {"task_id": "123", "status": "accepted"})

    @patch("src.apps.encoding.tasks.get_runner_client")
    @patch("src.apps.encoding.tasks.trigger_runner_encoding_task.retry")
    def test_trigger_runner_encoding_retry_on_connection_error(
        self, mock_retry, mock_get_client
    ):
        """Verifies that the task retries when a connection error occurs."""
        mock_client = MagicMock()
        mock_client.execute_task.side_effect = ConnectionError("Connection refused")
        mock_get_client.return_value = mock_client

        mock_retry.side_effect = Exception("Retry Triggered")

        source_url = f"http://testserver/videos/{self.video.slug}.mp4"

        with self.assertRaises(Exception) as context:
            trigger_runner_encoding_task(
                video_id=self.video.id,
                source_url=source_url,
            )

        self.assertEqual(str(context.exception), "Retry Triggered")
        mock_client.execute_task.assert_called_once()

        video = Video.objects.get(id=self.video.id)
        # encoding_status is set to PROCESSING at task start before the retry.
        self.assertEqual(video.encoding_status, Video.EncodingStatus.PROCESSING)
