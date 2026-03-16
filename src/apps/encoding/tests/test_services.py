from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
import requests

from src.apps.encoding.services.runner_client import RunnerClient, get_runner_client
from src.apps.encoding.services.storage import (
    get_storage_path_video,
    get_storage_path_image,
    move_video_files_to_new_owner,
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
        self.user2 = User.objects.create_user(username="otheruser", password="password")

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
        self.assertTrue(path.endswith(f"{self.video.slug}.mp4"))
        self.assertIn("testuser", path)

    def test_get_storage_path_image(self):
        path = get_storage_path_image(self.video, "test.jpg")
        self.assertIn(self.video.slug, path)
        self.assertTrue(path.endswith(".jpg"))

    @patch("src.apps.encoding.services.storage.shutil.move")
    @patch("src.apps.encoding.services.storage.os.path.exists")
    @patch("src.apps.encoding.services.storage.os.makedirs")
    def test_move_video_files_to_new_owner(self, mock_makedirs, mock_exists, mock_move):
        mock_exists.return_value = True

        self.video.video_file.name = f"videos/{self.user.owner.hashkey}/1/test.mp4"
        self.video.thumbnail.name = f"videos/{self.user.owner.hashkey}/1/thumb.jpg"

        move_video_files_to_new_owner(self.video, self.user, self.user2)

        mock_move.assert_called_once()
        self.assertIn(self.user2.owner.hashkey, self.video.video_file.name)
        self.assertIn(self.user2.owner.hashkey, self.video.thumbnail.name)
