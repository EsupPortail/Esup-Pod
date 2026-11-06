"""
Esup-Pod - Video application views tests.
"""

from unittest.mock import patch
import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.video.models import Video, Subtitle, Type, Discipline
from src.apps.authentication.models import AccessGroup

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

# ggignore-start
# gitguardian:ignore
PWD = "password"
# ggignore-end


@override_settings(
    MEDIA_ROOT=TEMP_MEDIA_ROOT,
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ],
)
class VideoViewSetTests(APITestCase):
    """
    Tests for the VideoViewSet.
    """

    @classmethod
    def tearDownClass(cls):
        """Cleans up temporary media directory after tests."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def _get_results(self, response):
        """Helper to get results from paginated or non-paginated response."""
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]
        return response.data

    def setUp(self):
        """Sets up test users and various video types for API verification."""
        self.user = User.objects.create_user(username="testuser", password=PWD)  # nosec
        self.other_user = User.objects.create_user(
            username="other", password=PWD
        )  # nosec
        self.superuser = User.objects.create_superuser(
            username="admin", password=PWD
        )  # nosec

        self.video_content = SimpleUploadedFile(
            "test.mp4", b"file_content", content_type="video/mp4"
        )
        self.type_tut = Type.objects.create(title="Tutorial", slug="tutorial")
        self.discipline_math = Discipline.objects.create(title="Math", slug="math")

        self.video = Video.objects.create(
            title="My Video",
            owner=self.user,
            video_file=self.video_content,
            status=Video.Status.PUBLISHED,
            type=self.type_tut,
        )
        self.video.disciplines.add(self.discipline_math)
        self.video.tags = "django, python"
        self.video.save()

        self.group_vip = AccessGroup.objects.create(display_name="VIP", code_name="vip")
        self.restricted_video = Video.objects.create(
            title="Restricted Video",
            owner=self.user,
            video_file=self.video_content,
            status=Video.Status.RESTRICTED,
            is_auth_required=True,
            password=PWD,
        )

    def test_get_queryset_unauthenticated(self):
        """Verifies that unauthenticated users only see published videos."""
        url = reverse("video-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_list = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(response_list), 1)
        self.assertEqual(response_list[0]["title"], "My Video")

    def test_get_queryset_superuser(self):
        """Verifies that superusers see all videos regardless of status."""
        self.client.force_authenticate(user=self.superuser)
        url = reverse("video-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_list = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(response_list), 2)

    @patch("src.apps.video.views.VideoViewSet.encoding_settings")
    def test_perform_create_quota_exceeded(self, mock_settings):
        """Verifies that exceeding the user quota returns a 400 error."""
        mock_settings.user_quota_size_gb = 0

        self.client.force_authenticate(user=self.user)
        url = reverse("video-list")
        data = {
            "title": "New Video",
            "video_file": SimpleUploadedFile(
                "test2.mp4", b"large content", content_type="video/mp4"
            ),
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video_file", response.data)

    def test_filter_by_type(self):
        """Verifies that videos can be filtered by type slug."""
        url = f"{reverse('video-list')}?type__slug=tutorial"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.video.id)

    def test_filter_by_discipline(self):
        """Verifies that videos can be filtered by discipline ID."""
        url = f"{reverse('video-list')}?discipline={self.discipline_math.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        self.assertEqual(len(results), 1)

    def test_filter_by_tags_slug(self):
        """Verifies that videos can be filtered by tag slug."""
        url = f"{reverse('video-list')}?tags__slug=django"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        self.assertEqual(len(results), 1)

    def test_filter_by_tags_name(self):
        """Verifies that videos can be filtered by tag name."""
        url = f"{reverse('video-list')}?tags__name=python"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        self.assertEqual(len(results), 1)

    def test_filter_by_multiple_tags(self):
        """Verifies that videos can be filtered by multiple tag names (acts as an OR/IN behavior, matching videos containing any of the provided tags)."""
        url = f"{reverse('video-list')}?tags__name=python&tags__name=django"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        self.assertEqual(len(results), 1)

    def test_filter_by_status(self):
        """Verifies that videos can be filtered by status."""
        self.client.force_authenticate(user=self.superuser)
        url = f"{reverse('video-list')}?status=RE"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Restricted Video")

    def test_filter_by_owner_username(self):
        """Verifies that videos can be filtered by owner username."""
        self.client.force_authenticate(user=self.superuser)
        url = f"{reverse('video-list')}?owner__username=testuser"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        self.assertEqual(len(results), 2)  # My Video and Restricted Video

    def test_search_includes_tags(self):
        """Verifies that search works on tag names."""
        url = f"{reverse('video-list')}?search=django"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], self.video.id)

    def test_access_restricted_group(self):
        """Verifies that user in restricted group can access video."""
        vip_user = User.objects.create_user(username="vip", password="password")
        owner = vip_user.owner
        owner.accessgroups.add(self.group_vip)

        vid_group = Video.objects.create(
            title="VIP Video",
            owner=self.superuser,
            status=Video.Status.PUBLISHED,
            video_file=self.video_content,
        )
        vid_group.restricted_groups.add(self.group_vip)

        self.client.force_authenticate(user=vip_user)
        url = reverse("video-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        titles = [v["title"] for v in results]
        self.assertIn("VIP Video", titles)

    def test_stream_video_owner(self):
        """Verifies that the owner can successfully stream their video using an ephemeral token."""
        self.client.force_authenticate(user=self.user)

        token_url = reverse("video-create-stream-token", kwargs={"slug": self.video.slug})
        token_response = self.client.post(token_url)
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        token = token_response.data["stream_token"]

        url = f"{reverse('video-stream', kwargs={'slug': self.video.slug})}?token={token}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "video/mp4")

    def test_stream_video_unauthenticated_restricted(self):
        """Verifies that unauthenticated users cannot obtain a stream token for restricted videos."""
        token_url = reverse(
            "video-create-stream-token", kwargs={"slug": self.restricted_video.slug}
        )
        response = self.client.post(token_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_view(self):
        """Verifies that the register-view endpoint correctly increments view counts."""
        url = reverse("video-register-view", kwargs={"slug": self.video.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_count"], 1)

        self.video.refresh_from_db()
        self.assertEqual(self.video.view_count, 1)

    def test_unlock_restricted_video_success(self):
        """Verifies that a correct password unlocks a restricted video for a visitor."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("video-unlock", kwargs={"slug": self.restricted_video.slug})
        data = {"password": PWD}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("video_url", response.data)

    def test_unlock_restricted_video_wrong_password(self):
        """Verifies that a wrong password fails to unlock a restricted video."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("video-unlock", kwargs={"slug": self.restricted_video.slug})
        data = {"password": "wrongpassword"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_video_tags(self):
        """Verifies that tags can be updated via the API."""
        self.client.force_authenticate(user=self.user)
        url = reverse("video-detail", kwargs={"slug": self.video.slug})
        data = {"tags": ["newtag1", "newtag2"]}
        response = self.client.patch(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        tags = [t.name for t in self.video.tags.all()]
        self.assertIn("newtag1", tags)
        self.assertIn("newtag2", tags)
        self.assertNotIn("django", tags)
        data = {"tags": "newtag3, newtag4"}
        response = self.client.patch(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        tags = [t.name for t in self.video.tags.all()]
        self.assertIn("newtag3", tags)
        self.assertIn("newtag4", tags)
        self.assertNotIn("newtag1", tags)

    def test_clear_video_password(self):
        """Verifies that setting the password to an empty string clears the password lock."""
        self.client.force_authenticate(user=self.user)
        url = reverse("video-detail", kwargs={"slug": self.restricted_video.slug})
        response = self.client.get(url)
        self.assertTrue(response.data["has_password"])
        data = {"password": ""}
        response = self.client.patch(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["has_password"])
        self.restricted_video.refresh_from_db()
        self.assertFalse(bool(self.restricted_video.password))

    def test_owner_first_last_name_in_payload(self):
        """Verifies that owner_first_name and owner_last_name are present in video payload."""
        self.user.first_name = "Jean"
        self.user.last_name = "Dupont"
        self.user.save()

        url = reverse("video-detail", kwargs={"slug": self.video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["owner_first_name"], "Jean")
        self.assertEqual(response.data["owner_last_name"], "Dupont")

    def test_thumbnail_serialization_fallback(self):
        """Verifies that the serialized thumbnail field falls back to thumbnail_url when empty."""
        self.client.force_authenticate(user=self.user)

        url = reverse("video-detail", kwargs={"slug": self.video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("default_thumbnail", response.data["thumbnail_url"])
        self.assertEqual(response.data["thumbnail"], response.data["thumbnail_url"])

        # Add overview file
        overview_file = SimpleUploadedFile(
            "overview.png", b"image_content", content_type="image/png"
        )
        self.video.overview = overview_file
        self.video.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("thumbnails", response.data["thumbnail_url"])
        self.assertNotIn("default_thumbnail", response.data["thumbnail_url"])
        self.assertEqual(response.data["thumbnail"], response.data["thumbnail_url"])


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SubtitleViewSetTests(APITestCase):
    """
    Tests for the SubtitleViewSet.
    """

    @classmethod
    def tearDownClass(cls):
        """Cleans up temporary media directory after tests."""
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        """Sets up a video and a subtitle for serialization testing."""
        self.user = User.objects.create_user(username="testuser", password=PWD)  # nosec
        self.other_user = User.objects.create_user(
            username="other", password=PWD
        )  # nosec

        self.video = Video.objects.create(
            title="My Video",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )

        self.subtitle_content = SimpleUploadedFile(
            "sub.vtt",
            b"WEBVTT\n\n00:00.000 --> 00:05.000\nHello",
            content_type="text/vtt",
        )
        self.subtitle = Subtitle.objects.create(
            video=self.video, language="en", file=self.subtitle_content
        )

    def test_get_queryset_filter_by_video(self):
        """Verifies that subtitles can be filtered by video ID in the API."""
        url = f"{reverse('subtitle-list')}?video_id={self.video.id}"
        response = self.client.get(url)
        response_list = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(response_list), 1)

    def test_create_subtitle_owner(self):
        """Verifies that the video owner can upload new subtitles."""
        self.client.force_authenticate(user=self.user)
        url = reverse("subtitle-list")
        data = {
            "video": self.video.id,
            "language": "fr",
            "file": SimpleUploadedFile(
                "fr.vtt", b"WEBVTT\n\nBonjour", content_type="text/vtt"
            ),
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_subtitle_not_owner(self):
        """Verifies that a non-owner cannot upload subtitles to someone else's video."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("subtitle-list")
        data = {
            "video": self.video.id,
            "language": "es",
            "file": SimpleUploadedFile(
                "es.vtt", b"WEBVTT\n\nHola", content_type="text/vtt"
            ),
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CommentBasicViewTests(APITestCase):
    """Tests for the CommentViewSet."""

    def setUp(self):
        """Sets up user and video for comment API testing."""
        self.user = User.objects.create_user(
            username="testuser_comments", password="password"
        )
        self.video = Video.objects.create(
            title="My Video", owner=self.user, status=Video.Status.PUBLISHED
        )
        self.client.force_authenticate(user=self.user)

    def test_add_and_list_comment(self):
        """Verifies that a comment can be added and listed successfully."""
        # 1. Add comment
        url_add = reverse("comment-add-root", kwargs={"video_slug": self.video.slug})
        response = self.client.post(url_add, {"content": "Hello API test"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn("id", response.data)
        self.assertIn("author_name", response.data)
        self.assertIn("author_picture", response.data)
        self.assertIn("content", response.data)
        self.assertIn("added", response.data)
        self.assertEqual(response.data["content"], "Hello API test")

        # 2. List comments
        url_list = reverse("comment-list", kwargs={"video_slug": self.video.slug})
        response_list = self.client.get(url_list)
        self.assertEqual(len(response_list.data), 1)

        comment_data = response_list.data[0]
        self.assertEqual(comment_data["content"], "Hello API test")
        self.assertIn("author_name", comment_data)
        self.assertIn("author_picture", comment_data)


class TagViewSetTests(APITestCase):
    """
    Tests for the TagViewSet.
    """

    def _get_results(self, response):
        """Helper to get results from paginated or non-paginated response."""
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]
        return response.data

    def setUp(self):
        """Sets up tags via a video."""
        self.user = User.objects.create_user(username="taguser", password=PWD)
        self.video = Video.objects.create(
            title="Tagged Video",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )
        self.video.tags = "mytag1, mytag2"
        self.video.save()

    def test_list_tags(self):
        """Verifies that tags are listed correctly."""
        url = reverse("tag-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = self._get_results(response)
        self.assertEqual(len(results), 2)
        tag_names = [t["name"] for t in results]
        self.assertIn("mytag1", tag_names)
        self.assertIn("mytag2", tag_names)

    def test_search_tags(self):
        """Verifies searching tags."""
        url = f"{reverse('tag-list')}?search=mytag1"
        response = self.client.get(url)
        results = self._get_results(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "mytag1")
