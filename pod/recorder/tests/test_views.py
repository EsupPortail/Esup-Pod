"""
Unit tests for recorder views
"""
import hashlib
import os

from django.conf import settings
from django.test import override_settings
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from pod.recorder.models import Recorder
from pod.video.models import Type


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
class recorderViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        videotype = Type.objects.create(title='others')
        user = User.objects.create(username='pod', password='podv2')
        Recorder.objects.create(id=1, user=user, name="recorder1",
                                address_ip="16.3.10.37", type=videotype,
                                directory="dir1", recording_type="video")
        print(" --->  SetUp of recorderViewsTestCase : OK !")

    def test_add_recording(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/add_recording/")
        self.assertRaises(PermissionDenied)  # No mediapath and user is not SU

        self.user.is_superuser = True
        self.user.save()
        response = self.client.get("/add_recording/",
                                   {'mediapath': 'video.mp4',
                                    'recorder': 1})
        self.assertEqual(response.status_code, 302)  # User is not staff

        self.user.is_staff = True
        self.user.save()

        # recorder not exist
        response = self.client.get("/add_recording/",
                                   {'mediapath': 'video.mp4',
                                    'recorder': 100})
        self.assertEqual(response.status_code, 403)

        response = self.client.get("/add_recording/",
                                   {'mediapath': 'video.mp4',
                                    'recorder': 1})
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'recorder/add_recording.html')

        print(
            "   --->  test_add_recording of recorderViewsTestCase : OK !")

    def test_claim_recording(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/claim_record/")
        self.assertRaises(PermissionDenied)  # No mediapath and user is not SU

        self.user.is_superuser = True
        self.user.save()
        response = self.client.get("/claim_record/")
        self.assertEqual(response.status_code, 302)  # User is not staff

        self.user.is_staff = True
        self.user.save()
        response = self.client.get("/claim_record/")
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'recorder/claim_record.html')

        print(
            "   --->  test_claim_record of recorderViewsTestCase : OK !")

    def test_recorder_notify(self):
        self.client = Client()

        record = Recorder.objects.get(id=1)
        response = self.client.get("/recorder_notify/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'nok : recordingPlace or '
                                           b'mediapath or key are missing')

        response = self.client.get("/recorder_notify/?key=abc&mediapath"
                                   "=/some/path&recordingPlace=16_3_10_37"
                                   "&course_title=title")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'nok : key is not valid')

        m = hashlib.md5()
        m.update(record.ipunder().encode('utf-8') + record.salt.encode('utf-8')
                 )
        response = self.client.get("/recorder_notify/?key=" + m.hexdigest() +
                                   "&mediapath=/some/path&recordingPlace"
                                   "=16_3_10_37&course_title=title")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')

        print(
            "   --->  test_record_notify of recorderViewsTestCase : OK !")
