"""
Esup-Pod - Video models tests.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from src.apps.video.models import Video, ViewCount, Comment
import datetime

from src.apps.video.apps import sync_metadata

User = get_user_model()


class VideoModelTests(TestCase):
    """
    Esup-Pod - Tests for the Video application models.
    """

    def setUp(self):
        """Sets up a video and an owner for model testing."""
        sync_metadata(sender=None)
        self.user = User.objects.create_user(username="owner", password="password")
        self.video = Video.objects.create(
            title="Model Test Video",
            owner=self.user,
            description="A description",
            status=Video.Status.PUBLISHED,
            license_id="CC-BY",
        )

    def test_get_dublin_core(self):
        """Verifies the Dublin Core metadata generation."""
        dc = self.video.get_dublin_core()
        self.assertEqual(dc["title"], "Model Test Video")
        self.assertEqual(dc["description"], "A description")
        self.assertEqual(dc["creator"], "owner")
        self.assertEqual(dc["format"], "video/mp4")
        self.assertEqual(dc["rights"], "CC-BY")

    def test_view_count_creation(self):
        """Verifies daily view count records and their string representation."""
        view_count = ViewCount.objects.create(
            video=self.video, date=datetime.date(2026, 1, 1), count=5
        )
        self.assertEqual(view_count.video, self.video)
        self.assertEqual(view_count.count, 5)
        self.assertEqual(str(view_count), "Model Test Video - 2026-01-01: 5")

    def test_video_str(self):
        """Verifies the video's string representation."""
        self.assertEqual(str(self.video), "Model Test Video (Published (Public))")


class CommentBasicTests(TestCase):
    """Esup-Pod - Tests for the Comment model."""

    def setUp(self):
        """Sets up a video and a user for comment testing."""
        sync_metadata(sender=None)
        self.user = User.objects.create_user(username="commenter2", password="password")
        self.video = Video.objects.create(
            title="A Video", owner=self.user, status=Video.Status.PUBLISHED
        )

    def test_create_comment(self):
        """Verifies the creation of a comment."""
        comment = Comment.objects.create(
            author=self.user, video=self.video, content="Small test comment"
        )
        self.assertEqual(str(comment), "Small test comment")
        self.assertEqual(comment.number_vote, 0)
