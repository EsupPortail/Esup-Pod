"""
Unit tests for recorder views
"""
import hashlib

from django.conf import settings
from django.test import TestCase
from django.test import Client, override_settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Recorder, RecordingFileTreatment
from pod.video.models import Type
from django.contrib.sites.models import Site

from xml.dom import minidom

from .. import views
from importlib import reload
from http import HTTPStatus
import os

OPENCAST_FILES_DIR = getattr(settings, "OPENCAST_FILES_DIR", "opencast-files")


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

    def test_studio_presenter_post(self):
        self.client = Client()
        response = self.client.get("/studio/presenter_post")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        # test get method
        response = self.client.get("/studio/presenter_post")
        self.assertEqual(response.status_code, 400)

        response = self.client.post("/studio/presenter_post", {"presenter": "test"})
        self.assertEqual(response.status_code, 400)

        response = self.client.post("/studio/presenter_post", {"presenter": "mid"})
        self.assertEqual(response.status_code, 200)

        print(" -->  test_studio_presenter_post of studio_podTestView", " : OK !")

    def test_studio_info_me_json(self):
        self.client = Client()
        response = self.client.get("/studio/info/me.json")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get("/studio/info/me.json")
        self.assertTrue(b"ROLE_ADMIN" in response.content)
        self.assertEqual(response.status_code, 200)

        print(" -->  test_studio_info_me_json of studio_podTestView", " : OK !")

    def test_studio_ingest_createMediaPackage(self):
        self.client = Client()
        response = self.client.get("/studio/ingest/createMediaPackage")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get("/studio/ingest/createMediaPackage")
        self.assertEqual(response.status_code, 200)

        # check if response is xml
        mediaPackage_content = minidom.parseString(response.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia = mediapackage.getAttribute("id")

        mediaPackage_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
        )
        mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
        self.assertTrue(os.path.exists(mediaPackage_file))

        mediaPackage_content = minidom.parse(mediaPackage_file)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        self.assertEqual(mediapackage.getAttribute("id"), idMedia)

        print(
            " -->  test_studio_ingest_createMediaPackage of studio_podTestView", " : OK !"
        )

    def test_studio_ingest_addDCCatalog(self):
        self.client = Client()
        response = self.client.get("/studio/ingest/addDCCatalog")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get("/studio/ingest/addDCCatalog")
        self.assertEqual(response.status_code, 400)

        # check if response is xml
        response_media_package = self.client.get("/studio/ingest/createMediaPackage")
        mediaPackage_content = minidom.parseString(response_media_package.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia_sent = mediapackage.getAttribute("id")

        dublinCoreContent = """
            <?xml version="1.0" encoding="UTF-8"?>
            <dublincore xmlns="http://www.opencastproject.org/xsd/1.0/dublincore/"
                        xmlns:dcterms="http://purl.org/dc/terms/"
                        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <dcterms:created xsi:type="dcterms:W3CDTF">
                    2022-02-10T09:41:15.762Z
                </dcterms:created>
                <dcterms:title>test dublin core</dcterms:title>
                <dcterms:creator>mid</dcterms:creator>
                <dcterms:extent xsi:type="dcterms:ISO8601">PT5.568S</dcterms:extent>
                <dcterms:spatial>Pod Studio</dcterms:spatial>
            </dublincore>
        """

        response = self.client.post(
            "/studio/ingest/addDCCatalog",
            {
                "mediaPackage": mediaPackage_content.toxml(),
                "dublinCore": dublinCoreContent,
                "flavor": "dublincore/episode",
            },
        )
        # check response code 200
        self.assertEqual(response.status_code, 200)
        # get media package return by request
        mediaPackage_content = minidom.parseString(response.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia = mediapackage.getAttribute("id")
        self.assertEqual(idMedia, idMedia_sent)

        mediaPackage_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
        )
        mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
        # chek if mediapackage file exist
        self.assertTrue(os.path.exists(mediaPackage_file))
        # check if dublin core file exist
        dublinCore_file = os.path.join(mediaPackage_dir, "dublincore.xml")
        self.assertTrue(os.path.exists(dublinCore_file))
        # check if media package content is good content with id media
        mediaPackage_content = minidom.parse(mediaPackage_file)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        self.assertEqual(mediapackage.getAttribute("id"), idMedia)

        # check if mediaPackage_content has catalog with good type
        catalog = mediaPackage_content.getElementsByTagName("catalog")[0]
        self.assertTrue(catalog)
        self.assertEqual(catalog.getAttribute("type"), "dublincore/episode")

        print(" -->  test_studio_ingest_addDCCatalog of studio_podTestView", " : OK !")

    def test_studio_ingest_addAttachment(self):
        self.client = Client()
        response = self.client.get("/studio/ingest/addAttachment")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get("/studio/ingest/addAttachment")
        self.assertEqual(response.status_code, 400)

        response_media_package = self.client.get("/studio/ingest/createMediaPackage")
        mediaPackage_content = minidom.parseString(response_media_package.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia_sent = mediapackage.getAttribute("id")

        acl = SimpleUploadedFile(
            name="acl.xml",
            content="",  # not use in Pod
            content_type="application/xml",
        )

        response = self.client.post(
            "/studio/ingest/addAttachment",
            {
                "mediaPackage": mediaPackage_content.toxml(),
                "BODY": acl,
                "flavor": "security/xacml+episode",
            },
        )
        # check response code 200
        self.assertEqual(response.status_code, 200)
        # get media package return by request
        mediaPackage_content = minidom.parseString(response.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia = mediapackage.getAttribute("id")
        self.assertEqual(idMedia, idMedia_sent)

        mediaPackage_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
        )
        mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
        # chek if mediapackage file exist
        self.assertTrue(os.path.exists(mediaPackage_file))

        # check if media package content is good content with id media
        mediaPackage_content = minidom.parse(mediaPackage_file)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        self.assertEqual(mediapackage.getAttribute("id"), idMedia)

        # check if mediaPackage_content has attachment with good type
        attachment = mediaPackage_content.getElementsByTagName("attachment")[0]
        self.assertTrue(attachment)
        self.assertEqual(attachment.getAttribute("type"), "security/xacml+episode")

        print(" -->  test_studio_ingest_addAttachment of studio_podTestView", " : OK !")

    def test_studio_ingest_addTrack(self):
        self.client = Client()
        response = self.client.get("/studio/ingest/addTrack")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get("/studio/ingest/addTrack")
        self.assertEqual(response.status_code, 400)

        response_media_package = self.client.get("/studio/ingest/createMediaPackage")
        mediaPackage_content = minidom.parseString(response_media_package.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia_sent = mediapackage.getAttribute("id")

        video = SimpleUploadedFile(
            name="file.webm",
            content=b'empty file',
            content_type="video/webm",
        )

        response = self.client.post(
            "/studio/ingest/addTrack",
            {
                "mediaPackage": mediaPackage_content.toxml(),
                "BODY": video,
                "flavor": "presenter/source",
                "tags": None,
            },
        )

        # check response code 200
        self.assertEqual(response.status_code, 200)
        # get media package return by request
        mediaPackage_content = minidom.parseString(response.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia = mediapackage.getAttribute("id")
        self.assertEqual(idMedia, idMedia_sent)

        mediaPackage_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
        )
        mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
        # chek if mediapackage file exist
        self.assertTrue(os.path.exists(mediaPackage_file))

        # check if media package content is good content with id media
        mediaPackage_content = minidom.parse(mediaPackage_file)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        self.assertEqual(mediapackage.getAttribute("id"), idMedia)

        track = mediaPackage_content.getElementsByTagName("track")[0]
        self.assertTrue(track)
        self.assertEqual(track.getAttribute("type"), "presenter/source")

        opencast_filename, ext = os.path.splitext(video.name)
        self.assertEqual(track.getAttribute("filename"), opencast_filename)
        dest_filename = "%s%s" % (
            str("presenter/source").replace("/", "_").replace(" ", ""),
            ext,
        )
        video_file = os.path.join(mediaPackage_dir, dest_filename)
        # chek if mediapackage file exist
        self.assertTrue(os.path.exists(video_file))

        print(" -->  test_studio_ingest_addTrack of studio_podTestView", " : OK !")


    def  test_studio_ingest_addCatalog(self):
        self.client = Client()
        response = self.client.get("/studio/ingest/addCatalog")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get("/studio/ingest/addCatalog")
        self.assertEqual(response.status_code, 400)

        print(" -->  test_studio_ingest_addCatalog of studio_podTestView", " : OK !")

