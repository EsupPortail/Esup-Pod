"""
Tests for the process_tasks management command runner payloads for Esup-Pod.

Run with `python manage.py test pod.video_encode_transcript.tests.test_process_tasks`
"""

import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from pod.video_encode_transcript.management.commands.process_tasks import Command


class ProcessTasksCommandPayloadTests(SimpleTestCase):
    """Verify process_tasks delegates payload building to shared runner helpers."""

    def setUp(self) -> None:
        self.command = Command()
        self.site = SimpleNamespace(domain="example.com")
        self.runner_manager = SimpleNamespace(name="runner-a")

    @patch(
        "pod.video_encode_transcript.runner_manager.get_list_rendition",
        return_value={
            360: {
                "resolution": "640x360",
                "video_bitrate": "750k",
                "audio_bitrate": "96k",
                "encode_mp4": True,
            }
        },
    )
    @patch("pod.video_encode_transcript.runner_manager._attach_dressing_info")
    @patch("pod.video_encode_transcript.runner_manager._attach_cut_info")
    @patch(
        "pod.video_encode_transcript.management.commands.process_tasks.submit_runner_task_to_managers"
    )
    def test_submit_encoding_task_includes_video_metadata(
        self,
        mock_submit_runner_task_to_managers,
        mock_attach_cut_info,
        mock_attach_dressing_info,
        mock_get_list_rendition,
    ) -> None:
        """Encoding tasks should build a shared payload including video metadata."""
        mock_submit_runner_task_to_managers.return_value = True

        video = SimpleNamespace(
            id=17,
            slug="sample-video",
            title="Sample video",
            video="videos/sample.mp4",
        )

        result = self.command._submit_encoding_task(
            video, self.site, [self.runner_manager]
        )

        self.assertTrue(result)
        payload = mock_submit_runner_task_to_managers.call_args.kwargs["data"]
        self.assertEqual(payload["parameters"]["video_id"], 17)
        self.assertEqual(payload["parameters"]["video_slug"], "sample-video")
        self.assertEqual(payload["parameters"]["video_title"], "Sample video")
        self.assertEqual(
            json.loads(payload["parameters"]["rendition"]),
            {
                "360": {
                    "resolution": "640x360",
                    "video_bitrate": "750k",
                    "audio_bitrate": "96k",
                    "encode_mp4": True,
                }
            },
        )
        mock_get_list_rendition.assert_called_once_with()
        mock_attach_cut_info.assert_called_once()
        mock_attach_dressing_info.assert_called_once()
        self.assertEqual(
            payload["source_url"], "http://example.com/media/videos/sample.mp4"
        )
        self.assertEqual(
            payload["notify_url"], "http://example.com/runner/notify_task_end/"
        )
        mock_submit_runner_task_to_managers.assert_called_once_with(
            runner_managers=[self.runner_manager],
            data=payload,
            task_type="encoding",
            source_type="video",
            source_id=17,
        )

    @override_settings(
        TRANSCRIPTION_TYPE="whisper",
        TRANSCRIPTION_NORMALIZE=True,
    )
    @patch(
        "pod.video_encode_transcript.management.commands.process_tasks.submit_runner_task_to_managers"
    )
    @patch(
        "pod.video_encode_transcript.transcript.resolve_transcription_language",
        return_value="fr",
    )
    def test_submit_transcription_task_includes_video_metadata(
        self, mock_resolve_transcription_language, mock_submit_runner_task_to_managers
    ) -> None:
        """Transcription tasks should build a shared payload including metadata."""
        mock_submit_runner_task_to_managers.return_value = True

        video = Mock(
            id=23,
            slug="transcript-video",
            title="Transcript video",
            transcript="fr",
            duration=12.5,
            video="videos/transcript.mp4",
        )
        video.get_video_mp3.return_value = None

        result = self.command._submit_transcription_task(
            video, self.site, [self.runner_manager]
        )

        self.assertTrue(result)
        payload = mock_submit_runner_task_to_managers.call_args.kwargs["data"]
        self.assertEqual(payload["parameters"]["language"], "fr")
        self.assertEqual(payload["parameters"]["duration"], 12.5)
        self.assertTrue(payload["parameters"]["normalize"])
        self.assertEqual(payload["parameters"]["model_type"], "whisper")
        self.assertEqual(payload["parameters"]["video_id"], 23)
        self.assertEqual(payload["parameters"]["video_slug"], "transcript-video")
        self.assertEqual(payload["parameters"]["video_title"], "Transcript video")
        self.assertEqual(
            payload["source_url"], "http://example.com/media/videos/transcript.mp4"
        )
        mock_submit_runner_task_to_managers.assert_called_once_with(
            runner_managers=[self.runner_manager],
            data=payload,
            task_type="transcription",
            source_type="video",
            source_id=23,
        )
        mock_resolve_transcription_language.assert_called_once_with(video)

    @override_settings(
        MEDIA_ROOT="/srv/media",
        MEDIA_URL="/media/",
    )
    @patch(
        "pod.video_encode_transcript.management.commands.process_tasks.submit_runner_task_to_managers"
    )
    @patch(
        "pod.video_encode_transcript.runner_manager.get_list_rendition",
        return_value={
            720: {
                "resolution": "1280x720",
                "video_bitrate": "2000k",
                "audio_bitrate": "128k",
                "encode_mp4": False,
            }
        },
    )
    def test_submit_studio_task_uses_shared_source_url_and_payload(
        self, mock_get_list_rendition, mock_submit_runner_task_to_managers
    ) -> None:
        """Studio tasks should reuse shared source URL and payload builders."""
        mock_submit_runner_task_to_managers.return_value = True

        recording = SimpleNamespace(id=31, source_file="/srv/media/studio/source.xml")

        result = self.command._submit_studio_task(
            recording, self.site, [self.runner_manager]
        )

        self.assertTrue(result)
        payload = mock_submit_runner_task_to_managers.call_args.kwargs["data"]
        self.assertEqual(
            payload["source_url"], "http://example.com/media/studio/source.xml"
        )
        self.assertEqual(
            json.loads(payload["parameters"]["rendition"]),
            {
                "720": {
                    "resolution": "1280x720",
                    "video_bitrate": "2000k",
                    "audio_bitrate": "128k",
                    "encode_mp4": False,
                }
            },
        )
        self.assertNotIn("video_id", payload["parameters"])
        mock_get_list_rendition.assert_called_once_with()
        mock_submit_runner_task_to_managers.assert_called_once_with(
            runner_managers=[self.runner_manager],
            data=payload,
            task_type="studio",
            source_type="recording",
            source_id=31,
        )
