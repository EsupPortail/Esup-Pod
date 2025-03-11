"""Unit tests for speaker models."""

from django.test import TestCase
from django.contrib.auth.models import User
from pod.video.models import Type, Video
from pod.speaker.models import Speaker, Job, JobVideo


class SpeakerModelTest(TestCase):
    """Test case for Pod speaker models."""

    def setUp(self):
        """Set up SpeakerModel Tests."""
        owner = User.objects.create(username="pod")
        videotype = Type.objects.create(title="others")
        video = Video.objects.create(
            title="video1",
            type=videotype,
            owner=owner,
            video="test.mp4",
            duration=20,
        )
        video2 = Video.objects.create(
            title="video2",
            type=videotype,
            owner=owner,
            video="test2.mp4",
            duration=20,
        )
        speaker1 = Speaker.objects.create(firstname="Dupont", lastname="Pierre")
        speaker2 = Speaker.objects.create(firstname="Martin", lastname="Michel")
        job1 = Job.objects.create(speaker=speaker1, title="Directeur")
        job2 = Job.objects.create(speaker=speaker1, title="President")
        job3 = Job.objects.create(speaker=speaker2, title="Responsable")
        JobVideo.objects.create(video=video, job=job1)
        JobVideo.objects.create(video=video, job=job2)
        JobVideo.objects.create(video=video2, job=job3)

    def test_attributs_full(self):
        """Test all attributs."""
        speaker1 = Speaker.objects.get(id=1)
        speaker2 = Speaker.objects.get(id=2)
        job1 = Job.objects.get(id=1)
        self.assertEqual(speaker1.firstname, "Dupont")
        self.assertEqual(speaker1.lastname, "Pierre")
        self.assertEqual(speaker2.firstname, "Martin")
        self.assertEqual(speaker2.lastname, "Michel")
        self.assertEqual(job1.title, "Directeur")
        print(" ---> test_attributs_full: OK! --- SpeakerModelTest")
