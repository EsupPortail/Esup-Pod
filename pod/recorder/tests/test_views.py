"""
Unit tests for recorder views
"""
import hashlib

from django.conf import settings
from django.test import TestCase
from django.test import Client, override_settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from ..models import Recorder, RecordingFileTreatment
from pod.video.models import Type
from django.contrib.sites.models import Site

from .. import views
from importlib import reload
from http import HTTPStatus
import os


class recorderViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        videotype = Type.objects.create(title="others")
        user = User.objects.create(username="pod", password="podv2")
        recorder = Recorder.objects.create(
            id=1,
            user=user,
            name="recorder1",
            address_ip="16.3.10.37",
            type=videotype,
            directory="dir1",
            recording_type="video",
        )
        recording_file = RecordingFileTreatment.objects.create(
            type="video", file="/home/pod/files/somefile.mp4", recorder=recorder
        )
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
        response = self.client.get(
            "/add_recording/", {"mediapath": "video.mp4", "recorder": 1}
        )
        self.assertEqual(response.status_code, 302)  # User is not staff

        self.user.is_staff = True
        self.user.save()

        # recorder not exist
        response = self.client.get(
            "/add_recording/", {"mediapath": "video.mp4", "recorder": 100}
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.get(
            "/add_recording/", {"mediapath": "video.mp4", "recorder": 1}
        )
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "recorder/add_recording.html")

        print("   --->  test_add_recording of recorderViewsTestCase : OK !")

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

        self.assertTemplateUsed(response, "recorder/claim_record.html")

        print("   --->  test_claim_record of recorderViewsTestCase : OK !")

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

        self.assertTemplateUsed(response, "recorder/record_delete.html")

        print("   --->  test_delete_record recorderViewsTestCase : OK !")

    def test_recorder_notify(self):
        self.client = Client()

        record = Recorder.objects.get(id=1)
        response = self.client.get("/recorder_notify/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content,
            b"nok : recordingPlace or " b"mediapath or key are missing",
        )

        response = self.client.get(
            "/recorder_notify/?key=abc&mediapath"
            "=/some/path&recordingPlace=16_3_10_37"
            "&course_title=title"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"nok : key is not valid")

        m = hashlib.md5()
        m.update(record.ipunder().encode("utf-8") + record.salt.encode("utf-8"))
        response = self.client.get(
            "/recorder_notify/?key="
            + m.hexdigest()
            + "&mediapath=/some/path&recordingPlace"
            "=16_3_10_37&course_title=title"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

        print("   --->  test_record_notify of recorderViewsTestCase : OK !")


class studio_podTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def create_index_file(self):
        text = """
        <html>
            <body>
                <h1>Heading</h1>
            </body>
        </html>
        """
        template_file = os.path.join(
            settings.BASE_DIR, "custom/static/opencast/studio/index.html"
        )
        template_dir = os.path.dirname(template_file)
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
        file = open(template_file, "w+")
        file.write(text)
        file.close()

    def setUp(self):
        User.objects.create(username="pod", password="pod1234pod")
        print(" --->  SetUp of studio_podTestView: OK!")

    def test_studio_podTestView_get_request(self):
        self.create_index_file()
        self.client = Client()
        response = self.client.get("/studio/")
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/studio/")
        self.assertEqual(response.status_code, HTTPStatus.OK)

        print(" --->  test_studio_podTestView_get_request of video_recordTestView: OK!")

    @override_settings(DEBUG=True, RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=True)
    def test_studio_podTestView_get_request_restrict(self):
        reload(views)
        self.create_index_file()
        self.client = Client()
        response = self.client.get("/studio/")
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/studio/")
        self.assertEquals(response.context["access_not_allowed"], True)
        self.user.is_staff = True
        self.user.save()
        response = self.client.get("/studio/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        print(
            " --->  test_studio_podTestView_get_request_restrict ",
            "of studio_podTestView: OK!",
        )

    """
    def test_video_recordTestView_upload_recordvideo(self):
        reload(views)
        video = SimpleUploadedFile("file.mp4", b"file_content", content_type="video/mp4")
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("video_record"),
            {"video": video, "title": "test upload"},
            **{"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context, None)
        try:
            data = json.loads(response.content)
        except (RuntimeError, TypeError, NameError, AttributeError) as err:
            print("Unexpected error: {0}".format(err))
            data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["url_edit"], "/video_edit/0001-test-upload/")
        self.assertEqual(Video.objects.all().count(), 1)
        vid = Video.objects.get(id=1)
        self.assertEqual(vid.title, "test upload")
        print(
            " --->  test_video_recordTestView_upload_recordvideo ",
            "of video_recordTestView: OK!",
        )
    """
