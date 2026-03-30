"""Tests for Esup-Pod transcription language resolution fallbacks."""

from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings

from pod.completion.models import Track
from pod.video.models import Type, Video
from pod.video_encode_transcript.runner_manager import (
    _prepare_encoding_parameters,
    _prepare_transcription_parameters,
)
from pod.video_encode_transcript.transcript import resolve_transcription_language


class RunnerManagerEncodingParametersTests(SimpleTestCase):
    """Validate metadata attachment for runner manager encoding payloads."""

    @patch(
        "pod.video_encode_transcript.runner_manager._build_rendition_parameters",
        return_value={"rendition": "{}"},
    )
    @patch("pod.video_encode_transcript.runner_manager._attach_cut_info")
    @patch("pod.video_encode_transcript.runner_manager._attach_dressing_info")
    def test_prepare_encoding_parameters_attaches_video_metadata(
        self,
        mock_attach_dressing_info,
        mock_attach_cut_info,
        mock_build_rendition_parameters,
    ) -> None:
        """Include lightweight video metadata for video encoding tasks."""
        video = SimpleNamespace(
            id=17,
            slug="sample-video",
            title="Sample video",
        )

        params = _prepare_encoding_parameters(video=video)

        self.assertEqual(params["rendition"], "{}")
        self.assertEqual(params["video_id"], 17)
        self.assertEqual(params["video_slug"], "sample-video")
        self.assertEqual(params["video_title"], "Sample video")
        mock_build_rendition_parameters.assert_called_once_with()
        mock_attach_cut_info.assert_called_once()
        mock_attach_dressing_info.assert_called_once()

    @patch(
        "pod.video_encode_transcript.runner_manager._build_rendition_parameters",
        return_value={"rendition": "{}"},
    )
    @patch("pod.video_encode_transcript.runner_manager._attach_cut_info")
    @patch("pod.video_encode_transcript.runner_manager._attach_dressing_info")
    def test_prepare_encoding_parameters_skips_video_specific_data_for_studio_tasks(
        self,
        mock_attach_dressing_info,
        mock_attach_cut_info,
        mock_build_rendition_parameters,
    ) -> None:
        """Keep studio encoding payloads limited to rendition parameters."""
        params = _prepare_encoding_parameters(video=None)

        self.assertEqual(params, {"rendition": "{}"})
        mock_build_rendition_parameters.assert_called_once_with()
        mock_attach_cut_info.assert_not_called()
        mock_attach_dressing_info.assert_not_called()


class TranscriptionLanguageResolutionTests(TestCase):
    """Validate fallback behavior when transcription language is missing."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Create a baseline video object used by each language fallback test."""
        owner = User.objects.create(username="lang_resolution_owner")
        videotype = Type.objects.create(title="others")
        self.video = Video.objects.create(
            title="video-lang-resolution",
            type=videotype,
            owner=owner,
            video="test.mp4",
            main_lang="fr",
        )

    def test_resolve_transcription_language_prefers_video_transcript(self) -> None:
        """Use video.transcript when it is explicitly set."""
        self.video.transcript = "en"
        self.video.save(update_fields=["transcript"])
        Track.objects.create(video=self.video, lang="de")

        self.assertEqual(resolve_transcription_language(self.video), "en")

    def test_resolve_transcription_language_uses_track_when_transcript_empty(
        self,
    ) -> None:
        """Fallback to the first available track language when transcript is empty."""
        self.video.transcript = ""
        self.video.save(update_fields=["transcript"])
        Track.objects.create(video=self.video, lang="de")

        self.assertEqual(resolve_transcription_language(self.video), "de")

    @override_settings(
        TRANSCRIPTION_TYPE="whisper",
        TRANSCRIPTION_NORMALIZE=True,
    )
    def test_prepare_transcription_parameters_uses_resolved_language(self) -> None:
        """Pass the resolved fallback language and metadata into runner params."""
        self.video.transcript = ""
        self.video.duration = 12.5
        self.video.save(update_fields=["transcript", "duration"])
        Track.objects.create(video=self.video, lang="es")

        params = _prepare_transcription_parameters(self.video)

        self.assertEqual(params["language"], "es")
        self.assertEqual(params["duration"], 12.5)
        self.assertTrue(params["normalize"])
        self.assertEqual(params["model_type"], "whisper")
        self.assertEqual(params["video_id"], self.video.id)
        self.assertEqual(params["video_slug"], self.video.slug)
        self.assertEqual(params["video_title"], self.video.title)

    @patch(
        "pod.video_encode_transcript.transcript.resolve_transcription_language",
        side_effect=RuntimeError("runner unavailable"),
    )
    def test_prepare_transcription_parameters_falls_back_to_legacy_lang_key(
        self, mock_resolve_transcription_language
    ) -> None:
        """Keep the legacy payload shape when language resolution fails."""
        self.video.transcript = "en"
        self.video.save(update_fields=["transcript"])

        params = _prepare_transcription_parameters(self.video)

        self.assertEqual(params["lang"], "en")
        self.assertEqual(params["video_id"], self.video.id)
        self.assertEqual(params["video_slug"], self.video.slug)
        self.assertEqual(params["video_title"], self.video.title)
        self.assertNotIn("language", params)
        mock_resolve_transcription_language.assert_called_once_with(self.video)
