"""Unit tests for the REST views helpers in video_encode_transcript."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.permissions import AllowAny
from rest_framework.test import APIRequestFactory

from pod.recorder.models import Recorder, Recording
from pod.video.models import Type, Video
from pod.video_encode_transcript import rest_views
from pod.video_encode_transcript.models import EncodingAudio

# ggignore-start
# gitguardian:ignore
PWD = "secret"  # nosec
# ggignore-end


class RestViewsHelpersTests(unittest.TestCase):
    """Validate the helper functions that sanitize paths used by REST views."""

    def test_safe_temp_media_path_allows_files_under_media_temp(self) -> None:
        """Return a normalized path inside MEDIA_ROOT/temp for a safe filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = os.path.join(tmpdir, "temp")
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, "subtitle.vtt")
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write("WEBVTT")

            with patch.object(rest_views, "MEDIA_ROOT", tmpdir):
                resolved_path = rest_views._safe_temp_media_path("subtitle.vtt")

            self.assertEqual(resolved_path, os.path.realpath(file_path))

    def test_safe_temp_media_path_rejects_path_traversal(self) -> None:
        """Reject filenames that escape the temporary media directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(rest_views, "MEDIA_ROOT", tmpdir):
                with self.assertRaises(Exception):
                    rest_views._safe_temp_media_path("../escaped.vtt")

    def test_get_safe_video_output_allows_relative_paths(self) -> None:
        """Resolve a relative path inside the recorder base directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(rest_views, "MEDIA_ROOT", tmpdir), patch.object(
                rest_views, "DEFAULT_RECORDER_PATH", tmpdir
            ):
                safe_path = rest_views._get_safe_video_output(
                    {"video_output": "records/output.mp4"}
                )

            self.assertEqual(safe_path, os.path.join(tmpdir, "records", "output.mp4"))

    def test_get_safe_video_output_rejects_absolute_or_parent_paths(self) -> None:
        """Reject absolute and traversal paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(rest_views, "MEDIA_ROOT", tmpdir), patch.object(
                rest_views, "DEFAULT_RECORDER_PATH", tmpdir
            ):
                with self.assertRaises(Exception):
                    rest_views._get_safe_video_output({"video_output": "/tmp/evil.mp4"})
                with self.assertRaises(Exception):
                    rest_views._get_safe_video_output({"video_output": "../evil.mp4"})


class RestViewsApiTests(TestCase):
    """Validate the API views exposed by the module."""

    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="tester", password=PWD)
        self.user.is_staff = True
        self.user.save()
        self.video_type = Type.objects.create(title="Type", slug="type")
        self.video = Video.objects.create(
            title="Sample video",
            owner=self.user,
            type=self.video_type,
            encoding_in_progress=False,
        )

    def test_launch_encode_view_sets_launch_flag(self) -> None:
        """Launching encoding should mark the video for processing."""
        request = self.factory.get("/encode/", {"slug": self.video.slug})

        with patch.object(
            rest_views.launch_encode_view.cls, "permission_classes", [AllowAny]
        ):
            with patch.object(Video, "save", autospec=True) as save_mock:
                response = rest_views.launch_encode_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(save_mock.call_args[0][0].launch_encode)

    def test_launch_transcript_view_starts_transcription(self) -> None:
        """Launching transcript should invoke the transcription starter."""
        audio_file = SimpleUploadedFile("audio.mp3", b"data", content_type="audio/mpeg")
        EncodingAudio.objects.create(
            name="audio",
            video=self.video,
            encoding_format="audio/mp3",
            source_file=audio_file,
        )
        request = self.factory.get("/transcript/", {"slug": self.video.slug})

        with patch.object(
            rest_views.launch_transcript_view.cls, "permission_classes", [AllowAny]
        ):
            with patch.object(
                rest_views, "start_transcript", create=True
            ) as start_transcript:
                rest_views.launch_transcript_view(request)

        start_transcript.assert_called_once_with(self.video.id, threaded=True)

    def test_store_remote_encoded_video_studio_sends_safe_output(self) -> None:
        """Studio encoding should forward a safe output path to the encoder."""
        recorder_type = Type.objects.create(title="Recorder Type", slug="recorder-type")
        recorder = Recorder.objects.create(
            name="studio-recorder",
            address_ip="127.0.0.1",
            user=self.user,
            recording_type="studio",
            type=recorder_type,
        )
        recording = Recording.objects.create(
            recorder=recorder,
            user=self.user,
            title="studio recording",
            type="studio",
            source_file="/tmp/recording.mp4",
        )
        payload = {
            "video_output": "records/output.mp4",
            "msg": "encoded",
        }
        request = self.factory.post(
            "/studio/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_HOST="example.com",
        )
        request.GET = request.GET.copy()
        request.GET["recording_id"] = str(recording.id)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(rest_views, "MEDIA_ROOT", tmpdir), patch.object(
                rest_views, "DEFAULT_RECORDER_PATH", tmpdir
            ), patch.object(
                rest_views.store_remote_encoded_video_studio.cls,
                "permission_classes",
                [AllowAny],
            ), patch(
                "pod.video_encode_transcript.encode.store_encoding_studio_info"
            ) as store_info:
                response = rest_views.store_remote_encoded_video_studio(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "ok")
        store_info.assert_called_once()
        self.assertEqual(store_info.call_args[0][0], str(recording.id))
        self.assertEqual(
            store_info.call_args[0][1],
            os.path.join(tmpdir, "records", "output.mp4"),
        )
        self.assertEqual(store_info.call_args[0][2], "encoded")
