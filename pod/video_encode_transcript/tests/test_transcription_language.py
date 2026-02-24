"""Tests for Esup-Pod transcription language resolution fallbacks."""

from django.contrib.auth.models import User
from django.test import TestCase

from pod.completion.models import Track
from pod.video.models import Type, Video
from pod.video_encode_transcript.runner_manager import _prepare_transcription_parameters
from pod.video_encode_transcript.transcript import resolve_transcription_language


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

    def test_prepare_transcription_parameters_uses_resolved_language(self) -> None:
        """Pass the resolved fallback language into transcription runner params."""
        self.video.transcript = ""
        self.video.save(update_fields=["transcript"])
        Track.objects.create(video=self.video, lang="es")

        params = _prepare_transcription_parameters(self.video)

        self.assertEqual(params["language"], "es")
