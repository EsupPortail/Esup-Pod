"""
Unit tests for recorder views
"""
import hashlib

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from ..models import Recorder, RecordingFileTreatment
from pod.video.models import Type
from django.contrib.sites.models import Site


class recorderViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        site = Site.objects.get(id=1)
        videotype = Type.objects.create(title='others')
        user = User.objects.create(username='pod', password='podv2')
        recorder = Recorder.objects.create(id=1, user=user, name="recorder1",
                                           address_ip="16.3.10.37",
                                           type=videotype,
                                           directory="dir1",
                                           recording_type="video")
        recording_file = RecordingFileTreatment.objects.create(
            type='video',
            file="/home/pod/files/somefile.mp4",
            recorder=recorder)
        recording_file.save()
        recorder.sites.add(site)

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
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

    def test_delete_record(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/delete_record/1/")
        self.assertRaises(PermissionDenied)

        self.user.is_staff = True
        self.user.save()
        response = self.client.get("/delete_record/1/")
        self.assertRaises(PermissionDenied)

        self.user.is_superuser = True
        self.user.save()

        response = self.client.get("/delete_record/2/")
        self.assertEqual(response.status_code, 404)

        response = self.client.get("/delete_record/1/")
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'recorder/record_delete.html')

        print(
            "   --->  test_delete_record recorderViewsTestCase : OK !")

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
