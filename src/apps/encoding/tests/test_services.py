from unittest.mock import patch, MagicMock
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
    def setUp(self):
        self.client = RunnerClient("http://runner.local", "secret_token")

    @patch("src.apps.encoding.services.runner_client.requests.post")
    def test_execute_task_success(self, mock_post):
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
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        with self.assertRaises(ConnectionError):
            self.client.execute_task(
                video_id="1", source_url="http://source", notify_url="http://notify"
            )

    @patch("src.apps.encoding.services.runner_client.requests.get")
    def test_get_task_manifest_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"task_id": "123", "files": ["test.mp4"]}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = self.client.get_task_manifest(task_id="123")

        self.assertEqual(result, {"task_id": "123", "files": ["test.mp4"]})
        mock_get.assert_called_once()

    @patch("config.env.env")
    def test_get_runner_client(self, mock_env):
        mock_env.side_effect = lambda k, default: (
            "http://test" if k == "ENCODING_MANAGER_URL" else "test_token"
        )

        client = get_runner_client()
        self.assertEqual(client.url, "http://test")
        self.assertEqual(client.token, "test_token")


class StorageServicesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

        video_content = SimpleUploadedFile(
            "test.mp4", b"file_content", content_type="video/mp4"
        )
        self.video = Video.objects.create(
            title="Storage Test Video",
            owner=self.user,
            video_file=video_content,
        )

    def test_get_storage_path_video(self):
        path = get_storage_path_video(self.video, "test.mp4")
        self.assertTrue(path.endswith(".mp4"))
        self.assertTrue(path.startswith("videos/"))

        # Verify the new hashed structure: videos/xx/yy/uuid.mp4
        parts = path.split("/")
        self.assertEqual(len(parts), 4)
        self.assertEqual(len(parts[1]), 2)
        self.assertEqual(len(parts[2]), 2)

    def test_get_storage_path_image(self):
        path = get_storage_path_image(self.video, "test.jpg")
        self.assertTrue(path.endswith(".jpg"))
        self.assertTrue(path.startswith("thumbnails/"))

        # Verify the new hashed structure: thumbnails/xx/yy/uuid.jpg
        parts = path.split("/")
        self.assertEqual(len(parts), 4)
        self.assertEqual(len(parts[1]), 2)
        self.assertEqual(len(parts[2]), 2)
