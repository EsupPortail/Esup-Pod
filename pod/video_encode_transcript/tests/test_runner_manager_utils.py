"""Regression tests for Runner Manager artifact persistence."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from pod.video.models import Type, Video
from pod.video_encode_transcript.runner_manager_utils import (
    FILEPICKER,
    CustomImageModel,
    remote_video_part,
)


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
    @patch(
        "pod.video_encode_transcript.runner_manager_utils.add_encoding_log"
    )
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
        mock_check_file.assert_called_once_with(
            "/tmp/media/videos/0001/overview.vtt"
        )
        mock_import_remote_video.assert_called_once()
        mock_add_encoding_log.assert_any_call(
            self.video.id,
            "attach existing overview: /tmp/media/videos/0001/overview.vtt",
        )
