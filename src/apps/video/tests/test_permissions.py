"""
Esup-Pod - Video permissions tests.
"""

import tempfile
import shutil


from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from src.apps.video.models import Video

User = get_user_model()

# noscan
PWD = "password"

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class VideoPermissionsTests(APITestCase):
    """
    Tests based on the provided Access Control Matrices.
    Matrix 1: Role-based permissions (default config).
    Matrix 2: Video status-based permissions.
    """

    @classmethod
    def tearDownClass(cls):
        """Cleans up temporary media directory after tests."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """Sets up various users and videos with different statuses for permission testing."""
        self.user_owner = User.objects.create_user(username="owner", password=PWD)
        self.user_other = User.objects.create_user(username="other", password=PWD)
        self.user_admin = User.objects.create_superuser(username="admin", password=PWD)

        self.video_content = SimpleUploadedFile(
            "test.mp4", b"file_content", content_type="video/mp4"
        )

        self.video_published = Video.objects.create(
            title="Published Video",
            owner=self.user_owner,
            status=Video.Status.PUBLISHED,
            video_file=self.video_content,
        )

        self.video_restricted = Video.objects.create(
            title="Restricted Video",
            owner=self.user_owner,
            status=Video.Status.RESTRICTED,
            is_auth_required=True,
            video_file=self.video_content,
            duration=120,
        )
        Video.objects.filter(pk=self.video_restricted.pk).update(
            status=Video.Status.RESTRICTED, duration=1
        )
        self.video_restricted.refresh_from_db()

        self.video_draft = Video.objects.create(
            title="Draft Video",
            owner=self.user_owner,
            video_file=self.video_content,
        )
        Video.objects.filter(pk=self.video_draft.pk).update(
            status=Video.Status.DRAFT, duration=1
        )
        self.video_draft.refresh_from_db()

        self.list_url = "/api/videos/"
        self.detail_url = lambda slug: f"/api/videos/{slug}/"

    def test_anonymous_access(self):
        """
        Role: Anonymous
        - Can view PUBLISHED: Yes
        - Can view RESTRICTED: No
        - Can view DRAFT: No
        """
        self.client.logout()

        response = self.client.get(self.list_url)
        results = (
            response.data["results"]
            if isinstance(response.data, dict) and "results" in response.data
            else response.data
        )

        ids = [v["id"] for v in results]
        self.assertIn(self.video_published.id, ids)
        self.assertNotIn(self.video_restricted.id, ids)
        self.assertNotIn(self.video_draft.id, ids)

        response = self.client.get(self.detail_url(self.video_published.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.detail_url(self.video_restricted.slug))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(self.detail_url(self.video_draft.slug))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_access_non_owner(self):
        """
        Role: Authenticated (Non-Owner)
        - Can view PUBLISHED: Yes
        - Can view RESTRICTED: Yes
        - Can view DRAFT: No
        """
        self.client.force_authenticate(user=self.user_other)

        response = self.client.get(self.list_url)
        results = (
            response.data["results"]
            if isinstance(response.data, dict) and "results" in response.data
            else response.data
        )

        ids = [v["id"] for v in results]
        self.assertIn(self.video_published.id, ids)
        self.assertIn(self.video_restricted.id, ids)
        self.assertNotIn(self.video_draft.id, ids)

        response = self.client.get(self.detail_url(self.video_restricted.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_access(self):
        """
        Role: Owner
        - Can view DRAFT: Yes (it's mine)
        - Can update: Yes
        - Can delete: Yes
        """
        self.client.force_authenticate(user=self.user_owner)

        response = self.client.get(self.list_url)
        results = (
            response.data["results"]
            if isinstance(response.data, dict) and "results" in response.data
            else response.data
        )

        ids = [v["id"] for v in results]
        self.assertIn(self.video_draft.id, ids)

        data = {"title": "Updated Title"}
        response = self.client.patch(self.detail_url(self.video_draft.slug), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video_draft.refresh_from_db()
        self.assertEqual(self.video_draft.title, "Updated Title")

        response = self.client.delete(self.detail_url(self.video_draft.slug))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Video.objects.filter(id=self.video_draft.id).exists())

    @patch("src.apps.encoding.tasks.trigger_runner_encoding_task.delay")
    def test_create_video(self, mock_trigger):
        """Test video creation."""
        self.client.force_authenticate(user=self.user_owner)

        video_file = SimpleUploadedFile(
            "new.mp4", b"new_content", content_type="video/mp4"
        )
        data = {
            "title": "New Video",
            "video_file": video_file,
            "date_of_event": "2026-02-11",
        }

        response = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        video = Video.objects.get(title="New Video")
        self.assertEqual(video.owner, self.user_owner)
        # After creation, visibility defaults to DRAFT while encoding starts.
        self.assertEqual(video.status, Video.Status.DRAFT)
        self.assertIn(
            video.encoding_status,
            [
                Video.EncodingStatus.PENDING,
                Video.EncodingStatus.PROCESSING,
                Video.EncodingStatus.ERROR,
            ],
        )
