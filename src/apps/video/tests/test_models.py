"""
Esup-Pod - Video models tests.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from src.apps.video.models import Video, ViewCount
import datetime

User = get_user_model()


class VideoModelTests(TestCase):
    """
    Esup-Pod - Tests for the Video application models.
    """
    def setUp(self):
        self.user = User.objects.create_user(username="owner", password="password")
        self.video = Video.objects.create(
            title="Model Test Video",
            owner=self.user,
            description="A description",
            status=Video.Status.PUBLISHED,
            license=Video.License.CC_BY,
        )

    def test_get_dublin_core(self):
        dc = self.video.get_dublin_core()
        self.assertEqual(dc["title"], "Model Test Video")
        self.assertEqual(dc["description"], "A description")
        self.assertEqual(dc["creator"], "owner")
        self.assertEqual(dc["format"], "video/mp4")
        self.assertEqual(dc["rights"], Video.License.CC_BY)

    def test_view_count_creation(self):
        view_count = ViewCount.objects.create(
            video=self.video, date=datetime.date(2026, 1, 1), count=5
        )
        self.assertEqual(view_count.video, self.video)
        self.assertEqual(view_count.count, 5)
        self.assertEqual(str(view_count), "Model Test Video - 2026-01-01: 5")

    def test_video_str(self):
        self.assertEqual(str(self.video), "Model Test Video (Published (Public))")
