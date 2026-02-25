from unittest.mock import patch, MagicMock
from requests.exceptions import ConnectionError

from django.test import TestCase
from django.contrib.auth import get_user_model

from src.apps.video.models import Video
from src.apps.encoding.tasks import trigger_runner_encoding_task
from src.apps.encoding.constants import ENCODING_CHOICES

User = get_user_model()


class EncodingTaskTestCase(TestCase):
    def setUp(self):
        # Create user to own the video
        self.user = User.objects.create_user(username="testuser", password="password")
        # Create a dummy video in the database
        self.video = Video.objects.create(
            title="Test Video",
            description="Testing the encoding task",
            status=Video.Status.ENCODING,
            owner=self.user,
        )

    @patch("src.apps.encoding.tasks.get_runner_client")
    def test_trigger_runner_encoding_success(self, mock_get_client):
        # Setup mock client
        mock_client = MagicMock()
        mock_client.settings.renditions = ENCODING_CHOICES
        mock_client.execute_task.return_value = {"task_id": "123", "status": "accepted"}
        mock_get_client.return_value = mock_client

        source_url = f"http://testserver/videos/{self.video.slug}.mp4"

        # Execute task
        response = trigger_runner_encoding_task(
            video_id=self.video.id,
            source_url=source_url,
        )

        # Assert client was called correctly
        mock_client.execute_task.assert_called_once_with(
            video_id=str(self.video.slug),
            source_url=source_url,
            parameters={
                "video_id": str(self.video.id),
                "slug": self.video.slug,
                "title": self.video.title,
                "encoding_choices": ENCODING_CHOICES,
            },
        )
        self.assertEqual(response, {"task_id": "123", "status": "accepted"})

    @patch("src.apps.encoding.tasks.get_runner_client")
    @patch("src.apps.encoding.tasks.trigger_runner_encoding_task.retry")
    def test_trigger_runner_encoding_retry_on_connection_error(
        self, mock_retry, mock_get_client
    ):
        # Setup mock client to raise a ConnectionError (e.g. timeout)
        mock_client = MagicMock()
        mock_client.execute_task.side_effect = ConnectionError("Connection refused")
        mock_get_client.return_value = mock_client

        # Mock retry to just raise an Exception so we can catch it and verify it was called
        mock_retry.side_effect = Exception("Retry Triggered")

        source_url = f"http://testserver/videos/{self.video.slug}.mp4"

        # Execute task and expect the retry exception
        with self.assertRaises(Exception) as context:
            trigger_runner_encoding_task(
                video_id=self.video.id,
                source_url=source_url,
            )

        self.assertEqual(str(context.exception), "Retry Triggered")
        mock_client.execute_task.assert_called_once()

        # Verify video status remains ENCODING during retry period
        video = Video.objects.get(id=self.video.id)
        self.assertEqual(video.status, Video.Status.ENCODING)
