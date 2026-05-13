"""
Esup-Pod - Tests for encoding services.

This module validates the RunnerClient communication and the storage path
generation logic.
"""

from unittest.mock import patch, MagicMock
from datetime import datetime
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
import requests

from src.apps.encoding.services.runner_client import RunnerClient, get_runner_client
from src.apps.encoding.services.storage import (
    get_storage_path_video,
    get_storage_path_image,
)
from src.apps.video.models import Video

User = get_user_model()


class RunnerClientTests(TestCase):
    """
    Test suite for the RunnerClient service.
    """

    def setUp(self):
        """
        Sets up a RunnerClient instance for testing.
        """
        self.client = RunnerClient("http://runner.local", "secret_token")

    @patch("src.apps.encoding.services.runner_client.requests.post")
    def test_execute_task_success(self, mock_post):
        """Verifies successful task execution through the runner client."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"status": "ok"}
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        result = self.client.execute_task(
            video_id="1", source_url="http://source", notify_url="http://notify"
        )

        self.assertEqual(result, {"status": "ok"})
        mock_post.assert_called_once()

    @patch("src.apps.encoding.services.runner_client.requests.post")
    def test_execute_task_failure(self, mock_post):
        """Verifies handling of request exceptions during task execution."""
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        with self.assertRaises(ConnectionError):
            self.client.execute_task(
                video_id="1", source_url="http://source", notify_url="http://notify"
            )

    @patch("src.apps.encoding.services.runner_client.requests.get")
    def test_get_task_manifest_success(self, mock_get):
        """Verifies successful retrieval of task manifest."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"task_id": "123", "files": ["test.mp4"]}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = self.client.get_task_manifest(task_id="123")

        self.assertEqual(result, {"task_id": "123", "files": ["test.mp4"]})
        mock_get.assert_called_once()

    @patch("config.env.env")
    def test_get_runner_client(self, mock_env):
        """Verifies the factory function returns a configured RunnerClient."""
        mock_env.side_effect = lambda k, default: (
            "http://test" if k == "ENCODING_MANAGER_URL" else "test_token"
        )

        client = get_runner_client()
        self.assertEqual(client.url, "http://test")
        self.assertEqual(client.token, "test_token")


class StorageServicesTests(TestCase):
    """
    Test suite for storage utility functions.
    """

    def setUp(self):
        """
        Setup a user and a video for storage testing.
        """
        # gitguardian:start-ignore
        self.user = User.objects.create_user(
            username="testuser", password="password"
        )  # nosec
        # gitguardian:end-ignore

        video_content = SimpleUploadedFile(
            "test.mp4", b"file_content", content_type="video/mp4"
        )
        self.video = Video.objects.create(
            title="Storage Test Video",
            owner=self.user,
            video_file=video_content,
        )

    @patch("django.utils.timezone.now")
    def test_get_storage_path_video(self, mock_now):
        """Verifies the generation of hashed storage paths for videos."""
        mock_now.return_value = datetime(2023, 5, 10)
        filename = "my_holiday_video.mp4"
        path = get_storage_path_video(self.video, filename)

        self.assertTrue(path.startswith("video/source/2023/05/10/"))

        name_on_disk = path.split("/")[-1]
        self.assertNotIn("my_holiday_video", name_on_disk)
        self.assertEqual(len(name_on_disk), 44)

    @patch("django.utils.timezone.now")
    def test_get_storage_path_image(self, mock_now):
        """Verifies the generation of hashed storage paths for images."""
        mock_now.return_value = datetime(2023, 5, 10)
        path = get_storage_path_image(self.video, "test.jpg")

        self.assertTrue(path.startswith("video/thumbnails/2023/05/10/"))
        self.assertTrue(path.endswith(".jpg"))

        filename_part = path.split("/")[-1].split(".")[0]
        self.assertEqual(len(filename_part), 40)
