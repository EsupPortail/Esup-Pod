import os

from django.test import TestCase
from django.test import override_settings
from django.conf import settings
from django.contrib.auth.models import User

from ..models import Recording  # , RecordingFile


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
class RecordingTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        user = User.objects.create(username="pod")
        source_file = "/home/pod/files/video.mp4"
        type = "video"
        recording = Recording.objects.create(user=user, title="media1")
        recording.type = type
        recording.source_file = source_file
        recording.save()
        print(" --->  SetUp of MediaCoursesTestCase : OK !")

    """
        test attributs
    """

    def test_attributs(self):
        recording = Recording.objects.get(id=1)
        self.assertEqual(recording.title, "media1")
        self.assertEqual(recording.type, "video")
        self.assertEqual(recording.source_file, "/home/pod/files/video.mp4")
        print(
            "   --->  test_attributs of RecordingTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Recording.objects.filter(title="media1").delete()
        self.assertEquals(Recording.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of RecordingTestCase : OK !")
