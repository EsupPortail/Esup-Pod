"""
Tests the views for import_video module.

*  run with `python manage.py test pod.import_video.tests.test_views`

"""

import os
from ..models import ExternalRecording
from ..views import bbb_encode_presentation, bbb_encode_presentation_and_upload_to_pod
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from http import HTTPStatus

# Directory that will contain the video files generated by bbb-recorder
IMPORT_VIDEO_BBB_RECORDER_PATH = getattr(
    settings,
    "IMPORT_VIDEO_BBB_RECORDER_PATH",
    "/data/bbb-recorder/media/"
)


class ExternalRecordingDeleteTestView(TestCase):
    """List of view tests for deleting an external recording.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        """Set up contents before Delete Recording tests."""
        site = Site.objects.get(id=1)

        user = User.objects.create(username="pod", password="pod1234pod")
        user.owner.sites.add(Site.objects.get_current())
        user.is_staff = True
        user.save()
        user.owner.save()

        ExternalRecording.objects.create(
            id=1,
            name="test recording1",
            site=site,
            owner=user,
            type="bigbluebutton",
            source_url="https://bbb.url",
        )

        user2 = User.objects.create(username="pod2", password="pod1234pod")
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()

        print(" --->  SetUp of ExternalRecordingDeleteTestView: OK!")

    def test_recording_TestView_get_request_restrict(self):
        """Test the list of recordings."""
        self.client = Client()
        url = reverse("import_video:external_recordings", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertTrue(b"test recording1" in response.content)
        print(
            " --->  test_recording_TestView_get_request_restrict ",
            "of recording_TestView: OK!",
        )

    def test_recording_delete_get_request(self):
        """Test recording delete with Get request."""
        self.client = Client()
        # check auth
        url = reverse(
            "import_video:delete_external_recording",
            kwargs={"id": 2523},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse(
            "import_video:delete_external_recording",
            kwargs={"id": 2523},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # check access right
        recording = ExternalRecording.objects.get(name="test recording1")
        url = reverse(
            "import_video:delete_external_recording",
            kwargs={
                "id": recording.id,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        # No POST request
        self.assertEqual(response.status_code, 403)

        # With POST, good user, good URL
        response = self.client.post(
            url,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        print(" --->  test_recording_delete_get_request of RecordingDeleteTestView: OK!")


class ExternalRecordingUploadTestView(TestCase):
    """List of view tests for upload to Pod an external recording.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        """Set up for tests views."""
        site = Site.objects.get(id=1)

        user = User.objects.create(username="pod", password="pod1234pod")
        user.save()
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        user2 = User.objects.create(username="pod2", password="pod1234pod")
        user2.is_staff = True
        user2.save()

        ExternalRecording.objects.create(
            id=2,
            name="test youtube recording1",
            site=site,
            owner=user2,
            type="youtube",
            source_url="https://youtube.url",
        )
        ExternalRecording.objects.create(
            id=3,
            name="test peertube recording1",
            site=site,
            owner=user2,
            type="peertube",
            source_url="https://peertube.url",
        )
        ExternalRecording.objects.create(
            id=4,
            name="test external bbb recording1",
            site=site,
            owner=user2,
            type="bigbluebutton",
            source_url="https://bbb.url",
        )
        ExternalRecording.objects.create(
            id=5,
            name="test direct video recording1",
            site=site,
            owner=user2,
            type="video",
            source_url="https://video.url",
        )
        ExternalRecording.objects.create(
            id=6,
            name="test mediacad video recording1",
            site=site,
            owner=user2,
            type="video",
            source_url="https://mediacad.url",
        )

        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of ExternalRecordingUploadTestView: OK!")

    def test_recording_upload_get_request(self):
        """Test recording upload with Get request."""
        self.client = Client()
        # check auth
        url = reverse(
            "import_video:upload_external_recording_to_pod",
            kwargs={"record_id": 2523},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth
        # check recording
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse(
            "import_video:upload_external_recording_to_pod",
            kwargs={"record_id": 2523},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # check access right
        recording = ExternalRecording.objects.get(name="test youtube recording1")
        url = reverse(
            "import_video:upload_external_recording_to_pod",
            kwargs={
                "record_id": recording.id,
            },
        )
        # Get Request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_recording_upload_post_request(self):
        """Test recording upload with Post request."""
        unable_str = _("Unable to upload the video to Pod").encode("utf-8")

        # Check upload for external recording
        # Youtube type
        recordingYt = ExternalRecording.objects.get(name="test youtube recording1")
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse(
            "import_video:upload_external_recording_to_pod",
            kwargs={"record_id": recordingYt.id},
        )
        response = self.client.post(
            url,
            {
                "recording_name": "test youtube recording1",
                "source_url": "https://youtube.url",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Message for a bad URL
        self.assertTrue(
            _("YouTube content is inaccessible.").encode("utf-8") in response.content
        )

        # Peertube type
        recordingPt = ExternalRecording.objects.get(name="test peertube recording1")
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse(
            "import_video:upload_external_recording_to_pod",
            kwargs={"record_id": recordingPt.id},
        )
        response = self.client.post(
            url,
            {
                "recording_name": "test peertube recording1",
                "source_url": "https://peertube.url",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Message for a bad URL
        self.assertTrue(unable_str in response.content)

        # External BBB type
        recordingBBB = ExternalRecording.objects.get(name="test external bbb recording1")
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse(
            "import_video:upload_external_recording_to_pod",
            kwargs={"record_id": recordingBBB.id},
        )
        response = self.client.post(
            url,
            {
                "recording_name": "test external bbb recording1",
                "source_url": "https://bbb.url",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Message for a bad URL
        self.assertTrue(unable_str in response.content)

        # Video type
        recordingVideo = ExternalRecording.objects.get(
            name="test direct video recording1"
        )
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse(
            "import_video:upload_external_recording_to_pod",
            kwargs={"record_id": recordingVideo.id},
        )
        response = self.client.post(
            url,
            {
                "recording_name": "test direct video recording1",
                "source_url": "https://video.url",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Message for a bad URL
        self.assertTrue(unable_str in response.content)

        # Video type - Mediacad video
        recordingMediacad = ExternalRecording.objects.get(
            name="test mediacad video recording1"
        )
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse(
            "import_video:upload_external_recording_to_pod",
            kwargs={"record_id": recordingMediacad.id},
        )
        response = self.client.post(
            url,
            {
                "recording_name": "test mediacad video recording1",
                "source_url": "https://video.url",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Message for a bad URL
        self.assertTrue(unable_str in response.content)

        print(" --->  test_recording_upload_get_request of RecordingUploadTestView: OK!")

    def test_recording_encode_presentation(self):
        """Test recording encode presentation."""
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)

        # Encode presentation
        recordingBBB = ExternalRecording.objects.get(name="test external bbb recording1")
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        expected = os.path.join(IMPORT_VIDEO_BBB_RECORDER_PATH, "video.webm")
        actual = bbb_encode_presentation(
            "video.webm",
            recordingBBB.source_url,
        )
        self.assertEqual(actual, expected)
        # Encode presentation and move to destination
        # Expected state
        expected = _(
            "Impossible to upload to Pod the video, "
            "the link provided does not seem valid."
        )
        bbb_encode_presentation_and_upload_to_pod(
            recordingBBB.id,
            recordingBBB.source_url,
            "webm"
        )
        recordingBBB = ExternalRecording.objects.get(name="test external bbb recording1")
        self.assertEqual(recordingBBB.state, expected)

        print(" --->  test_recording_encode_presentation of RecordingUploadTestView: OK!")
