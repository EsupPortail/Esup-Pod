"""Unit tests for Esup-Pod playlist utilities."""
import hashlib
from django.test import TestCase
from django.contrib.auth.models import User
from pod.video.models import Type, Video
from pod.playlist.models import Playlist, PlaylistContent
from pod.playlist.utils import (
    check_password,
    check_video_in_playlist,
    get_link_to_start_playlist,
    get_next_rank,
    get_number_playlist,
    get_number_video_added_in_playlist,
    get_number_video_in_playlist,
    get_playlist,
    get_playlist_list_for_user,
    get_playlists_for_additional_owner,
    get_promoted_playlist,
    get_public_playlist,
    get_video_list_for_playlist,
    user_add_video_in_playlist,
    user_remove_video_from_playlist,
    remove_playlist,
    get_number_video_added_in_specific_playlist,
    get_favorite_playlist_for_user,
    get_additional_owners,
    get_total_favorites_video,
    get_count_video_added_in_playlist
)


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
        """Test if test_user_add_video_in_playlist works correctly."""
        user_add_video_in_playlist(self.playlist, self.video)
        video_in_playlist = PlaylistContent.objects.filter(
            playlist=self.playlist,
            video=self.video
        ).exists()
        self.assertTrue(
            video_in_playlist,
            "Test if tuple has been correctly inserted."
        )
        user_add_video_in_playlist(self.playlist, self.video)
        self.assertEqual(
            1,
            get_number_video_in_playlist(self.playlist)
        )
        print(" --->  test_user_add_video_in_playlist ok")

    def test_user_remove_video_from_playlist(self) -> None:
        """Test if test_user_remove_video_from_playlist works correctly."""
        user_add_video_in_playlist(self.playlist, self.video)
        user_remove_video_from_playlist(self.playlist, self.video)
        video_in_playlist = PlaylistContent.objects.filter(
            playlist=self.playlist,
            video=self.video
        ).exists()
        self.assertFalse(
            video_in_playlist,
            "Test if tuple has been correctly removed."
        )
        print(" --->  test_user_remove_video_from_playlist ok")

    def test_check_video_in_playlist(self) -> None:
        """Test if test_check_video_in_playlist works correctly."""
        self.assertFalse(
            check_video_in_playlist(self.playlist, self.video)
        )
        user_add_video_in_playlist(self.playlist, self.video)
        self.assertTrue(
            check_video_in_playlist(self.playlist, self.video)
        )
        print(" --->  test_check_video_in_playlist ok")

    def test_get_next_rank(self) -> None:
        """Test if test_get_next_rank works correctly."""
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
        """Test if test_get_number_playlist works correctly."""
        self.assertEqual(
            2,
            get_number_playlist(self.user)
        )  # Favorites + Playlist1
        self.assertEqual(
            1,
            get_number_playlist(self.user2)
        )  # Favorites
        print(" --->  test_get_number_playlist ok")

    def test_get_number_video_in_playlist(self) -> None:
        """Test if test_get_number_video_in_playlist works correctly."""
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
        """Test if test_get_number_video_in_playlist works correctly."""
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
        """Test if remove_playlist works correctly."""
        remove_playlist(self.user, self.playlist)
        self.assertEqual(1, get_number_playlist(self.user))
        print(" --->  test_remove_playlist ok")

    def test_get_public_playlist(self) -> None:
        """Test if test_get_public_playlist works correctly."""
        self.assertEqual(1, len(get_public_playlist()))

        Playlist.objects.create(
            name="playlist_protected",
            description="Ma description",
            visibility="protected",
            autoplay=True,
            owner=self.user2
        )
        Playlist.objects.create(
            name="playlist_private",
            description="Ma description",
            visibility="private",
            autoplay=True,
            owner=self.user
        )

        Playlist.objects.create(
            name="playlist_public_2",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user
        )

        self.assertEqual(2, len(get_public_playlist()))
        print(" --->  test_get_public_playlist ok")

    def test_get_promoted_playlist(self) -> None:
        """Test if test_get_promoted_playlist works correctly."""
        self.assertEqual(1, len(get_public_playlist()))

        Playlist.objects.create(
            name="playlist_protected",
            description="Ma description",
            visibility="protected",
            autoplay=True,
            owner=self.user2
        )
        Playlist.objects.create(
            name="playlist_private",
            description="Ma description",
            visibility="private",
            autoplay=True,
            owner=self.user
        )

        Playlist.objects.create(
            name="playlist_public_2",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user,
            promoted=True
        )

        self.assertEqual(1, len(get_promoted_playlist()))
        print(" --->  test_get_promoted_playlist ok")

    def test_get_playlist_list_for_user(self) -> None:
        """Test if test_get_playlist_list_for_user works correctly."""
        playlist_user = Playlist.objects.create(
            name="playlist_public_2",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user
        )
        playlist_user2 = Playlist.objects.create(
            name="playlist_public_user2",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user2
        )

        self.assertEqual(
            3,
            get_number_playlist(self.user)
        )
        self.assertTrue(
            playlist_user in get_playlist_list_for_user(self.user),
            "The user playlist is in the list."
        )
        self.assertFalse(
            playlist_user2 in get_playlist_list_for_user(self.user),
            "The user2 playlist is not present in the user list."
        )
        print(" --->  test_get_playlist_list_for_user ok")

    def test_get_video_list_for_playlist(self) -> None:
        """Test if test_get_video_list_for_playlist works correctly."""
        user_add_video_in_playlist(self.playlist, self.video)
        user_add_video_in_playlist(self.playlist, self.video2)

        self.assertEqual(
            2,
            len(get_video_list_for_playlist(self.playlist))
        )
        self.assertTrue(
            check_video_in_playlist(self.playlist, self.video),
            "The video is present on playlist list."
        )
        self.assertTrue(
            check_video_in_playlist(self.playlist, self.video2),
            "The video2 is present on playlist list."
        )
        print(" --->  test_get_video_list_for_playlist ok")

    def test_get_playlist(self) -> None:
        """Test if test_get_playlist works correctly."""
        new_playlist = Playlist.objects.create(
            name="new_playlist",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user
        )
        self.assertEqual(
            get_playlist(new_playlist.slug),
            new_playlist
        )
        print(" --->  test_get_playlist ok")

    def test_get_playlists_for_additional_owner(self) -> None:
        """Test if get_playlists_for_additional_owner works correctly."""
        new_playlist = Playlist.objects.create(
            name="new_playlist",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user
        )
        new_playlist.additional_owners.add(self.user2)
        new_playlist.save()
        self.assertTrue(
            new_playlist in get_playlists_for_additional_owner(self.user2),
            "The playlist is present on additional playlist list."
        )
        print(" --->  test_get_playlists_for_additional_owner ok")

    def test_get_link_to_start_playlist(self) -> None:
        """Test if get_link_to_start_playlist works correctly."""
        user_add_video_in_playlist(self.playlist, self.video)
        self.assertEqual(
            get_link_to_start_playlist(self.user, self.playlist),
            f"/video/{self.video.slug}/?playlist={self.playlist.slug}"
        )
        print(" --->  test_get_link_to_start_playlist ok")

    def test_get_number_video_added_in_specific_playlist(self):
        """Test if get_number_video_added_in_specific_playlist works correctly."""
        user_add_video_in_playlist(self.playlist, self.video)
        user_add_video_in_playlist(self.playlist, self.video2)

        new_playlist = Playlist.objects.create(
            name="new_playlist",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user
        )
        user_add_video_in_playlist(new_playlist, self.video3)
        self.assertEqual(2, get_number_video_added_in_specific_playlist(self.playlist))
        self.assertEqual(1, get_number_video_added_in_specific_playlist(new_playlist))

        print(" --->  test_get_number_video_added_in_specific_playlist ok")

    def test_get_favorite_playlist_for_user(self):
        """Test if get_favorite_playlist_for_user works correctly."""
        slug_user_1 = get_favorite_playlist_for_user(self.user)
        user_add_video_in_playlist(slug_user_1, self.video)
        user_add_video_in_playlist(slug_user_1, self.video2)
        user_add_video_in_playlist(slug_user_1, self.video3)
        self.assertEqual(3, get_number_video_added_in_specific_playlist(
            get_favorite_playlist_for_user(self.user)))
        self.assertEqual(0, get_number_video_added_in_specific_playlist(
            get_favorite_playlist_for_user(self.user2)))

        print(" --->  test_get_favorite_playlist_for_user ok")

    def test_get_additional_owners(self):
        """Test if get_additional_owners works correctly."""
        new_playlist = Playlist.objects.create(
            name="new_playlist",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user
        )
        self.assertEqual(0, len(get_additional_owners(new_playlist)))
        new_playlist.additional_owners.add(self.user2)
        self.assertEqual(1, len(get_additional_owners(new_playlist)))
        self.assertIn(self.user2, get_additional_owners(new_playlist))
        print(" --->  test_get_additional_owners ok")

    def test_get_total_favorites_video(self):
        """Test if get_total_favorites_video works correctly."""
        fav_user_1 = get_favorite_playlist_for_user(self.user)
        user_add_video_in_playlist(fav_user_1, self.video)
        user_add_video_in_playlist(fav_user_1, self.video2)
        fav_user_2 = get_favorite_playlist_for_user(self.user2)
        user_add_video_in_playlist(fav_user_2, self.video)

        self.assertEqual(2, get_total_favorites_video(self.video))
        self.assertEqual(1, get_total_favorites_video(self.video2))
        self.assertEqual(0, get_total_favorites_video(self.video3))

        print(" --->  test_get_total_favorites_video ok")

    def test_get_count_video_added_in_playlist(self):
        """Test if get_count_video_added_in_playlist works correctly."""
        fav_user_1 = get_favorite_playlist_for_user(self.user)
        fav_user_2 = get_favorite_playlist_for_user(self.user2)

        user_add_video_in_playlist(fav_user_1, self.video)
        user_add_video_in_playlist(fav_user_2, self.video)
        user_add_video_in_playlist(self.playlist, self.video)
        user_add_video_in_playlist(self.playlist, self.video2)

        self.assertEqual(3, get_count_video_added_in_playlist(self.video))
        self.assertEqual(1, get_count_video_added_in_playlist(self.video2))
        self.assertEqual(0, get_count_video_added_in_playlist(self.video3))

        print(" --->  test_get_count_video_added_in_playlist ok")

    def test_check_password(self):
        """Test if test_check_password works correctly."""
        protected_playlist = Playlist.objects.create(
            name="Playlist1",
            description="Ma description",
            visibility="protected",
            autoplay=True,
            owner=self.user,
            # Encoding not made in create method.
            password=hashlib.sha256("good_password".encode("utf-8")).hexdigest()
        )
        self.assertFalse(
            check_password("wrong_password", protected_playlist)
        )
        self.assertTrue(
            check_password("good_password", protected_playlist)
        )

        print(" --->  test_check_password ok")
