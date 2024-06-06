"""Unit tests for recorder views."""

import hashlib
import os
from http import HTTPStatus
from defusedxml import minidom

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from pod.video.models import Type
from .. import views
from ..models import Recorder, Recording, RecordingFileTreatment

OPENCAST_FILES_DIR = getattr(settings, "OPENCAST_FILES_DIR", "opencast-files")
OPENCAST_DEFAULT_PRESENTER = getattr(settings, "OPENCAST_DEFAULT_PRESENTER", "mid")


class RecorderViewsTestCase(TestCase):
    """Test case for Pod recorder views."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create models to be tested."""
        site = Site.objects.get(id=1)
        videotype = Type.objects.create(title="others")
        user = User.objects.create(username="pod", password="podv3")
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
        print(" --->  SetUp of RecorderViewsTestCase: OK!")

    def test_add_recording(self):
        """Test method add_recording()."""

        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        url = reverse("record:add_recording")
        self.client.get(url)
        self.assertRaises(PermissionDenied)  # No mediapath and user is not SU

        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(url, {"mediapath": "video.mp4", "recorder": 1})
        self.assertEqual(response.status_code, 302)  # User is not staff

        self.user.is_staff = True
        self.user.save()

        # recorder not exist
        response = self.client.get(url, {"mediapath": "video.mp4", "recorder": 100})
        self.assertEqual(response.status_code, 403)

        response = self.client.get(url, {"mediapath": "video.mp4", "recorder": 1})
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "recorder/add_recording.html")

        print("   --->  test_add_recording of RecorderViewsTestCase: OK!")

    def test_claim_recording(self):
        """Test method claim_recording()."""

        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        url = reverse("record:claim_record")
        self.client.get(url)
        self.assertRaises(PermissionDenied)  # No mediapath and user is not SU

        self.user.is_superuser = True
        self.user.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # User is not staff

        self.user.is_staff = True
        self.user.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "recorder/claim_record.html")

        print("   --->  test_claim_record of RecorderViewsTestCase: OK!")

    def test_delete_record(self):
        """Test method delete_recording()."""

        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        url = reverse("record:delete_record", kwargs={"id": 1})
        self.client.get(url)
        self.assertRaises(PermissionDenied)

        self.user.is_staff = True
        self.user.save()
        self.client.get(url)
        self.assertRaises(PermissionDenied)

        self.user.is_superuser = True
        self.user.save()
        url = reverse("record:delete_record", kwargs={"id": 2})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        url = reverse("record:delete_record", kwargs={"id": 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, "recorder/record_delete.html")

        print("   --->  test_delete_record RecorderViewsTestCase: OK!")

    def test_recorder_notify(self):
        """Test method recorder_notify()."""

        self.client = Client()

        record = Recorder.objects.get(id=1)
        url = reverse("record:recorder_notify", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content,
            b"nok: recordingPlace or " b"mediapath or key are missing",
        )

        response = self.client.get(
            url + "?key=abc&mediapath"
            "=/some/path&recordingPlace=16_3_10_37"
            "&course_title=title"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"nok: key is not valid")

        m = hashlib.md5()
        m.update(record.ipunder().encode("utf-8") + record.salt.encode("utf-8"))
        response = self.client.get(
            url + "?key=" + m.hexdigest() + "&mediapath=/some/path&recordingPlace"
            "=16_3_10_37&course_title=title"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

        print("   --->  test_record_notify of RecorderViewsTestCase: OK!")


class StudioPodTestView(TestCase):
    """Test case for Pod studio views."""

    fixtures = [
        "initial_data.json",
    ]

    def create_index_file(self):
        """Create and write a xml file."""
        text = """
        <html>
            <head>
            </head>
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
        if not (os.access(template_file, os.F_OK) and os.stat(template_file).st_size > 0):
            file = open(template_file, "w+")
            file.write(text)
            file.close()

    def setUp(self):
        """Create models to be tested."""
        User.objects.create(username="pod")
        print(" --->  SetUp of StudioPodTestView: OK!")

    def test_StudioPodTestView_get_request(self):
        """Test view studio_pod."""
        self.create_index_file()
        self.client = Client()
        url = reverse("recorder:studio_pod", kwargs={})

        # not logged
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # user logged in
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        print(" --->  test_StudioPodTestView_get_request of openCastTestView: OK!")

    def test_StudioPodTestView_get_request_restrict(self):
        """Test view studio_pod."""

        views.__REVATSO__ = True  # override setting value to test
        self.create_index_file()
        url = reverse("recorder:studio_pod", kwargs={})
        self.client = Client()

        # not logged
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # user logged in
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.context["access_not_allowed"], True)
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        views.__REVATSO__ = False
        print(
            " --->  test_StudioPodTestView_get_request_restrict ",
            "of StudioPodTestView: OK!",
        )

    def test_studio_presenter_post(self):
        """Test view presenter_post."""

        self.client = Client()
        url = reverse("recorder:presenter_post", kwargs={})

        # not logged
        self.client.get(url)
        self.assertRaises(PermissionDenied)

        # user logged in
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        # test get method
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

        response = self.client.post(url, {"presenter": "test"})
        self.assertEqual(response.status_code, 400)

        response = self.client.post(url, {"presenter": "mid"})
        self.assertEqual(response.status_code, 200)

        print(" -->  test_studio_presenter_post of StudioPodTestView: OK!")

    def test_studio_info_me_json(self):
        """Test view info_me_json."""

        self.client = Client()
        url = reverse("recorder:info_me_json", kwargs={})

        # not logged
        self.client.get(url)
        self.assertRaises(PermissionDenied)

        # user logged in
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertTrue(b"ROLE_ADMIN" in response.content)
        self.assertEqual(response.status_code, 200)

        print(" -->  test_studio_info_me_json of StudioPodTestView: OK!")

    def test_studio_ingest_createMediaPackage(self):
        """Test view ingest_createMediaPackage."""

        self.client = Client()
        url = reverse("recorder:ingest_createMediaPackage", kwargs={})

        # not logged
        self.client.get(url)
        self.assertRaises(PermissionDenied)

        # user logged in
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # check if response is xml
        mediaPackage_content = minidom.parseString(response.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia = mediapackage.getAttribute("id")
        presenter = mediapackage.getAttribute("presenter")
        self.assertEqual(presenter, OPENCAST_DEFAULT_PRESENTER)

        mediaPackage_dir = os.path.join(
            settings.MEDIA_ROOT, OPENCAST_FILES_DIR, "%s" % idMedia
        )
        mediaPackage_file = os.path.join(mediaPackage_dir, "%s.xml" % idMedia)
        self.assertTrue(os.path.exists(mediaPackage_file))

        mediaPackage_content = minidom.parse(mediaPackage_file)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        self.assertEqual(mediapackage.getAttribute("id"), idMedia)

        print(" -->  test_studio_ingest_createMediaPackage of StudioPodTestView: OK!")

    def test_studio_ingest_createMediaPackage_with_presenter(self):
        """Test view presenter_post."""

        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        url_presenter_post = reverse("recorder:presenter_post", kwargs={})
        response = self.client.post(url_presenter_post, {"presenter": "mid"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["presenter"], "mid")

        url_createMediaPackage = reverse("recorder:ingest_createMediaPackage", kwargs={})
        response = self.client.get(url_createMediaPackage)
        self.assertEqual(response.status_code, 200)

        mediaPackage_content = minidom.parseString(response.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        presenter = mediapackage.getAttribute("presenter")

        self.assertEqual(presenter, "mid")
        self.assertEqual(self.client.session.get("presenter", None), None)

        response = self.client.post(url_presenter_post, {"presenter": "piph"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["presenter"], "piph")

        response = self.client.get(url_createMediaPackage)
        self.assertEqual(response.status_code, 200)

        mediaPackage_content = minidom.parseString(response.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        presenter = mediapackage.getAttribute("presenter")

        self.assertEqual(presenter, "piph")
        self.assertEqual(self.client.session.get("presenter", None), None)

        print(
            " -->  test_studio_ingest_createMediaPackage_with_presenter"
            + " of StudioPodTestView",
            ": OK!",
        )

    def test_studio_ingest_addDCCatalog(self):
        """Test view ingest_addDCCatalog."""

        self.client = Client()
        url_addDCCatalog = reverse("recorder:ingest_addDCCatalog", kwargs={})

        # not logged
        self.client.get(url_addDCCatalog)
        self.assertRaises(PermissionDenied)

        # user logged in
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get(url_addDCCatalog)
        self.assertEqual(response.status_code, 400)

        # check if response is xml
        url_createMediaPackage = reverse("recorder:ingest_createMediaPackage", kwargs={})
        response_media_package = self.client.get(url_createMediaPackage)
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
            url_addDCCatalog,
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

        print(" -->  test_studio_ingest_addDCCatalog of StudioPodTestView: OK!")

    def test_studio_ingest_addAttachment(self):
        """Test view ingest_addAttachment."""

        self.client = Client()
        url_addAttachment = reverse("recorder:ingest_addAttachment", kwargs={})

        # user not logged
        response = self.client.get(url_addAttachment)
        self.assertRaises(PermissionDenied)

        # user logged in
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get(url_addAttachment)
        self.assertEqual(response.status_code, 400)

        url_createMediaPackage = reverse("recorder:ingest_createMediaPackage", kwargs={})
        response_media_package = self.client.get(url_createMediaPackage)
        mediaPackage_content = minidom.parseString(response_media_package.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia_sent = mediapackage.getAttribute("id")

        acl = SimpleUploadedFile(
            name="acl.xml",
            content="",  # not use in Pod
            content_type="application/xml",
        )

        response = self.client.post(
            url_addAttachment,
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

        print(" -->  test_studio_ingest_addAttachment of StudioPodTestView: OK!")

    def test_studio_ingest_addTrack(self):
        """Test view ingest_addTrack."""

        self.client = Client()
        url_addTrack = reverse("recorder:ingest_addTrack", kwargs={})

        # user not logged
        response = self.client.get(url_addTrack)
        self.assertRaises(PermissionDenied)

        # user logged in
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get(url_addTrack)
        self.assertEqual(response.status_code, 400)

        url_createMediaPackage = reverse("recorder:ingest_createMediaPackage", kwargs={})
        response_media_package = self.client.get(url_createMediaPackage)
        mediaPackage_content = minidom.parseString(response_media_package.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia_sent = mediapackage.getAttribute("id")

        video = SimpleUploadedFile(
            name="file.webm",
            content=b"empty file",
            content_type="video/webm",
        )

        response = self.client.post(
            url_addTrack,
            {
                "mediaPackage": mediaPackage_content.toxml(),
                "BODY": video,
                "flavor": "presenter/source",
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

        print(" -->  test_studio_ingest_addTrack of StudioPodTestView: OK!")

    def test_studio_ingest_addCatalog(self):
        """Test view ingest_addCatalog."""

        self.client = Client()
        url_addCatalog = reverse("recorder:ingest_addCatalog", kwargs={})

        # not logged
        response = self.client.get(url_addCatalog)
        self.assertRaises(PermissionDenied)

        # user logged in
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get(url_addCatalog)
        self.assertEqual(response.status_code, 400)

        url_createMediaPackage = reverse("recorder:ingest_createMediaPackage", kwargs={})
        response_media_package = self.client.get(url_createMediaPackage)
        mediaPackage_content = minidom.parseString(response_media_package.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia_sent = mediapackage.getAttribute("id")

        cutting = SimpleUploadedFile(
            name="cutting.smil",
            content=b'<smil xmlns="http://www.w3.org/ns/SMIL"><body>'
            + b'<par><video clipBegin="0.8s" clipEnd="4.327764s" /></par></body></smil>',
            content_type="text/xml",
        )

        response = self.client.post(
            url_addCatalog,
            {
                "mediaPackage": mediaPackage_content.toxml(),
                "BODY": cutting,
                "flavor": "smil/cutting",
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

        # check if mediaPackage_content has catalog with good type
        catalog = mediaPackage_content.getElementsByTagName("catalog")[0]
        self.assertTrue(catalog)
        self.assertEqual(catalog.getAttribute("type"), "smil/cutting")

        # check if dublin core file exist
        cutting_file = os.path.join(mediaPackage_dir, cutting.name)
        self.assertTrue(os.path.exists(cutting_file))

        print(" -->  test_studio_ingest_addCatalog of StudioPodTestView: OK!")

    def test_studio_ingest_ingest(self):
        """Test view ingest_ingest."""

        self.client = Client()
        url_ingest = reverse("recorder:ingest_ingest", kwargs={})

        # not logged
        response = self.client.get(url_ingest)
        self.assertRaises(PermissionDenied)

        # user logged in
        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get(url_ingest)
        self.assertEqual(response.status_code, 400)

        url_createMediaPackage = reverse("recorder:ingest_createMediaPackage", kwargs={})
        response_media_package = self.client.get(url_createMediaPackage)
        mediaPackage_content = minidom.parseString(response_media_package.content)
        mediapackage = mediaPackage_content.getElementsByTagName("mediapackage")[0]
        idMedia_sent = mediapackage.getAttribute("id")

        response = self.client.post(
            url_ingest,
            {
                "mediaPackage": mediaPackage_content.toxml(),
            },
        )
        self.assertRaises(PermissionDenied)

        videotype = Type.objects.create(title="others")
        recorder = Recorder.objects.create(
            name="recorder_studio",
            address_ip="16.3.10.37",
            type=videotype,
            directory="dir1",
            recording_type="studio",
        )
        # recorder.sites=get_current_site(None)
        # recorder.save()
        response = self.client.post(
            url_ingest,
            {
                "mediaPackage": mediaPackage_content.toxml(),
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
        # check if mediapackage file exist
        self.assertTrue(os.path.exists(mediaPackage_file))

        recording = Recording.objects.filter(
            user=self.user,
            title=idMedia,
            type="studio",
            # Source file corresponds to Pod XML file
            source_file=mediaPackage_file,
            recorder=recorder,
        )
        # check if recording object exist
        self.assertTrue(recording.first())

        print(" -->  test_studio_ingest_ingest of StudioPodTestView: OK!")


class StudioDigestViews(TestCase):
    """Test case for Pod studio views with Digest auth."""

    def test_digest_presenter_post(self):
        """Test Digest restriction on view presenter_post."""

        self.client = Client()
        url = reverse("recorder_digest:presenter_post", kwargs={})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_studio_pod of StudioDigestViews: OK!")

    def test_digest_studio_static(self):
        """Test Digest restriction on view studio_static."""

        self.client = Client()
        url = reverse("recorder_digest:studio_static", kwargs={"file": "test"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_studio_static of StudioDigestViews: OK!")

    def test_digest_settings_toml(self):
        """Test Digest restriction on view settings_toml."""

        self.client = Client()
        url = reverse("recorder_digest:settings_toml", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_settings_toml of StudioDigestViews: OK!")

    def test_digest_info_me_json(self):
        """Test Digest restriction on view info_me_json."""

        self.client = Client()
        url = reverse("recorder_digest:info_me_json", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_info_me_json of StudioDigestViews: OK!")

    def test_digest_ingest_createMediaPackage(self):
        """Test Digest restriction on view ingest_createMediaPackage."""

        self.client = Client()
        url = reverse("recorder_digest:ingest_createMediaPackage", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_ingest_createMediaPackage of StudioDigestViews: OK!")

    def test_digest_ingest_addDCCatalog(self):
        """Test Digest restriction on view ingest_addDCCatalog."""

        self.client = Client()
        url = reverse("recorder_digest:ingest_addDCCatalog", kwargs={})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_ingest_addDCCatalog of StudioDigestViews: OK!")

    def test_digest_ingest_addAttachment(self):
        """Test Digest restriction on view ingest_addAttachment."""

        self.client = Client()
        url = reverse("recorder_digest:ingest_addAttachment", kwargs={})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_ingest_addAttachment of StudioDigestViews: OK!")

    def test_digest_ingest_addTrack(self):
        """Test Digest restriction on view ingest_addTrack."""

        self.client = Client()
        url = reverse("recorder_digest:ingest_addTrack", kwargs={})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_ingest_addTrack of StudioDigestViews: OK!")

    def test_digest_ingest_addCatalog(self):
        """Test Digest restriction on view ingest_addCatalog."""

        self.client = Client()
        url = reverse("recorder_digest:ingest_addCatalog", kwargs={})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_ingest_addCatalog of StudioDigestViews: OK!")

    def test_digest_ingest_ingest(self):
        """Test Digest restriction on view ingest_ingest."""

        self.client = Client()
        url = reverse("recorder_digest:ingest_ingest", kwargs={})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_ingest_ingest of StudioDigestViews: OK!")

    def test_digest_hosts_json(self):
        """Test Digest restriction on view hosts_json."""

        self.client = Client()
        url = reverse("recorder_digest:hosts_json", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_hosts_json of StudioDigestViews: OK!")

    def test_digest_capture_admin_config(self):
        """Test Digest restriction on view capture_admin_config."""

        self.client = Client()
        url = reverse("recorder_digest:capture_admin_config", kwargs={"name": "test"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_capture_admin_config of StudioDigestViews: OK!")

    def test_digest_capture_admin(self):
        """Test Digest restriction on view capture_admin_agent."""

        self.client = Client()
        url = reverse("recorder_digest:capture_admin_agent", kwargs={"name": "test"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_capture_admin of StudioDigestViews: OK!")

    def test_digest_admin_ng_series(self):
        """Test Digest restriction on view admin_ng_series."""

        self.client = Client()
        url = reverse("recorder_digest:admin_ng_series", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_admin_ng_series of StudioDigestViews: OK!")

    def test_digest_services_available(self):
        """Test Digest restriction on view services_available."""

        self.client = Client()
        url = reverse("recorder_digest:services_available", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_digest_services_available of StudioDigestViews: OK!")
