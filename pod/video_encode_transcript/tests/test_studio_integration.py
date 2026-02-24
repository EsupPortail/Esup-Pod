"""
Studio task integration tests for Esup-Pod video creation helpers.

Run with `python manage.py test pod.video_encode_transcript.tests.test_studio_integration`
"""

import os
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from pod.video_encode_transcript.views import _create_video_from_studio_task


class StudioFlowIntegrationTests(TestCase):
    """Cover the studio task to video creation path and file relocation behavior."""

    def test_create_video_and_move_task_dir(self):
        """Create a video from a studio task and move extracted files to final media path."""
        with tempfile.TemporaryDirectory(prefix="podv4_media_") as tmp_media_root:
            # Arrange settings
            with override_settings(MEDIA_ROOT=tmp_media_root, VIDEOS_DIR="videos"):
                task_id = 42
                recording_id = 9
                user_hash = "abc123"
                src_dir = os.path.join(tmp_media_root, "tasks", str(task_id))
                os.makedirs(src_dir, exist_ok=True)

                # Create expected source files
                studio_base = os.path.join(src_dir, "studio_base.mp4")
                with open(studio_base, "wb") as f:
                    f.write(b"MP4DATA")
                # Additional file to ensure the whole folder is moved
                with open(
                    os.path.join(src_dir, "extra.txt"), "w", encoding="utf-8"
                ) as f:
                    f.write("EXTRA")

                # Fake objects returned by patched calls
                fake_video = SimpleNamespace(id=777)
                fake_recording = SimpleNamespace(
                    user=SimpleNamespace(owner=SimpleNamespace(hashkey=user_hash))
                )

                # Build a lightweight task-like object
                task = SimpleNamespace(id=task_id, recording_id=recording_id)

                with patch(
                    "pod.video_encode_transcript.views.save_basic_video",
                    return_value=fake_video,
                ) as mock_save_video, patch(
                    "pod.video_encode_transcript.views.Recording.objects.get",
                    return_value=fake_recording,
                ) as mock_get_recording:
                    # Act
                    video_id = _create_video_from_studio_task(
                        task, extracted_dir=src_dir
                    )

                # Assert save_basic_video usage
                mock_save_video.assert_called_once()
                args, kwargs = mock_save_video.call_args
                # (recording, src_file)
                self.assertEqual(args[1], studio_base)
                mock_get_recording.assert_called_once_with(id=recording_id)
                self.assertEqual(video_id, fake_video.id)

                # Destination path must include user hash and video id
                dest_dir = os.path.join(
                    tmp_media_root, "videos", user_hash, str(fake_video.id)
                )
                self.assertTrue(os.path.isdir(dest_dir))
                # Source folder removed
                self.assertFalse(os.path.exists(src_dir))
                # Files moved
                self.assertTrue(
                    os.path.isfile(os.path.join(dest_dir, "studio_base.mp4"))
                )
                with open(
                    os.path.join(dest_dir, "extra.txt"), "r", encoding="utf-8"
                ) as f:
                    self.assertEqual(f.read(), "EXTRA")
