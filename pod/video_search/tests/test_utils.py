"""Unit tests for Esup-Pod video search utilities.

*  run with 'python manage.py test pod.video_search.tests.test_utils'
"""

from django.test import TestCase
from django.contrib.auth.models import User

from pod.video.models import Video, Type
from ..utils import index_es, delete_es


class VideoSearchTestUtils(TestCase):
    """TestCase for Esup-Pod video utilities."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        self.user = User.objects.create(username="pod", password="pod1234pod")
        self.v = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

    def test_index_and_delete_es(self) -> None:
        res = index_es(self.v)
        self.assertTrue(res["result"] in ["created", "updated"])
        self.assertEqual(res["_id"], str(self.v.id))
        delete = delete_es(self.v.id)
        self.assertEqual(delete["result"], "deleted")
        self.assertEqual(delete["_id"], str(self.v.id))
        print("--> test_index_and_delete_es ok! ")
