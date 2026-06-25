"""
Esup-Pod - Import Video tests.
"""

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from src.apps.import_video.models import ExternalRecording
from src.apps.import_video.serializers import ExternalRecordingSerializer
from src.apps.import_video.views import ExternalRecordingViewSet

User = get_user_model()


class ExternalRecordingModelTests(APITestCase):
    """Tests for the ExternalRecording model."""

    def setUp(self):
        """Sets up a staff user, a site, and a recording for model testing."""
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(
            username="staff_user",
            password="password",
            is_staff=True,
        )
        self.recording = ExternalRecording.objects.create(
            name="Test Recording",
            owner=self.user,
            site=self.site,
            source_type=ExternalRecording.SourceType.YOUTUBE,
            source_url="https://www.youtube.com/watch?v=test123",
        )

    def test_create_external_recording(self):
        """Verifies that an ExternalRecording can be created with correct defaults."""
        self.assertEqual(self.recording.name, "Test Recording")
        self.assertEqual(self.recording.source_type, ExternalRecording.SourceType.YOUTUBE)
        self.assertEqual(
            self.recording.import_status, ExternalRecording.ImportStatus.PENDING
        )
        self.assertIsNone(self.recording.video)
        self.assertEqual(self.recording.error_message, "")

    def test_external_recording_str(self):
        """Verifies the string representation of ExternalRecording."""
        self.assertIn("Test Recording", str(self.recording))
        self.assertIn("YouTube", str(self.recording))
        self.assertIn("Pending", str(self.recording))

    def test_default_import_status_is_pending(self):
        """Verifies that the default import status is PENDING."""
        self.assertEqual(
            self.recording.import_status, ExternalRecording.ImportStatus.PENDING
        )


class ExternalRecordingSerializerTests(APITestCase):
    """Tests for the ExternalRecordingSerializer validation."""

    def test_invalid_youtube_url(self):
        """Rejects a source_url that is not a valid YouTube URL."""
        site = Site.objects.get_current()
        data = {
            "name": "Bad YouTube",
            "source_type": ExternalRecording.SourceType.YOUTUBE,
            "source_url": "https://www.notyoutube.com/video/abc",
            "site": site.id,
        }
        serializer = ExternalRecordingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("source_url", serializer.errors)

    def test_invalid_peertube_url(self):
        """Rejects a source_url that is not a valid PeerTube URL."""
        site = Site.objects.get_current()
        data = {
            "name": "Bad PeerTube",
            "source_type": ExternalRecording.SourceType.PEERTUBE,
            "source_url": "https://peertube.example.com/not-a-video",
            "site": site.id,
        }
        serializer = ExternalRecordingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("source_url", serializer.errors)

    def test_invalid_bbb_url(self):
        """Rejects a source_url that is not a valid BBB recording URL."""
        site = Site.objects.get_current()
        data = {
            "name": "Bad BBB",
            "source_type": ExternalRecording.SourceType.BBB,
            "source_url": "https://bbb.example.com/not-a-valid-url",
            "site": site.id,
        }
        serializer = ExternalRecordingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("source_url", serializer.errors)

    def test_valid_youtube_url(self):
        """Accepts a valid YouTube URL."""
        site = Site.objects.get_current()
        data = {
            "name": "Good YouTube",
            "source_type": ExternalRecording.SourceType.YOUTUBE,
            "source_url": "https://www.youtube.com/watch?v=abc123",
            "site": site.id,
        }
        serializer = ExternalRecordingSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_peertube_url(self):
        """Accepts a valid PeerTube URL."""
        site = Site.objects.get_current()
        data = {
            "name": "Good PeerTube",
            "source_type": ExternalRecording.SourceType.PEERTUBE,
            "source_url": "https://peertube.example.com/videos/watch/abc-123",
            "site": site.id,
        }
        serializer = ExternalRecordingSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


class ExternalRecordingViewSetTests(APITestCase):
    """Tests for the ExternalRecordingViewSet API endpoints."""

    def setUp(self):
        """Sets up users, site, and a recording for API testing."""
        self.factory = APIRequestFactory()
        self.site = Site.objects.get_current()
        self.staff_user = User.objects.create_user(
            username="staff",
            password="password",
            is_staff=True,
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="password",
            is_staff=False,
        )
        self.recording = ExternalRecording.objects.create(
            name="API Test Recording",
            owner=self.staff_user,
            site=self.site,
            source_type=ExternalRecording.SourceType.VIDEO_FILE,
            source_url="https://example.com/video.mp4",
        )

    def test_import_blocked_if_processing(self):
        """Import action returns 400 if recording is already PROCESSING."""
        self.recording.import_status = ExternalRecording.ImportStatus.PROCESSING
        self.recording.save()

        view = ExternalRecordingViewSet.as_view({"post": "import_to_pod"})
        request = self.factory.post("/")
        force_authenticate(request, user=self.staff_user)
        response = view(request, id=self.recording.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_import_blocked_if_done(self):
        """Import action returns 400 if recording is already DONE."""
        self.recording.import_status = ExternalRecording.ImportStatus.DONE
        self.recording.save()

        view = ExternalRecordingViewSet.as_view({"post": "import_to_pod"})
        request = self.factory.post("/")
        force_authenticate(request, user=self.staff_user)
        response = view(request, id=self.recording.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_import_from_error(self):
        """Reset action sets status back to PENDING from ERROR."""
        self.recording.import_status = ExternalRecording.ImportStatus.ERROR
        self.recording.error_message = "Something went wrong."
        self.recording.save()

        view = ExternalRecordingViewSet.as_view({"post": "reset_import"})
        request = self.factory.post("/")
        force_authenticate(request, user=self.staff_user)
        response = view(request, id=self.recording.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recording.refresh_from_db()
        self.assertEqual(
            self.recording.import_status, ExternalRecording.ImportStatus.PENDING
        )
        self.assertEqual(self.recording.error_message, "")

    def test_reset_blocked_if_processing(self):
        """Reset action returns 400 if recording is currently PROCESSING."""
        self.recording.import_status = ExternalRecording.ImportStatus.PROCESSING
        self.recording.save()

        view = ExternalRecordingViewSet.as_view({"post": "reset_import"})
        request = self.factory.post("/")
        force_authenticate(request, user=self.staff_user)
        response = view(request, id=self.recording.id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_staff_cannot_create_if_restricted(self):
        """Non-staff user cannot create a recording when restrict_to_staff is True."""
        from src.apps.import_video.conf import import_video_settings

        import_video_settings.restrict_to_staff = True

        view = ExternalRecordingViewSet.as_view({"post": "create"})
        data = {
            "name": "Unauthorized Recording",
            "source_type": ExternalRecording.SourceType.VIDEO_FILE,
            "source_url": "https://example.com/video.mp4",
            "site": self.site.id,
        }
        request = self.factory.post("/", data)
        force_authenticate(request, user=self.other_user)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_create(self):
        """Staff user can create a recording."""
        view = ExternalRecordingViewSet.as_view({"post": "create"})
        data = {
            "name": "Staff Recording",
            "source_type": ExternalRecording.SourceType.VIDEO_FILE,
            "source_url": "https://example.com/video.mp4",
            "site": self.site.id,
        }
        request = self.factory.post("/", data)
        force_authenticate(request, user=self.staff_user)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
