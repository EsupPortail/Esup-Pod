"""Esup-Pod - Unit tests for recorder utils."""

import os
import time
from xml.dom import minidom  # nosec

from django.conf import settings
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase

from pod.video.models import Type
from ..models import Recorder, Recording
from ..utils import (
    add_comment,
    studio_clean_old_entries,
    get_id_media,
    create_xml_element,
    create_digest_auth_response,
    get_auth_headers_as_dict,
    digest_is_valid,
    compute_digest,
)
from ...settings import BASE_DIR

MEDIA_ROOT = getattr(settings, "MEDIA_ROOT", os.path.join(BASE_DIR, "media"))
OPENCAST_FILES_DIR = getattr(settings, "OPENCAST_FILES_DIR", "opencast-files")


class UtilsTestCase(TestCase):
    """Test case for utils methods."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Create models to be tested."""
        r_type = Type.objects.create(title="others")
        user = User.objects.create(username="pod")
        recorder1 = Recorder.objects.create(
            id=1,
            user=user,
            name="rec1",
            address_ip="127.1.1.1",
            type=r_type,
            cursus="0",
            directory="dir1",
        )
        source_file = "/home/pod/files/video.mp4"
        v_type = "video"
        recording = Recording.objects.create(
            user=user,
            title="media1",
            type=v_type,
            source_file=source_file,
            recorder=recorder1,
            comment="line1",
        )
        recording.save()

        print(" --->  SetUp of UtilsTestCase: OK!")

    def test_add_comment(self) -> None:
        """Test method add_comment()."""
        recording = Recording.objects.get(id=1)
        first_comment = recording.comment
        new_comment = "line2"
        add_comment(recording.id, new_comment)

        recording = Recording.objects.get(id=1)
        self.assertEqual(recording.comment, first_comment + "\n" + new_comment)
        print("   --->  test_add_comment of UtilsTestCase: OK !")

    def test_clean_old_files(self) -> None:
        """Test case for cleaning old folders in opencast-files directory."""
        opencast_dir_path = os.path.join(MEDIA_ROOT, OPENCAST_FILES_DIR)

        # create a directory with a text file
        opencast_test_dir = os.path.join(opencast_dir_path, "test_dir")
        os.makedirs(opencast_test_dir, exist_ok=True)
        with open(os.path.join(opencast_test_dir, "dummy.txt"), "w") as f:
            f.write("dummy text")

        # create a file
        opencast_test_file = os.path.join(opencast_dir_path, "test_file.txt")
        with open(opencast_test_file, "w") as f:
            f.write("another dummy text")

        # must exist
        self.assertTrue(os.path.exists(opencast_test_dir))
        self.assertTrue(os.path.exists(opencast_test_file))

        # and dir and file are not deleted
        studio_clean_old_entries()
        self.assertTrue(os.path.exists(opencast_test_dir))
        self.assertTrue(os.path.exists(opencast_test_file))

        # change creation and modification datetime of the dir and file
        new_time = time.time() - 8 * 86400
        os.utime(opencast_test_dir, (new_time, new_time))
        os.utime(opencast_test_file, (new_time, new_time))

        # test that dir and file are deleted
        studio_clean_old_entries()
        self.assertFalse(os.path.exists(opencast_test_dir))
        self.assertFalse(os.path.exists(opencast_test_file))

        print("   --->  test_clean_old_files of UtilsTestCase: OK !")

    def test_get_id_media(self) -> None:
        """Test method get_id_media()."""
        # Test with no data
        request = RequestFactory().post("/")
        id_media = get_id_media(request)
        self.assertIsNone(id_media)

        # Test with invalid data
        request = RequestFactory().post("/", {"mediaPackage": ""})
        id_media = get_id_media(request)
        self.assertIsNone(id_media)

        # Test with invalid data
        request = RequestFactory().post("/", {"mediaPackage": "{}"})
        id_media = get_id_media(request)
        self.assertIsNone(id_media)

        # Test with a mediaPackage XML
        media_package_xml = """
                    <mediapackage id="1111">
                        <other_tag>xxx</other_tag>
                    </mediapackage>
                """
        request = RequestFactory().post("/", {"mediaPackage": media_package_xml})
        id_media = get_id_media(request)
        self.assertEqual(id_media, "1111")

        print("   --->  test_get_id_media of UtilsTestCase: OK !")

    def test_create_xml_element(self) -> None:
        """Test method create_xml_element()."""
        # Create a mock mediaPackage_content
        mediaPackage_content = minidom.Document()

        element_name = "not_track"
        type_name = "type"
        mimetype = "application/pdf"
        url_text = "https://example.com/document.pdf"
        element = create_xml_element(
            mediaPackage_content, element_name, type_name, mimetype, url_text
        )

        # Check filename does not exist
        self.assertFalse(element.hasAttribute("filename"))

        # Call the function
        element_name = "track"
        type_name = "audio"
        mimetype = "audio/mpeg"
        url_text = "https://example.com/audio.mp3"
        opencast_filename = "audio.mp3"
        element = create_xml_element(
            mediaPackage_content,
            element_name,
            type_name,
            mimetype,
            url_text,
            opencast_filename,
        )

        # Check that the element is created correctly
        self.assertEqual(element.nodeName, element_name)
        self.assertEqual(element.getAttribute("type"), type_name)
        self.assertEqual(element.getAttribute("filename"), opencast_filename)

        # Check that the mimetype and url child elements are created and appended
        self.assertEqual(len(element.getElementsByTagName("mimetype")), 1)
        self.assertEqual(len(element.getElementsByTagName("url")), 1)

        # Check the content of the mimetype and url elements
        mimetype_element = element.getElementsByTagName("mimetype")[0]
        url_element = element.getElementsByTagName("url")[0]
        self.assertEqual(mimetype_element.firstChild.nodeValue, mimetype)
        self.assertEqual(url_element.firstChild.nodeValue, url_text)

        # Check the optional "live" element for track
        live_element = element.getElementsByTagName("live")
        self.assertEqual(len(live_element), 1)
        self.assertEqual(live_element[0].firstChild.nodeValue, "false")


