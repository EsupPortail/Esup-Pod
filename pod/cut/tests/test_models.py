"""Unit tests for cut models."""

import unittest

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.models import User
from pod.video.models import Video
from pod.video.models import Type
from ..models import CutVideo

USE_CUT = getattr(settings, "USE_CUT", False)


@unittest.skipUnless(USE_CUT, "Set USE_CUT to True before testing video cut stuffs.")
class CutVideoModelTestCase(TestCase):
    """Test case for the CutVideo model."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up the test with a video and a cut."""
        owner = User.objects.create(username="test")
        video_type = Type.objects.create(title="others")
        video = Video.objects.create(
            title="video",
            type=video_type,
            owner=owner,
            video="test.mp4",
            duration=20,
        )
        CutVideo.objects.create(video=video, start="00:00:00", end="00:00:20")

    def test_bad_time(self) -> None:
        """Test the creation with bad time values."""
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
        print(" ---> test_bad_time: OK! --- CutVideoModel")

    def test_verify_time__value_error(self) -> None:
        """Test verify_time method with bad values."""
        video = Video.objects.get(id=1)
        cut = CutVideo()
        cut.duration = video.duration_in_time
        cut.video = video
        cut.start = "bad_value"
        cut.end = "bad_value"
        self.assertFalse(cut.verify_time())
        print(" ---> test_verify_time_value_error: OK! --- CutVideoModel")

    def test_verify_time__good_values(self) -> None:
        """Test verify_time method with good values."""
        video = Video.objects.get(id=1)
        cut = CutVideo()
        cut.duration = video.duration_in_time
        cut.video = video
        cut.start = "00:00:00"
        cut.end = "00:00:15"
        self.assertTrue(cut.verify_time())
        print(" ---> test_verify_time_good_values: OK! --- CutVideoModel")

    def test_start_in_int(self) -> None:
        """Test the start_in_int property."""
        cut = CutVideo.objects.get(id=1)
        self.assertEqual(cut.start_in_int, 0)
        print(" ---> test_start_in_int: OK! --- CutVideoModel")

    def test_end_in_int(self) -> None:
        """Test the end_in_int property."""
        cut = CutVideo.objects.get(id=1)
        self.assertEqual(cut.end_in_int, 20)
        print(" ---> test_end_in_int: OK! --- CutVideoModel")
