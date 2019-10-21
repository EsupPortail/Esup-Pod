import os

from django.test import TestCase
from django.test import override_settings
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from pod.video.models import Type
from ..models import Recorder, Recording, Job
from datetime import date


# Create your tests here.
@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    },
    LANGUAGE_CODE='en'
)
class MediacourseRecorderTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        user1 = User.objects.create_user("lb1")
        user2 = User.objects.create_user("lb2")
        videotype = Type.objects.create(title='others')
        Recorder.objects.create(user=user1, name="recorder1", address_ip="16.3.10.37", type=videotype, directory="dir1")
        Recorder.objects.create(user=user2, name="recorder2", address_ip="16.3.10.38", type=videotype, directory="dir2")
        print(" --->  SetUp of MediacourseRecorderTestCase : OK !")

    """
		test attributs
	"""

    def test_attributs(self):
        recorder1 = Recorder.objects.get(id=1)
        recorder2 = Recorder.objects.get(id=2)
        self.assertEqual(recorder1.user.username, "lb1")
        self.assertEqual(recorder1.name, "recorder1")
        self.assertEqual(recorder1.address_ip, "16.3.10.37")
        self.assertEqual(recorder2.name, "recorder2")
        self.assertEqual(recorder2.address_ip, "16.3.10.38")
        print(
            "   --->  test_attributs of MediacourseRecorderTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Recorder.objects.filter(name="recorder1").delete()
        self.assertEquals(Recorder.objects.all().count(), 1)

        print(
            "   --->  test_delete_object of MediacourseRecorderTestCase : OK !")

class MediacourseRecordingTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        user1 = User.objects.create(username="pod")
        videotype = Type.objects.create(title='others')
        recorder1 = Recorder.objects.create(id=1,user=user1, name="recorder1", address_ip="16.3.10.37", type=videotype, directory="dir1")
        recording = Recording.objects.create(title="file1", recorder=recorder1, mediapath="/data/ftp-pod/ftp/video.mp4")
        recording.type = "video"
        recording.date_added = timezone.now()
        print(" --->  SetUp of MediacourseRecordingTestCase : OK !")

    """
        test attributs
    """

    def test_attributs(self):
        recorder = Recorder.objects.get(id=1)
        recording = Recording.objects.get(id=1)
        self.assertEqual(recording.title, "file1")
        self.assertEqual(recording.type, "video")
        self.assertEqual(recording.mediapath, "/data/ftp-pod/ftp/video.mp4")
        self.assertEqual(recording.recorder, recorder)
        date = timezone.now()
        self.assertEqual(recording.date_added.year, date.year)
        self.assertEqual(recording.date_added.month, date.month)
        self.assertEqual(recording.date_added.day, date.day)
        print(
            "   --->  test_attributs of MediacourseRecordingTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Recording.objects.filter(title="file1").delete()
        self.assertEquals(Recording.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of MediacourseRecordingTestCase : OK !")

class MediacourseJobTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        job = Job.objects.create(id=1, mediapath="/data/ftp-pod/ftp/video.mp4", email_sent=False)
        print(" --->  SetUp of MediacourseJobTestCase : OK !")

    """
        test attributs
    """

    def test_attributs(self):
        job = Job.objects.get(id=1)
        self.assertEqual(job.mediapath, "/data/ftp-pod/ftp/video.mp4")
        self.assertEqual(job.email_sent, False)
        date = timezone.now()
        self.assertEqual(job.date_email_sent.year, date.year)
        self.assertEqual(job.date_email_sent.month, date.month)
        self.assertEqual(job.date_email_sent.day, date.day)
        print(
            "   --->  test_attributs of MediacourseJobTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Job.objects.filter(mediapath="/data/ftp-pod/ftp/video.mp4").delete()
        self.assertEquals(Job.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of MediacourseJobTestCase : OK !")