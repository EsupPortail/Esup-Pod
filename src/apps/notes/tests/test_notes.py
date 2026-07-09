"""
Esup-Pod - Notes tests.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from rest_framework import status
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from src.apps.notes.models import VideoNote
from src.apps.notes.serializers import VideoNoteSerializer
from src.apps.notes.views import VideoNoteViewSet
from src.apps.video.apps import sync_metadata
from src.apps.video.models import Video

User = get_user_model()


class VideoNoteModelTests(APITestCase):
    """Tests for the VideoNote model."""

    def setUp(self):
        """Sets up a user and a video for model testing."""
        sync_metadata(sender=None)
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(
            username="noter", password="password"
        )  # nosec
        self.video = Video.objects.create(
            title="Note Test Video",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )
        self.video.sites.add(self.site)

    def test_create_private_note(self):
        """Verifies that a private note can be created."""
        note = VideoNote.objects.create(
            video=self.video,
            owner=self.user,
            content="My private note",
            privacy=VideoNote.PrivacyStatus.PRIVATE,
        )
        self.assertEqual(note.content, "My private note")
        self.assertEqual(note.privacy, VideoNote.PrivacyStatus.PRIVATE)
        self.assertIsNone(note.timestamp)

    def test_create_note_with_timestamp(self):
        """Verifies that a note with a timestamp can be created."""
        note = VideoNote.objects.create(
            video=self.video,
            owner=self.user,
            content="Note at 30s",
            timestamp=30,
        )
        self.assertEqual(note.timestamp, 30)

    def test_note_str(self):
        """Verifies the string representation of a note."""
        note = VideoNote.objects.create(
            video=self.video,
            owner=self.user,
            content="Hello world",
            timestamp=10,
        )
        self.assertIn("noter", str(note))
        self.assertIn("10s", str(note))
        self.assertIn("Hello world", str(note))

    def test_note_str_without_timestamp(self):
        """Verifies the string representation of a note without timestamp."""
        note = VideoNote.objects.create(
            video=self.video,
            owner=self.user,
            content="Global note",
        )
        self.assertNotIn("@", str(note))


class VideoNoteViewSetTests(APITestCase):
    """Tests for the VideoNote API endpoints."""

    def setUp(self):
        """Sets up users, site, video and notes for API testing."""
        sync_metadata(sender=None)
        self.factory = APIRequestFactory()
        self.site = Site.objects.get_current()

        self.owner = User.objects.create_user(
            username="owner", password="password"
        )  # nosec
        self.other_user = User.objects.create_user(
            username="other", password="password"
        )  # nosec

        self.video = Video.objects.create(
            title="Test Video",
            owner=self.owner,
            status=Video.Status.PUBLISHED,
        )
        self.video.sites.add(self.site)

        self.private_note = VideoNote.objects.create(
            video=self.video,
            owner=self.owner,
            content="Private note",
            privacy=VideoNote.PrivacyStatus.PRIVATE,
        )
        self.public_note = VideoNote.objects.create(
            video=self.video,
            owner=self.owner,
            content="Public note",
            privacy=VideoNote.PrivacyStatus.PUBLIC,
        )

        # Patch the setting so tests pass
        patcher = patch(
            "src.apps.notes.views.VideoNoteViewSet.notes_settings.use_notes", True
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def test_owner_sees_own_private_note(self):
        """Owner can see their own private note."""
        view = VideoNoteViewSet.as_view({"get": "list"})
        request = self.factory.get("/", {"video": self.video.slug})
        force_authenticate(request, user=self.owner)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contents = [n["content"] for n in response.data["results"]]
        self.assertIn("Private note", contents)
        self.assertIn("Public note", contents)

    def test_other_user_cannot_see_private_note(self):
        """Other users cannot see private notes."""
        view = VideoNoteViewSet.as_view({"get": "list"})
        request = self.factory.get("/", {"video": self.video.slug})
        force_authenticate(request, user=self.other_user)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        contents = [n["content"] for n in response.data["results"]]
        self.assertNotIn("Private note", contents)
        self.assertIn("Public note", contents)

    def test_create_note(self):
        """Authenticated user can create a note."""
        view = VideoNoteViewSet.as_view({"post": "create"})
        data = {
            "video": self.video.id,
            "content": "New note",
            "privacy": VideoNote.PrivacyStatus.PRIVATE,
        }
        request = self.factory.post("/", data)
        force_authenticate(request, user=self.owner)
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "New note")
        self.assertEqual(response.data["owner"], "owner")

    def test_other_user_cannot_delete_note(self):
        """Other users cannot delete someone else's note."""
        view = VideoNoteViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete("/")
        force_authenticate(request, user=self.other_user)
        response = view(request, pk=self.public_note.pk)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete_own_note(self):
        """Owner can delete their own note."""
        view = VideoNoteViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete("/")
        force_authenticate(request, user=self.owner)
        response = view(request, pk=self.private_note.pk)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(VideoNote.objects.filter(pk=self.private_note.pk).exists())

    def test_owner_can_update_own_note(self):
        """Owner can update their own note."""
        view = VideoNoteViewSet.as_view({"patch": "partial_update"})
        request = self.factory.patch("/", {"content": "Updated content"})
        force_authenticate(request, user=self.owner)
        response = view(request, pk=self.public_note.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], "Updated content")

    def test_unauthenticated_cannot_access(self):
        """Unauthenticated users cannot access notes."""
        view = VideoNoteViewSet.as_view({"get": "list"})
        request = self.factory.get("/", {"video": self.video.slug})
        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_negative_timestamp_rejected(self):
        """Negative timestamps are rejected by the serializer."""
        data = {
            "video": self.video.id,
            "content": "Bad timestamp",
            "timestamp": -5,
        }
        serializer = VideoNoteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("timestamp", serializer.errors)

    @patch("src.apps.notes.views.VideoNoteViewSet.notes_settings.use_notes", False)
    def test_feature_disabled_returns_400(self):
        """Returns 400 when USE_NOTES is disabled."""
        view = VideoNoteViewSet.as_view({"get": "list"})
        request = self.factory.get("/", {"video": self.video.slug})
        force_authenticate(request, user=self.owner)
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
