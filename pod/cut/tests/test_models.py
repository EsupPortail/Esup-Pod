"""
Unit tests for cut models
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from pod.video.models import Video
from pod.video.models import Type
from ..models import CutVideo


class CutVideoModelTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        owner = User.objects.create(username="test")
        videotype = Type.objects.create(title="others")
        video = Video.objects.create(
            title="video",
            type=videotype,
            owner=owner,
            video="test.mp4",
            duration=20,
        )
        CutVideo.objects.create(video=video, start="00:00:00", end="00:00:20")

    def test_bad_time(self):
        video = Video.objects.get(id=1)
        cut = CutVideo()
        cut.duration = video.duration_in_time
        cut.video = video
        cut.start = "00:00:21"
        cut.end = "00:00:25"
        self.assertRaises(ValidationError, cut.clean)
        cut.start = "00:00:12"
        cut.end = "00:00:08"
        self.assertRaises(ValidationError, cut.clean)

        print(" ---> test_bad_time: OK ! --- CutVideoModel")
