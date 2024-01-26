"""Unit tests for Esup-Pod dressing views."""

from django.contrib.auth.models import User
from django.test import TestCase

from pod.dressing.models import Dressing

from pod.video.models import Type, Video


class VideoDressingViewTest(TestCase):
    """Dressing page test case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='user', password='password', is_staff=1)
        self.first_video = Video.objects.create(
            title="First video",
            slug="first-video",
            owner=self.user,
            video="first_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.dressing = Dressing.objects.create(title='Test Dressing')
        self.dressing.owners.set([self.user])
        self.dressing.users.set([self.user])

    def test_video_dressing_view(self):
        """Test for video_dressing view."""

        print(" ---> test_video_dressing_view: OK! --- VideoDressingViewTest")
