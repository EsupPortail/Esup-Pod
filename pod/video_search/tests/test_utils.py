"""Unit tests for Esup-Pod video search utilities."""

from django.test import TestCase
from django.contrib.auth.models import User

from pod.video.models import Video, Type
from ..utils import index_es


class VideoSearchTestUtils(TestCase):
    """TestCase for Esup-Pod video utilities."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Set up required objects for next tests."""
        self.user = User.objects.create(username="pod", password="pod1234pod")
        self.v = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

    def test_index_es(self):
        """Test if index video working well."""
        res = index_es(self.v)
        print("\n - RES : %s" % res)
        print("--> test_index_es ok ! ")
