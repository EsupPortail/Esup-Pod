"""Unit tests for Esup-Pod playlist utilities."""
from django.test import TestCase
from django.contrib.auth.models import User
from pod.playlist.models import Playlist, PlaylistContent
from pod.playlist.utils import check_video_in_playlist, get_next_rank, get_number_playlist
from pod.playlist.utils import get_number_video_added_in_playlist
from pod.playlist.utils import get_number_video_in_playlist, user_add_video_in_playlist
from pod.playlist.utils import user_has_playlist, user_remove_video_from_playlist
from pod.playlist.utils import remove_playlist
from pod.video.models import Type, Video


class PlaylistTestUtils(TestCase):
    """TestCase for Esup-Pod playlist utilities."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
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
        self.playlist = Playlist.objects.create(
            name="Playlist1",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user
        )

    def test_user_add_video_in_playlist(self) -> None:
        """Test if test_user_add_video_in_playlist works correctly"""
        status_msg = user_add_video_in_playlist(self.playlist, self.video)
        video_in_playlist = PlaylistContent.objects.filter(
            playlist=self.playlist,
            video=self.video
        ).exists()
        self.assertTrue(
            video_in_playlist,
            "Test if tuple has been correctly inserted"
        )
        self.assertEqual(
            status_msg,
            f"Video successfully added to the playlist : {self.playlist.name}"
        )

        status_msg = user_add_video_in_playlist(self.playlist, self.video)
        self.assertTrue(
            user_add_video_in_playlist(self.playlist, self.video),
            "Test if a tuple is already in database"
        )
        self.assertEqual(
            status_msg,
            f"This video is already in the playlist : {self.playlist.name}"
        )
        print(" --->  test_user_add_video_in_playlist ok")

    def test_user_remove_video_from_playlist(self) -> None:
        """Test if test_user_remove_video_from_playlist works correctly"""
        user_add_video_in_playlist(self.playlist, self.video)
        status_msg = user_remove_video_from_playlist(self.playlist, self.video)
        video_in_playlist = PlaylistContent.objects.filter(
            playlist=self.playlist,
            video=self.video
        ).exists()
        self.assertFalse(
            video_in_playlist,
            "Test if tuple has been correctly removed"
        )
        self.assertEqual(
            status_msg,
            f"Video successfully removed from the playlist : {self.playlist.name}"
        )

        status_msg = user_remove_video_from_playlist(self.playlist, self.video)
        self.assertEqual(
            status_msg,
            f"This video is not in the playlist : {self.playlist.name}"
        )
        print(" --->  test_user_remove_video_from_playlist ok")

    def test_user_has_playlist(self) -> None:
        """Test if test_user_has_playlist works correctly"""
        self.assertTrue(user_has_playlist(self.user))
        self.assertFalse(user_has_playlist(self.user2))
        print(" --->  test_user_has_playlist ok")

    def test_check_video_in_playlist(self) -> None:
        """Test if test_check_video_in_playlist works correctly"""
        self.assertFalse(
            check_video_in_playlist(self.playlist, self.video)
        )
        user_add_video_in_playlist(self.playlist, self.video)
        self.assertTrue(
            check_video_in_playlist(self.playlist, self.video)
        )
        print(" --->  test_check_video_in_playlist ok")

    def test_get_next_rank(self) -> None:
        """Test if test_get_next_rank works correctly"""
        self.assertEqual(
            1,
            get_next_rank(self.playlist)
        )
        user_add_video_in_playlist(self.playlist, self.video)
        user_add_video_in_playlist(self.playlist, self.video2)
        self.assertEqual(
            3,
            get_next_rank(self.playlist)
        )
        print(" --->  test_get_next_rank ok")

    def test_get_number_playlist(self) -> None:
        """Test if test_get_number_playlist works correctly"""
        self.assertEqual(
            1,
            get_number_playlist(self.user)
        )
        self.assertEqual(
            0,
            get_number_playlist(self.user2)
        )
        print(" --->  test_get_number_playlist ok")

    def test_get_number_video_in_playlist(self) -> None:
        """Test if test_get_number_video_in_playlist works correctly"""
        self.assertEqual(
            0,
            get_number_video_in_playlist(self.playlist)
        )
        user_add_video_in_playlist(self.playlist, self.video)
        self.assertEqual(
            1,
            get_number_video_in_playlist(self.playlist)
        )
        print(" --->  test_get_number_video_in_playlist ok")

    def test_get_number_video_added_in_playlist(self) -> None:
        """Test if test_get_number_video_in_playlist works correctly"""
        self.assertEqual(
            0,
            get_number_video_added_in_playlist(self.video)
        )
        playlist2 = Playlist.objects.create(
            name="Playlist2",
            description="Ma description",
            visibility="private",
            autoplay=True,
            owner=self.user2
        )
        playlist3 = Playlist.objects.create(
            name="Playlist3",
            description="Ma description",
            visibility="private",
            autoplay=True,
            owner=self.user
        )
        user_add_video_in_playlist(self.playlist, self.video)
        user_add_video_in_playlist(playlist2, self.video)
        user_add_video_in_playlist(playlist3, self.video)
        self.assertEqual(
            3,
            get_number_video_added_in_playlist(self.video)
        )
        print(" --->  test_get_number_video_added_in_playlist ok")

    def test_remove_playlist(self) -> None:
        """Test if remove_playlist works correctly"""
        remove_playlist(self.user, self.playlist)
        self.assertEqual(0, get_number_playlist(self.user))
