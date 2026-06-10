"""
Esup-Pod - Dressing signals tests.
"""

import pytest
from unittest.mock import patch
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from src.apps.dressing.models import Dressing
from src.apps.video.models import Video

User = get_user_model()


@pytest.fixture
def user():
    """Fixture to create a standard User."""
    return User.objects.create_user(username="testuser", password="testpassword")


@pytest.fixture
def video(user):
    """Fixture to create a Video with a video_file."""
    return Video.objects.create(
        title="Test Video",
        video_file=ContentFile(b"fake video content", name="test_video.mp4"),
        owner=user,
    )


@pytest.fixture
def dressing():
    """Fixture to create a Dressing instance."""
    return Dressing.objects.create(title="Signal Dressing")


@pytest.mark.django_db
class TestDressingSignals:
    """Tests for the Dressing signals."""

    @patch("src.apps.encoding.tasks.trigger_runner_encoding_task.delay")
    def test_m2m_changed_add_and_remove(self, mock_delay, dressing, video):
        """Test that adding and removing a video to/from a dressing triggers encoding."""
        # 1. Add video
        dressing.videos.add(video)

        # Verify task is triggered
        mock_delay.assert_called_once()
        args, kwargs = mock_delay.call_args
        assert args[0] == video.pk
        assert video.video_file.url in args[1]

        # Reset mock
        mock_delay.reset_mock()

        # 2. Remove video
        dressing.videos.remove(video)

        # Verify task is triggered on remove
        mock_delay.assert_called_once()
        args, kwargs = mock_delay.call_args
        assert args[0] == video.pk

    @patch("src.apps.encoding.tasks.trigger_runner_encoding_task.delay")
    def test_m2m_changed_clear(self, mock_delay, dressing, video):
        """Test that clearing the dressing videos triggers encoding for cleared videos."""
        dressing.videos.add(video)
        mock_delay.reset_mock()

        dressing.videos.clear()

        # Verify task is triggered on clear
        mock_delay.assert_called_once()
        args, kwargs = mock_delay.call_args
        assert args[0] == video.pk

    @patch("src.apps.encoding.tasks.trigger_runner_encoding_task.delay")
    def test_post_save_updates_associated_videos(self, mock_delay, dressing, video):
        """Test that updating a dressing triggers encoding for all associated videos."""
        dressing.videos.add(video)
        mock_delay.reset_mock()

        # Update dressing title or field
        dressing.opacity = 50
        dressing.save()

        # Verify task is triggered for the associated video
        mock_delay.assert_called_once()
        args, kwargs = mock_delay.call_args
        assert args[0] == video.pk

    @patch("src.apps.encoding.tasks.trigger_runner_encoding_task.delay")
    def test_post_save_does_not_trigger_on_create(self, mock_delay):
        """Test that creating a new dressing does not trigger encoding since there are no videos yet."""
        Dressing.objects.create(title="Brand New Dressing")
        mock_delay.assert_not_called()
