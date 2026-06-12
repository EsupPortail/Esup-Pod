"""
Esup-Pod - Completion admin tests.
"""

from unittest.mock import patch
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite

from src.apps.video.models import Video, Subtitle
from src.apps.completion.models import EnrichModelQueue
from src.apps.video.admin import SubtitleAdmin
from src.apps.completion.admin import EnrichModelQueueAdmin

User = get_user_model()


class MockRequest:
    """A mock request for testing."""

    def __init__(self, user=None):
        self.user = user


class AdminActionTests(TestCase):
    """Tests for custom admin actions."""

    def setUp(self):
        """Set up the test environment."""
        self.user = User.objects.create_superuser(username="admin", password="password")
        self.video = Video.objects.create(
            title="Test Video",
            owner=self.user,
        )
        self.subtitle = Subtitle.objects.create(
            video=self.video, language="en", file="test.vtt"
        )
        self.factory = RequestFactory()

    @patch("src.apps.completion.tasks.process_enrich_model_queue.delay")
    def test_enrich_model_action(self, mock_task_delay):
        """Test that enrich_model_action queues subtitles and triggers task."""
        request = self.factory.get("/")
        request.user = self.user

        site = AdminSite()
        subtitle_admin = SubtitleAdmin(Subtitle, site)

        from src.apps.completion.admin import enrich_model_action

        queryset = Subtitle.objects.all()
        with patch.object(subtitle_admin, "message_user"):
            enrich_model_action(subtitle_admin, request, queryset)

        self.assertTrue(
            EnrichModelQueue.objects.filter(
                track=self.subtitle, status="pending"
            ).exists()
        )

        mock_task_delay.assert_called_once()

    @patch("src.apps.completion.tasks.process_enrich_model_queue.delay")
    def test_trigger_processing_action(self, mock_task_delay):
        """Test trigger_processing action on EnrichModelQueueAdmin."""
        queue_item = EnrichModelQueue.objects.create(
            video=self.video, track=self.subtitle, status="error"
        )

        request = self.factory.get("/")
        request.user = self.user

        site = AdminSite()
        queue_admin = EnrichModelQueueAdmin(EnrichModelQueue, site)

        queryset = EnrichModelQueue.objects.all()
        with patch.object(queue_admin, "message_user"):
            queue_admin.trigger_processing(request, queryset)

        queue_item.refresh_from_db()
        self.assertEqual(queue_item.status, "pending")
        mock_task_delay.assert_called_once()