class DigestTestCase(TestCase):
    """Test case for Pod recorder digest methods."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Create models to be tested."""
        r_type = Type.objects.create(title="others")
        user = User.objects.create(username="pod")
        recorder = Recorder.objects.create(
            id=1,
            user=user,
            name="recorder1",
            address_ip="127.1.1.1",
            type=r_type,
            directory="dir1",
            recording_type="video",
            salt="pepper",
            credentials_login="inner_login",
        )
        recorder.save()
        print(" --->  SetUp of UtilsTestCase: OK!")

    def test_create_digest_auth_response(self) -> None:
        """Test method create_digest_auth_response()."""
        request = RequestFactory().get("/")

        # test 403
        request.META["REMOTE_ADDR"] = "999.99.99.99"
        response = create_digest_auth_response(request)
        self.assertEqual(response.status_code, 403)

        # test 401
        recorder = Recorder.objects.get(id=1)
        request.META["REMOTE_ADDR"] = recorder.address_ip
        response = create_digest_auth_response(request)

        self.assertEqual(response.status_code, 401)
        self.assertTrue("WWW-Authenticate" in response)
        self.assertIn(recorder.salt, response["WWW-Authenticate"])

        print("   --->  test_create_digest_auth_response of DigestTestCase: OK!")

    def test_get_auth_headers_as_dict(self) -> None:
        """Test method get_auth_headers_as_dict()."""
        # test no auth_headers
        request = RequestFactory().get("/")
        response = get_auth_headers_as_dict(request)
        self.assertEqual(response, {})

        # headers with key Authorization
        header = {"HTTP_Authorization": 'a="1", b="2"'}
        request = RequestFactory().get("/", {}, **header)
        response = get_auth_headers_as_dict(request)
        self.assertEqual(response, {"a": "1", "b": "2"})

        print("   --->  test_get_auth_headers_as_dict of DigestTestCase: OK!")

    def test_digest_is_valid(self) -> None:
        """Test digest validation."""
        # test no auth_headers
        request = RequestFactory().get("/")
        response = digest_is_valid(request)
        self.assertFalse(response)

        # request with Authorization header but needed keys missing (missing data to compute hash)
        header = {"HTTP_Authorization": 'a="1"'}
        request = RequestFactory().get("/", {}, **header)
        response = digest_is_valid(request)
        self.assertFalse(response)

        # request with Authorization header having keys
        header = {"HTTP_Authorization": 'username="", realm="", uri="", response=""'}
        request = RequestFactory().get("/", {}, **header)

        # test ip does not match any Recorder address_ip
        request.META["REMOTE_ADDR"] = "999.99.99.99"
        response = digest_is_valid(request)
        self.assertFalse(response)

        # test ip match but recorder.credentials_login is wrong
        recorder = Recorder.objects.get(id=1)
        request.META["REMOTE_ADDR"] = recorder.address_ip
        response = digest_is_valid(request)
        self.assertFalse(response)

        # compute digest
        login = recorder.credentials_login
        realm = "any"
        passw = recorder.credentials_password
        method = "GET"
        uri = "/"
        salt = recorder.salt
        computed = compute_digest(login, realm, passw, method, uri, salt)

        # Request Ip and Username match Recorder address_ip and credentials_login
        # Computed Hash sent by the client must be the same as th one calculated by the server
        header = {
            "HTTP_Authorization": 'username="'
            + login
            + '",realm="'
            + realm
            + '",uri="'
            + uri
            + '",response="'
            + computed
            + '"'
        }

        request = RequestFactory().get(uri, {}, **header)
        request.META["REMOTE_ADDR"] = recorder.address_ip
        response = digest_is_valid(request)
        self.assertTrue(response)
        print("   --->  test_digest_is_valid of DigestTestCase: OK!")
