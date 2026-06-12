"""
Esup-Pod - Completion tasks tests.
"""

from unittest.mock import patch, mock_open
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from src.apps.video.models import Video, Subtitle
from src.apps.completion.models import EnrichModelQueue
from src.apps.completion.tasks import process_enrich_model_queue

User = get_user_model()


class EnrichModelQueueTaskTests(TestCase):
    """Tests for the EnrichModelQueue Celery task."""

    def setUp(self):
        """Set up the test environment."""
        self.user = User.objects.create_user(username="owner", password="password")
        self.video = Video.objects.create(
            title="Test Video",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )
        self.subtitle_content = SimpleUploadedFile(
            "sub.vtt",
            b"WEBVTT\n\n00:00.000 --> 00:05.000\nHello World",
            content_type="text/vtt",
        )
        self.subtitle = Subtitle.objects.create(
            video=self.video, language="en", file=self.subtitle_content
        )
        self.queue_item = EnrichModelQueue.objects.create(
            video=self.video, track=self.subtitle, status="pending"
        )

    @patch("src.apps.completion.tasks.completion_settings")
    def test_process_disabled(self, mock_settings):
        """Task should return immediately if active_model_enrich is False."""
        mock_settings.active_model_enrich = False
        process_enrich_model_queue()
        self.queue_item.refresh_from_db()
        self.assertEqual(self.queue_item.status, "pending")

    @patch("src.apps.completion.tasks.subprocess.run")
    @patch("src.apps.completion.tasks.webvtt")
    @patch("src.apps.completion.tasks.completion_settings")
    def test_process_success(self, mock_settings, mock_webvtt, mock_subprocess_run):
        """Task should successfully process the queue and mark it as done."""
        mock_settings.active_model_enrich = True
        mock_settings.transcription_type = "VOSK"
        mock_settings.model_compile_dir = "/tmp/compile"
        mock_settings.transcription_model_param = {}

        # Mock webvtt to return a fake caption
        class FakeCaption:
            """A fake caption for testing."""

            text = "Hello World"

        mock_webvtt.read.return_value = [FakeCaption()]

        # Patch open to avoid writing to actual filesystem, and patch delay to prevent infinite recursive loop in tests
        with patch("src.apps.completion.tasks.open", mock_open()), patch(
            "src.apps.completion.tasks.process_enrich_model_queue.delay"
        ):
            process_enrich_model_queue()

        self.queue_item.refresh_from_db()
        self.assertEqual(self.queue_item.status, "done")
        mock_subprocess_run.assert_called_once()
        mock_webvtt.read.assert_called_once()

    @patch("src.apps.completion.tasks.webvtt")
    @patch("src.apps.completion.tasks.completion_settings")
    def test_process_error_handling(self, mock_settings, mock_webvtt):
        """Task should catch exceptions and mark queue item as error."""
        mock_settings.active_model_enrich = True
        mock_settings.transcription_type = "VOSK"
        mock_settings.model_compile_dir = "/tmp/compile"
        mock_settings.transcription_model_param = {}
        mock_webvtt.read.side_effect = Exception("Parse error")

        process_enrich_model_queue()

        self.queue_item.refresh_from_db()
        self.assertEqual(self.queue_item.status, "error")
