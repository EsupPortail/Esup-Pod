"""Esup-Pod playlist views tests.

*  run with 'python manage.py test pod.playlist.tests.test_views'
"""
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import override_settings, TestCase
from pod.playlist.utils import user_add_video_in_playlist
from pod.video.models import Type, Video

from ...playlist import context_processors
from ..models import Playlist, PlaylistContent

import importlib


class TestPlaylistsPageTestCase(TestCase):
    """Playlists page test case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        self.first_user = User.objects.create(
            username="first.user",
            password="first1234first",
        )
        self.second_user = User.objects.create(
            username="second.user",
            password="second1234second",
        )
        self.first_video = Video.objects.create(
            title="First video",
            owner=self.first_user,
            video="first_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.second_video = Video.objects.create(
            title="Second video",
            owner=self.first_user,
            video="second_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.third_video = Video.objects.create(
            title="Third video",
            owner=self.first_user,
            video="third_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.fourth_video = Video.objects.create(
            title="Fourth video",
            owner=self.second_user,
            video="fourth_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.public_playlist = Playlist.objects.create(
            name="Public playlist",
            visibility="public",
            owner=self.first_user,
        )
        self.protected_playlist = Playlist.objects.create(
            name="Protected playlist",
            password="protected1234protected",
            visibility="protected",
            owner=self.first_user,
        )
        self.private_playlist = Playlist.objects.create(
            name="Private playlist",
            visibility="private",
            owner=self.first_user,
        )
        self.public_playlist_2 = Playlist.objects.create(
            name="Second public playlist",
            visibility="public",
            owner=self.second_user,
        )
        self.playlist_content_1 = PlaylistContent.objects.create(
            playlist=self.public_playlist,
            video=self.first_video,
            rank=1,
        )
        self.playlist_content_2 = PlaylistContent.objects.create(
            playlist=self.public_playlist,
            video=self.second_video,
            rank=2,
        )
        self.playlist_content_3 = PlaylistContent.objects.create(
            playlist=self.public_playlist,
            video=self.third_video,
            rank=3,
        )
        self.playlist_content_4 = PlaylistContent.objects.create(
            playlist=self.public_playlist,
            video=self.fourth_video,
            rank=4,
        )
        self.url = reverse("playlist:list")

    @override_settings(USE_PLAYLIST=True)
    def test_video_counter(self) -> None:
        """Test if the video counter works correctly."""
        importlib.reload(context_processors)
        self.client.force_login(self.first_user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertTrue(
            "4" in response.content.decode(),
            "Test if '4' is visible."
        )
        self.client.logout()
        print(" --->  test_video_counter ok.")

    @override_settings(USE_PLAYLIST=True)
    def test_playlist_counter(self) -> None:
        """Test if the playlist counter works correctly."""
        importlib.reload(context_processors)
        self.client.force_login(self.first_user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertTrue(
            "4" in response.content.decode(),
            "Test if '4' is visible."
        )
        self.client.logout()
        print(" --->  test_playlist_counter ok.")

    @override_settings(USE_PLAYLIST=True)
    def test_card_titles(self) -> None:
        """Test if the playlist card titles are correct."""
        importlib.reload(context_processors)
        self.client.force_login(self.first_user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertTrue(
            "Protected playlist" in response.content.decode(),
            "Test if playlist title is visible."
        )
        self.client.logout()
        print(" --->  test_card_titles ok.")

    @override_settings(USE_PLAYLIST=True)
    def test_private_filter(self) -> None:
        """
        Test if private playlists only are visible when the private filter is active.
        """
        importlib.reload(context_processors)
        self.client.force_login(self.first_user)
        response = self.client.get(f"{self.url}?visibility=private")
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertFalse(
            "bi-lock" in response.content.decode(),
            "Test if protected icon isn't visible."
        )
        self.assertFalse(
            "bi-globe-americas" in response.content.decode(),
            "Test if public icon isn't visible."
        )
        self.client.logout()
        print(" --->  test_private_filter ok.")

    @override_settings(USE_PLAYLIST=True)
    def test_protected_filter(self) -> None:
        """
        Test if protected playlists only are visible when the protected filter is active.
        """
        importlib.reload(context_processors)
        self.client.force_login(self.first_user)
        response = self.client.get(f"{self.url}?visibility=protected")
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertFalse(
            "bi-incognito" in response.content.decode(),
            "Test if private icon isn't visible."
        )
        self.assertFalse(
            "bi-globe-americas" in response.content.decode(),
            "Test if public icon isn't visible."
        )
        self.client.logout()
        print(" --->  test_protected_filter ok.")

    @override_settings(USE_PLAYLIST=True)
    def test_public_filter(self) -> None:
        """
        Test if public playlists only are visible when the public filter is active.
        """
        importlib.reload(context_processors)
        self.client.force_login(self.first_user)
        response = self.client.get(f"{self.url}?visibility=public")
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertFalse(
            "bi-incognito" in response.content.decode(),
            "Test if private icon isn't visible."
        )
        self.assertFalse(
            "bi-lock" in response.content.decode(),
            "Test if protected icon isn't visible."
        )
        self.client.logout()
        print(" --->  test_public_filter ok.")


class TestPlaylistsPageLinkTestCase(TestCase):
    """Playlists page link test case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        self.user = User.objects.create(
            username="first.user",
            password="first1234first",
        )

    @override_settings(USE_PLAYLIST=True)
    def test_icon_visible(self) -> None:
        """Test if the icon is visible."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertTrue(
            "bi-list-ul" in response.content.decode(),
            "Test if playlist icon is visible."
        )
        self.client.logout()
        print(" --->  test_icon_visible ok.")


class TestModalVideoPlaylist(TestCase):
    """Playlists list modal test case."""
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
        self.public_playlist_user = Playlist.objects.create(
            name="public_playlist_user",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user
        )
        self.private_playlist_user = Playlist.objects.create(
            name="private_playlist_user",
            description="Ma description",
            visibility="private_playlist",
            autoplay=True,
            owner=self.user
        )
        self.public_playlist_user2 = Playlist.objects.create(
            name="public_playlist_user2",
            description="Ma description",
            visibility="protected_playlist",
            autoplay=True,
            owner=self.user2
        )
        user_add_video_in_playlist(self.public_playlist_user, self.video)
        self.url = reverse("video:video", kwargs={"slug": self.video.slug})

    @override_settings(USE_PLAYLIST=True)
    def test_list_playlist_in_modal(self) -> None:
        """Test if the list is correctly show."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTrue(
            f'id="{self.public_playlist_user.slug}-btn"' in response.content.decode(),
            "test if the first playlist is present."
        )
        self.assertTrue(
            f'id="{self.private_playlist_user.slug}-btn"' in response.content.decode(),
            "test if the second playlist is present."
        )
        self.assertFalse(
            f'id="{self.public_playlist_user2.slug}-btn"' in response.content.decode(),
            "test if the user2 playlist is not present."
        )
        self.client.logout()
        print(" --->  test_list_playlist_in_modal ok.")

    @override_settings(USE_PLAYLIST=True)
    def test_buttons_actions_playlist_in_modal(self) -> None:
        """Test if the buttons are correctly shown."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        # self.video is on the public playlist of user1
        url_remove_button = reverse(
            "playlist:remove-video",
            kwargs={"slug": self.public_playlist_user.slug, "video_slug": self.video.slug}
        )
        url_add_button = reverse(
            "playlist:add-video",
            kwargs={"slug": self.private_playlist_user.slug,
                    "video_slug": self.video.slug}
        )
        self.assertTrue(
            f'<a href="{url_remove_button}"' in response.content.decode(),
            "test if public playlist show a delete button."
        )
        self.assertTrue(
            f'<a href="{url_add_button}"' in response.content.decode(),
            "test if private playlist show an add button."
        )

        self.client.logout()
        print(" --->  test_buttons_actions_playlist_in_modal ok.")

    @override_settings(USE_PLAYLIST=True)
    def test_buttons_link(self) -> None:
        """Test if the buttons are correctly shown."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        # self.video is on the public playlist of user1
        url_remove_button = reverse(
            "playlist:remove-video",
            kwargs={"slug": self.public_playlist_user.slug, "video_slug": self.video.slug}
        )
        url_add_button = reverse(
            "playlist:add-video",
            kwargs={"slug": self.private_playlist_user.slug,
                    "video_slug": self.video.slug}
        )
        self.assertTrue(
            f'<a href="{url_remove_button}"' in response.content.decode(),
            "test if public playlist show a delete button."
        )
        self.assertTrue(
            f'<a href="{url_add_button}"' in response.content.decode(),
            "test if private playlist show an add button."
        )

        self.client.logout()
        print(" --->  test_buttons_actions_playlist_in_modal ok.")
