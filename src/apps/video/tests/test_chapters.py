"""
Esup-Pod - Chapter API tests.
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from src.apps.video.models import Chapter, Video
from src.apps.video.views.ChapterViewSet import ChapterViewSet

User = get_user_model()

# ggignore-start
# gitguardian:ignore
PWD = "password"
# ggignore-end


class ChapterAPITests(APITestCase):
    """Test suite for the Chapter API endpoints."""

    def setUp(self):
        """Create users, a published video, a draft video and one chapter."""
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(username="owner", password=PWD)  # nosec
        self.other_user = User.objects.create_user(
            username="other", password=PWD
        )  # nosec
        self.superuser = User.objects.create_superuser(
            username="admin", password=PWD
        )  # nosec
        self.video = Video.objects.create(
            title="Published video",
            owner=self.owner,
            status=Video.Status.PUBLISHED,
            duration=300,
        )
        self.draft_video = Video.objects.create(
            title="Draft video",
            owner=self.owner,
            status=Video.Status.DRAFT,
            duration=300,
        )
        self.chapter = Chapter.objects.create(
            video=self.video, title="Introduction", time_start=0
        )
        self.draft_chapter = Chapter.objects.create(
            video=self.draft_video, title="Secret", time_start=10
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _call(self, method, action, user=None, data=None, query="", **kwargs):
        """Call the viewset action and return the response."""
        view = ChapterViewSet.as_view({method: action})
        request = getattr(self.factory, method)(f"/{query}", data, format="json")
        if user:
            force_authenticate(request, user=user)
        return view(request, **kwargs)

    @staticmethod
    def _items(response):
        """Return the list of items, paginated or not."""
        if isinstance(response.data, dict) and "results" in response.data:
            return response.data["results"]
        return response.data

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def test_list_by_video_is_not_paginated(self):
        """Anyone can list the chapters of a published video as a plain list."""
        response = self._call("get", "list", query=f"?video_id={self.video.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual([c["title"] for c in response.data], ["Introduction"])

    def test_list_by_video_slug(self):
        """Chapters can be filtered by video slug."""
        response = self._call("get", "list", query=f"?video_slug={self.video.slug}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self._items(response)), 1)

    def test_list_invalid_video_id_returns_empty(self):
        """A non numeric video_id does not crash and returns nothing."""
        response = self._call("get", "list", query="?video_id=abc")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(self._items(response)), 0)

    def test_draft_video_chapters_hidden_from_anonymous(self):
        """Chapters of a draft video are not listed for anonymous users."""
        response = self._call("get", "list")
        titles = [c["title"] for c in self._items(response)]
        self.assertIn("Introduction", titles)
        self.assertNotIn("Secret", titles)

    def test_draft_video_chapters_hidden_from_other_user(self):
        """Chapters of a draft video are not listed for non owners."""
        response = self._call("get", "list", user=self.other_user)
        titles = [c["title"] for c in self._items(response)]
        self.assertNotIn("Secret", titles)

    def test_draft_video_chapters_visible_to_owner(self):
        """The owner sees the chapters of their draft video."""
        response = self._call("get", "list", user=self.owner)
        titles = [c["title"] for c in self._items(response)]
        self.assertIn("Secret", titles)

    def test_retrieve_draft_chapter_not_found_for_anonymous(self):
        """A chapter of a draft video cannot be retrieved by anonymous users."""
        response = self._call("get", "retrieve", pk=self.draft_chapter.pk)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def test_create_chapter_owner(self):
        """The video owner can add a chapter."""
        data = {"video": self.video.id, "title": "Part 2", "time_start": 60}
        response = self._call("post", "create", user=self.owner, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chapter.objects.filter(video=self.video).count(), 2)

    def test_create_chapter_superuser(self):
        """A superuser can add a chapter to any video."""
        data = {"video": self.video.id, "title": "Part 2", "time_start": 60}
        response = self._call("post", "create", user=self.superuser, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_chapter_other_user_forbidden(self):
        """A user who cannot edit the video cannot add a chapter."""
        data = {"video": self.video.id, "title": "Part 2", "time_start": 60}
        response = self._call("post", "create", user=self.other_user, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Chapter.objects.filter(video=self.video).count(), 1)

    def test_create_chapter_anonymous_rejected(self):
        """Anonymous users cannot add chapters."""
        data = {"video": self.video.id, "title": "Part 2", "time_start": 60}
        response = self._call("post", "create", data=data)
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_create_chapter_start_after_duration(self):
        """time_start must be lower than the video duration."""
        data = {"video": self.video.id, "title": "Too late", "time_start": 300}
        response = self._call("post", "create", user=self.owner, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("time_start", response.data)

    def test_create_chapter_unknown_duration(self):
        """A video without known duration cannot receive chapters yet."""
        video = Video.objects.create(
            title="Encoding", owner=self.owner, status=Video.Status.PUBLISHED
        )
        data = {"video": video.id, "title": "Intro", "time_start": 0}
        response = self._call("post", "create", user=self.owner, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_chapter_same_start_time(self):
        """Two chapters of a video cannot start at the same time."""
        data = {"video": self.video.id, "title": "Another", "time_start": 0}
        response = self._call("post", "create", user=self.owner, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("time_start", response.data)

    def test_create_chapter_title_too_long(self):
        """The title is limited to 100 characters."""
        data = {"video": self.video.id, "title": "x" * 101, "time_start": 30}
        response = self._call("post", "create", user=self.owner, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def test_update_chapter_owner(self):
        """The owner can rename a chapter."""
        response = self._call(
            "patch",
            "partial_update",
            user=self.owner,
            data={"title": "Welcome"},
            pk=self.chapter.pk,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.chapter.refresh_from_db()
        self.assertEqual(self.chapter.title, "Welcome")

    def test_update_chapter_keeps_own_start_time(self):
        """Saving a chapter with its own start time is not seen as a clash."""
        response = self._call(
            "patch",
            "partial_update",
            user=self.owner,
            data={"time_start": 0, "title": "Welcome"},
            pk=self.chapter.pk,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_chapter_other_user_forbidden(self):
        """A user who cannot edit the video cannot modify its chapters."""
        response = self._call(
            "patch",
            "partial_update",
            user=self.other_user,
            data={"title": "Hacked"},
            pk=self.chapter.pk,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.chapter.refresh_from_db()
        self.assertEqual(self.chapter.title, "Introduction")

    def test_update_chapter_cannot_change_video(self):
        """The video of an existing chapter is not modifiable."""
        other_video = Video.objects.create(
            title="Other", owner=self.owner, status=Video.Status.PUBLISHED, duration=100
        )
        response = self._call(
            "patch",
            "partial_update",
            user=self.owner,
            data={"video": other_video.id, "title": "Moved"},
            pk=self.chapter.pk,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.chapter.refresh_from_db()
        self.assertEqual(self.chapter.video_id, self.video.id)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def test_delete_chapter_owner(self):
        """The owner can delete a chapter."""
        response = self._call("delete", "destroy", user=self.owner, pk=self.chapter.pk)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Chapter.objects.filter(pk=self.chapter.pk).exists())

    def test_delete_chapter_other_user_forbidden(self):
        """A user who cannot edit the video cannot delete its chapters."""
        response = self._call(
            "delete", "destroy", user=self.other_user, pk=self.chapter.pk
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Chapter.objects.filter(pk=self.chapter.pk).exists())
