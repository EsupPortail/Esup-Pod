"""Regression tests for Runner Manager artifact persistence."""

import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from pod.video.models import Type, Video
from pod.video_encode_transcript.models import EncodingLog, Task
from pod.video_encode_transcript.runner_manager_utils import (
    FILEPICKER,
    CustomImageModel,
    remote_video_part,
)
from pod.video_encode_transcript.views import _finalize_task_import


class RunnerManagerArtifactPersistenceTests(TestCase):
    """Ensure importing one artifact does not overwrite another one."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        self.user = User.objects.create(username="runner-artifact-owner")
        self.video = Video.objects.create(
            title="Runner artifact video",
            owner=self.user,
            video="runner-artifact.mp4",
            type=Type.objects.get(id=1),
        )

    def _create_thumbnail(self) -> CustomImageModel:
        kwargs = {"file": "files/runner-thumbnail.png"}
        if FILEPICKER:
            kwargs.update(
                folder=self.video.get_or_create_video_folder(),
                created_by=self.user,
            )
        return CustomImageModel.objects.create(**kwargs)

    @override_settings(MEDIA_ROOT="/tmp/media")
    @patch("pod.video_encode_transcript.runner_manager_utils.add_encoding_log")
    @patch(
        "pod.video_encode_transcript.runner_manager_utils.import_remote_video",
        return_value="",
    )
    @patch(
        "pod.video_encode_transcript.runner_manager_utils.check_file",
        return_value=True,
    )
    def test_overview_import_preserves_concurrently_attached_thumbnail(
        self,
        mock_check_file,
        mock_import_remote_video,
        mock_add_encoding_log,
    ) -> None:
        """A stale Video instance must not clear a newly attached thumbnail."""
        stale_video = Video.objects.get(id=self.video.id)
        thumbnail = self._create_thumbnail()
        Video.objects.filter(id=self.video.id).update(thumbnail=thumbnail)

        info_video = {
            "has_stream_video": True,
            "encode_video": [
                {
                    "encoding_format": "video/mp4",
                    "filename": "encoded-video.mp4",
                    "rendition": "720",
                }
            ],
            "has_stream_thumbnail": False,
        }

        remote_video_part(stale_video, info_video, "/tmp/media/videos/0001")

        self.video.refresh_from_db()
        self.assertEqual(self.video.thumbnail_id, thumbnail.id)
        self.assertEqual(self.video.overview.name, "videos/0001/overview.vtt")
        mock_check_file.assert_called_once_with("/tmp/media/videos/0001/overview.vtt")
        mock_import_remote_video.assert_called_once()
        mock_add_encoding_log.assert_any_call(
            self.video.id,
            "attach existing overview: /tmp/media/videos/0001/overview.vtt",
        )

    @patch("pod.video_encode_transcript.runner_manager_utils.USE_NOTIFICATIONS", False)
    @patch("pod.video_encode_transcript.runner_manager_utils.USE_TRANSCRIPTION", False)
    @patch(
        "pod.video_encode_transcript.runner_manager_utils.EMAIL_ON_ENCODING_COMPLETION",
        False,
    )
    def test_completed_import_preserves_thumbnail_after_audio_and_finalization(self):
        """A complete Runner import must retain the selected image in the database."""
        task = Task.objects.create(video=self.video, type="encoding", status="running")
        info_video = {
            "duration": 47,
            "has_stream_video": True,
            "has_stream_audio": True,
            "has_stream_thumbnail": True,
            "encode_video": [
                {
                    "encoding_format": "video/mp4",
                    "filename": "720p_runner.mp4",
                    "rendition": "1280x720",
                }
            ],
            "encode_audio": {
                "encoding_format": "audio/mp3",
                "filename": "audio_runner.mp3",
            },
            "encode_thumbnail": [
                {"filename": f"thumbnail_{index}.jpg"} for index in (2, 0, 1)
            ],
        }
        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            output_dir = Path(media_root) / f"{self.video.id:04d}"
            output_dir.mkdir()
            (output_dir / "info_video.json").write_text(
                json.dumps(info_video), encoding="utf-8"
            )
            (output_dir / "720p_runner.mp4").write_bytes(b"encoded video")
            (output_dir / "audio_runner.mp3").write_bytes(b"encoded audio")
            (output_dir / "overview.vtt").write_text("WEBVTT\n", encoding="utf-8")
            image_fixture = Path(__file__).with_name("testimage.jpg")
            for entry in info_video["encode_thumbnail"]:
                shutil.copyfile(image_fixture, output_dir / entry["filename"])

            _finalize_task_import(task, str(output_dir), "")

            self.video.refresh_from_db()
            task.refresh_from_db()
            self.assertEqual(task.status, "completed")
            self.assertFalse(self.video.encoding_in_progress)
            self.assertEqual(self.video.duration, 47)
            self.assertEqual(
                self.video.overview.name, f"{self.video.id:04d}/overview.vtt"
            )
            self.assertIsNotNone(self.video.thumbnail_id)
            thumbnail = CustomImageModel.objects.get(id=self.video.thumbnail_id)
            self.assertEqual(Path(thumbnail.file.name).name, "thumbnail_1.jpg")
            self.assertTrue(thumbnail.file_exist())
            self.assertEqual(self.video.encodingvideo_set.count(), 1)
            self.assertEqual(self.video.encodingaudio_set.count(), 1)
            encoding_log = EncodingLog.objects.get(video=self.video).log
            self.assertIn("- persisted_thumbnail_id:\n%s" % thumbnail.id, encoding_log)
            self.assertIn("End:", encoding_log)
