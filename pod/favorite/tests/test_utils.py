"""Unit tests for Esup-Pod favorite video utilities."""

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase

from pod.favorite.models import Favorite
from pod.favorite.utils import get_next_rank, user_add_or_remove_favorite_video
from pod.favorite.utils import user_has_favorite_video, get_number_favorites
from pod.favorite.utils import get_all_favorite_videos_for_user
from pod.video.utils import sort_videos_list
from pod.video.models import Type, Video


class FavoriteTestUtils(TestCase):
    """TestCase for Esup-Pod favorite video utilities."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        self.user = User.objects.create(username="pod", password="pod1234pod")
        self.user2 = User.objects.create(username="pod2", password="pod1234pod2")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.video2 = Video.objects.create(
            title="Video2",
            owner=self.user,
            video="test2.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.video3 = Video.objects.create(
            title="Video3",
            owner=self.user2,
            video="test3.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

    def test_next_rank(self) -> None:
        """Test if get_next_rank works correctly"""
        Favorite.objects.create(
            owner=self.user,
            video=self.video,
            rank=1,
        )
        self.assertEqual(
            2,
            get_next_rank(self.user),
            "Test if user with favorite can generate the next rank",
        )
        self.assertEqual(
            1,
            get_next_rank(self.user2),
            "Test if user without favorite can generate the next rank",
        )
        print(" --->  test_next_rank ok")

    def test_user_add_or_remove_favorite_video(self) -> None:
        """Test if test_user_add_or_remove_favorite_video works correctly"""
        user_add_or_remove_favorite_video(self.user, self.video)
        favorite_tuple_exists = Favorite.objects.filter(
            owner=self.user, video=self.video
        ).exists()
        self.assertTrue(
            favorite_tuple_exists,
            "Test if tuple has been correctly inserted",
        )
        user_add_or_remove_favorite_video(self.user, self.video)
        favorite_tuple_not_exists = Favorite.objects.filter(
            owner=self.user, video=self.video
        ).exists()
        self.assertFalse(
            favorite_tuple_not_exists,
            "Test if tuple has been correctly deleted",
        )
        print(" --->  test_user_add_or_remove_favorite_video ok")

    def test_user_has_favorite_video(self) -> None:
        """Test if test_user_has_favorite_video works correctly"""
        Favorite.objects.create(
            owner=self.user,
            video=self.video,
            rank=1,
        )
        self.assertTrue(
            user_has_favorite_video(self.user, self.video),
            "Test if user has a favorite video",
        )
        self.assertFalse(
            user_has_favorite_video(self.user2, self.video),
            "Test if user hasn't a favorite video",
        )
        print(" --->  test_user_has_favorite_video ok")

    def test_get_number_favorites(self) -> None:
        """Test if test_get_number_favorites works correctly"""
        self.assertEqual(
            get_number_favorites(self.video),
            0,
            "Test if there's no favorites in the video",
        )
        Favorite.objects.create(
            owner=self.user,
            video=self.video,
            rank=1,
        )
        Favorite.objects.create(
            owner=self.user2,
            video=self.video,
            rank=1,
        )
        self.assertEqual(
            get_number_favorites(self.video),
            2,
            "Test if there is 2 favorites in the video",
        )

        print(" --->  test_get_number_favorites ok")

    def test_get_all_favorite_videos_for_user(self) -> None:
        """Test if get_all_favorite_videos_for_user works correctly."""
        Favorite.objects.create(
            owner=self.user,
            video=self.video,
            rank=1,
        )
        video_list = get_all_favorite_videos_for_user(self.user)
        self.assertEqual(video_list.count(), 1)
        self.assertEqual(video_list.first(), self.video)
        print(" --->  get_all_favorite_videos_for_user ok")

    def test_sort_videos_list_1(self) -> None:
        """Test if sort_videos_list works correctly."""
        request = HttpRequest()
        Favorite.objects.create(
            owner=self.user,
            video=self.video,
            rank=1,
        )
        Favorite.objects.create(
            owner=self.user,
            video=self.video2,
            rank=2,
        )
        Favorite.objects.create(
            owner=self.user,
            video=self.video3,
            rank=3,
        )

        sorted_videos = [self.video3, self.video2, self.video]
        test_sorted_videos = sort_videos_list(
            request, get_all_favorite_videos_for_user(self.user),
            request.GET.get("sort", "rank")
        )
        self.assertEqual(list(test_sorted_videos), sorted_videos)

        request.GET["sort"] = "rank"
        request.GET["sort_direction"] = "desc"
        sorted_videos = [self.video, self.video2, self.video3]
        test_sorted_videos = sort_videos_list(
            request, get_all_favorite_videos_for_user(self.user),
            request.GET.get("sort", "rank")
        )
        self.assertEqual(list(test_sorted_videos), sorted_videos)

        print(" --->  sort_videos_list ok")
