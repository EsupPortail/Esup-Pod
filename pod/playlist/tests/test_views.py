"""Esup-Pod playlist views tests.

*  run with 'python manage.py test pod.playlist.tests.test_views'
"""
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.test import override_settings, TestCase

from bs4 import BeautifulSoup

from pod.video.models import Type, Video

from ..apps import FAVORITE_PLAYLIST_NAME
from ...playlist import context_processors
from ..models import Playlist, PlaylistContent
from ..utils import (
    get_favorite_playlist_for_user,
    get_link_to_start_playlist,
    user_add_video_in_playlist,
)

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
            promoted=True,
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
    def test_playlist_card_counter(self) -> None:
        """Test if the number of cards in playlist list page is correct."""
        importlib.reload(context_processors)
        self.client.force_login(self.first_user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertTrue(
            "data-number-playlists=5" in response.content.decode(),
            "Test if there's 5 playlists visible in the playlist page.",
        )
        self.client.logout()
        print(" --->  test_playlist_card_counter ok")

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
            "Test if playlist title is visible.",
        )
        self.client.logout()
        print(" --->  test_card_titles ok")

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
            "Test if protected icon isn't visible.",
        )
        self.assertFalse(
            "bi-globe-americas" in response.content.decode(),
            "Test if public icon isn't visible.",
        )
        self.assertTrue(
            "data-number-playlists=2" in response.content.decode(),
            "Test if there's 2 private playlists in the playlist page.",
        )
        self.client.logout()
        print(" --->  test_private_filter ok")

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
            "Test if private icon isn't visible.",
        )
        self.assertFalse(
            "bi-globe-americas" in response.content.decode(),
            "Test if public icon isn't visible.",
        )
        self.assertTrue(
            "data-number-playlists=1" in response.content.decode(),
            "Test if there's 1 protected playlist in the playlist page.",
        )
        self.client.logout()
        print(" --->  test_protected_filter ok")

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
            "Test if private icon isn't visible.",
        )
        self.assertFalse(
            "bi-lock" in response.content.decode(), "Test if protected icon isn't visible"
        )
        self.assertTrue(
            "data-number-playlists=1" in response.content.decode(),
            "Test if there's 1 playlist visible in the playlist page.",
        )
        self.client.logout()
        print(" --->  test_public_filter ok")

    @override_settings(USE_PLAYLIST=True)
    def test_allpublic_filter(self) -> None:
        """
        Test if all public playlists are visible when the allpublic filter is active.
        """
        importlib.reload(context_processors)
        self.client.force_login(self.first_user)
        response = self.client.get(f"{self.url}?visibility=allpublic")
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertFalse(
            "bi-incognito" in response.content.decode(),
            "Test if private icon isn't visible.",
        )
        self.assertFalse(
            "bi-lock" in response.content.decode(), "Test if protected icon isn't visible"
        )
        self.assertTrue(
            "data-number-playlists=2" in response.content.decode(),
            "Test if there's 2 playlists visible in the playlist page.",
        )
        self.client.logout()
        print(" --->  test_allpublic_filter ok")

    @override_settings(USE_PLAYLIST=True)
    def test_promoted_filter(self) -> None:
        """
        Test if all promoted playlist are visible when the promoted filter is active.
        """
        importlib.reload(context_processors)
        self.client.force_login(self.first_user)
        response = self.client.get(f"{self.url}?visibility=promoted")
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertFalse(
            "bi-incognito" in response.content.decode(),
            "Test if private icon isn't visible.",
        )
        self.assertFalse(
            "bi-lock" in response.content.decode(), "Test if protected icon isn't visible"
        )
        self.assertTrue(
            "promoted-icon" in response.content.decode(),
            "Test if promoted icon is visible.",
        )
        self.assertTrue(
            "data-number-playlists=1" in response.content.decode(),
            "Test if there's 1 promoted playlist in the playlist page.",
        )
        self.client.logout()
        print(" --->  test_promoted_filter ok")


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
            "bi-list-ul" in response.content.decode(), "Test if playlist icon is visible."
        )
        self.client.logout()
        print(" --->  test_icon_visible ok")


class TestModalVideoPlaylist(TestCase):
    """Playlist list modal test case."""

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
            owner=self.user,
        )
        self.private_playlist_user = Playlist.objects.create(
            name="private_playlist_user",
            description="Ma description",
            visibility="private_playlist",
            autoplay=True,
            owner=self.user,
        )
        self.public_playlist_user2 = Playlist.objects.create(
            name="public_playlist_user2",
            description="Ma description",
            visibility="protected_playlist",
            autoplay=True,
            owner=self.user2,
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
            "Test if the first playlist is present.",
        )
        self.assertTrue(
            f'id="{self.private_playlist_user.slug}-btn"' in response.content.decode(),
            "Test if the second playlist is present.",
        )
        self.assertFalse(
            f'id="{self.public_playlist_user2.slug}-btn"' in response.content.decode(),
            "Test if the user2 playlist is not present.",
        )
        self.client.logout()
        print(" --->  test_list_playlist_in_modal ok")

    @override_settings(USE_PLAYLIST=True)
    def test_buttons_actions_playlist_in_modal(self) -> None:
        """Test if the buttons are correctly shown."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        # self.video is on the public playlist of user1
        url_remove_button = reverse(
            "playlist:remove-video",
            kwargs={
                "slug": self.public_playlist_user.slug,
                "video_slug": self.video.slug,
            },
        )
        url_add_button = reverse(
            "playlist:add-video",
            kwargs={
                "slug": self.private_playlist_user.slug,
                "video_slug": self.video.slug,
            },
        )
        self.assertTrue(
            f'<a href="{url_remove_button}"' in response.content.decode(),
            "Test if public playlist show a delete button.",
        )
        self.assertTrue(
            f'<a href="{url_add_button}"' in response.content.decode(),
            "Test if private playlist show an add button.",
        )

        self.client.logout()
        print(" --->  test_buttons_actions_playlist_in_modal ok")

    @override_settings(USE_PLAYLIST=True)
    def test_buttons_link(self) -> None:
        """Test if the buttons are correctly shown."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        # self.video is on the public playlist of user1
        url_remove_button = reverse(
            "playlist:remove-video",
            kwargs={
                "slug": self.public_playlist_user.slug,
                "video_slug": self.video.slug,
            },
        )
        url_add_button = reverse(
            "playlist:add-video",
            kwargs={
                "slug": self.private_playlist_user.slug,
                "video_slug": self.video.slug,
            },
        )
        self.assertTrue(
            f'<a href="{url_remove_button}"' in response.content.decode(),
            "Test if public playlist show a delete button",
        )
        self.assertTrue(
            f'<a href="{url_add_button}"' in response.content.decode(),
            "Test if private playlist show an add button",
        )

        self.client.logout()
        print(" --->  test_buttons_actions_playlist_in_modal ok")


class TestAddOrRemoveFormTestCase(TestCase):
    """Add or remove form test case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        self.user = User.objects.create(
            username="simple.user",
            password="user1234user",
        )
        self.simple_playlist = Playlist.objects.create(
            name="My simple playlist",
            visibility="public",
            owner=self.user,
        )
        self.addUrl = reverse("playlist:add")
        self.editUrl = reverse(
            "playlist:edit", kwargs={"slug": self.simple_playlist.slug}
        )

    @override_settings(USE_PLAYLIST=True)
    def test_add_form_page(self) -> None:
        """Test if the form to add a new playlist is present."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.addUrl)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertTrue(
            _("Add a playlist") in response.content.decode(),
            "Test of 'Add a playlist' is visible in the page.",
        )
        self.client.logout()
        print(" --->  test_add_form_page ok")

    @override_settings(USE_PLAYLIST=True)
    def test_edit_form_page(self) -> None:
        """Test if the form to edit a playlist is present."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.editUrl)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertTrue(
            _("Edit the playlist") in response.content.decode(),
            "Test of 'Edit the playlist' is visible in the page.",
        )
        self.client.logout()
        print(" --->  test_edit_form_page ok")


class TestStartupPlaylistParamTestCase(TestCase):
    """Add or remove form test case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        self.user = User.objects.create(
            username="simple.user",
            password="user1234user",
        )
        self.simple_playlist = Playlist.objects.create(
            name="My simple playlist",
            visibility="public",
            owner=self.user,
        )
        self.playlist_without_videos = Playlist.objects.create(
            name="My playlist without videos",
            visibility="public",
            owner=self.user,
        )
        self.video = Video.objects.create(
            title="First video",
            owner=self.user,
            video="first_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        user_add_video_in_playlist(self.simple_playlist, self.video)
        self.url = reverse("playlist:list")

    @override_settings(USE_PLAYLIST=True)
    def test_link_in_playlists_page(self) -> None:
        """Test if the link is present into the playlists page."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertTrue(
            f"/playlist/start-playlist/{self.simple_playlist.slug}"
            in response.content.decode(),
            "Test if the link is present into the playlists page.",
        )
        self.client.logout()
        print(" --->  test_link_in_playlists_page ok")

    @override_settings(USE_PLAYLIST=True)
    def test_disabled_in_playlists_page(self) -> None:
        """Test if the disabled is present into the playlists page."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200.",
        )
        self.assertTrue(
            "disabled" in response.content.decode(),
            "Test if the disabled is present into the playlists page.",
        )
        self.client.logout()
        print(" --->  test_disabled_in_playlists_page ok")


class TestPlaylistPage(TestCase):
    """Playlist page test case."""

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
        self.playlist_user1 = Playlist.objects.create(
            name="Playlist1",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user,
        )
        self.playlist_user2 = Playlist.objects.create(
            name="Playlist2",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user2,
        )

        self.url_fav_user1 = reverse(
            "playlist:content",
            kwargs={"slug": get_favorite_playlist_for_user(self.user).slug},
        )
        self.url_fav_user2 = reverse(
            "playlist:content",
            kwargs={"slug": get_favorite_playlist_for_user(self.user2).slug},
        )

        self.playlist_content_1 = PlaylistContent.objects.create(
            playlist=self.playlist_user1,
            video=self.video,
            rank=1,
        )

    @override_settings(USE_FAVORITES=True)
    def test_playlist_video_list(self):
        """Test if the favorite video list has a correct number of video in it."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        user_add_video_in_playlist(get_favorite_playlist_for_user(self.user), self.video)
        user_add_video_in_playlist(get_favorite_playlist_for_user(self.user), self.video2)
        response = self.client.get(self.url_fav_user1)
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200 when the favorite video list isn't empty",
        )
        self.assertTrue(
            'data-countvideos="2"' in response.content.decode(),
            "Test if the playlist video list isn't empty",
        )
        self.client.logout()

        self.client.force_login(self.user2)
        user_add_video_in_playlist(self.playlist_user2, self.video3)
        response = self.client.get(
            reverse("playlist:content", kwargs={"slug": self.playlist_user2.slug})
        )
        self.assertTrue(
            'data-countvideos="1"' in response.content.decode(),
            "Test if the playlist video list isn't empty",
        )
        print(" --->  test_playlist_video_list ok")

    @override_settings(USE_FAVORITES=True)
    def test_favorite_video_list_link_in_navbar(self) -> None:
        """Test if the favorite video list link is present in the navbar."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertEqual(
            response.status_code,
            200,
            "Test if status code equal 200 in test_favorite_video_list_link_in_navbar",
        )
        self.assertTrue(
            str(_("My favorite videos")) in response.content.decode(),
            "Test if the favorite video list link is present in the navbar",
        )
        self.assertTrue(
            self.url_fav_user1 in response.content.decode(),
        )
        self.client.logout()
        print(" --->  test_favorite_video_list_link_in_navbar ok")

    def test_folder_icon_in_video_links(self) -> None:
        """Test if the differents icons appears correctly."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        user_add_video_in_playlist(self.playlist_user1, self.video)
        user_add_video_in_playlist(get_favorite_playlist_for_user(self.user), self.video)
        response = self.client.get(
            reverse("playlist:content", kwargs={"slug": self.playlist_user1.slug})
        )
        self.assertTrue(
            'class="bi bi-folder-minus card-footer-link-i"' in response.content.decode()
        )
        response = self.client.get(self.url_fav_user1)
        self.assertFalse(
            'class="bi bi-folder-minus card-footer-link-i"' in response.content.decode()
        )
        self.client.logout()
        print(" --->  test_folder_icon_in_video_links ok")

    def test_favorites_name_translate(self) -> None:
        """Test if the favorites name is correctly translated."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.url_fav_user1)
        self.assertTrue(
            f'{_("Playlist")} : {_(FAVORITE_PLAYLIST_NAME)}' in response.content.decode()
        )
        self.client.logout()
        print(" --->  test_folder_icon_in_video_links ok")

    def test_manage_section_for_editable_playlists(self) -> None:
        """Test if the manage section appears correctly for an editable playlist."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("playlist:content", kwargs={"slug": self.playlist_user1.slug})
        )
        self.assertTrue('id="card-manage-playlist"' in response.content.decode())
        response = self.client.get(self.url_fav_user1)
        self.assertFalse('id="card-manage-playlist"' in response.content.decode())
        self.client.logout()
        print(" --->  test_manage_section_for_editable_playlists ok")

    @override_settings(USE_PLAYLIST=True)
    def test_remove_video_in_playlist(self):
        """Test if remove a video from a playlist works."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        url_content = reverse(
            "playlist:content", kwargs={"slug": self.playlist_user1.slug}
        )
        response = self.client.get(url_content)
        self.assertTrue(
            'data-countvideos="1"' in response.content.decode(),
            "Test if there's 1 video in the playlist.",
        )
        url = reverse(
            "playlist:remove-video",
            kwargs={
                "slug": self.playlist_user1.slug,
                "video_slug": self.video.slug,
            },
        )
        response = self.client.get(url, HTTP_REFERER=url_content)
        self.assertEqual(response.status_code, 302)

        redirected_url = response.url
        response = self.client.get(redirected_url)
        self.assertTrue(
            'data-countvideos="0"' in response.content.decode(),
            "Test if there's 0 video in the playlist.",
        )
        print(" --->  test_remove_video_in_playlist ok")

    @override_settings(USE_PLAYLIST=True)
    def test_remove_video_in_playlist_json(self):
        """Test if remove a video from a playlist works with JSON."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        url_content = reverse(
            "playlist:content", kwargs={"slug": self.playlist_user1.slug}
        )
        response = self.client.get(url_content)
        self.assertTrue(
            'data-countvideos="1"' in response.content.decode(),
            "Test if there's 1 video in the playlist.",
        )

        url = (
            reverse(
                "playlist:remove-video",
                kwargs={
                    "slug": self.playlist_user1.slug,
                    "video_slug": self.video.slug,
                },
            )
            + "?json=1"
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = JsonResponse({"state": "out-playlist"}).content.decode("utf-8")
        self.assertEqual(response.content.decode("utf-8"), data)

        response = self.client.get(url_content)
        self.assertTrue(
            'data-countvideos="0"' in response.content.decode(),
            "Test if there's 0 video in the playlist.",
        )
        print(" --->  test_remove_video_in_playlist_json ok")


class TestStatsInfoTestCase(TestCase):
    """Statistics informations test case."""

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
        self.playlist_user1 = Playlist.objects.create(
            name="Playlist1",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user,
        )
        self.playlist_user2 = Playlist.objects.create(
            name="Playlist2",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user2,
        )
        user_add_video_in_playlist(get_favorite_playlist_for_user(self.user), self.video)
        user_add_video_in_playlist(get_favorite_playlist_for_user(self.user2), self.video)
        user_add_video_in_playlist(self.playlist_user1, self.video)
        user_add_video_in_playlist(self.playlist_user2, self.video)
        user_add_video_in_playlist(get_favorite_playlist_for_user(self.user), self.video2)
        # Video 1 -> 2 favorites and in 4 playlists (2 favs and playlist1, playlist2)
        # Video 2 -> 1 favorite and in 1 playlists (1 fav)
        # Video 3 -> 0

        self.url_video1 = reverse("video:video", args=[self.video.slug])
        self.url_video2 = reverse("video:video", args=[self.video2.slug])
        self.url_video3 = reverse("video:video", args=[self.video3.slug])

    def test_favorites_count(self) -> None:
        """Test if the favorites counter works correctly."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.url_video1)
        self.assertTrue(
            '<span id="favorites_count">2</span>' in response.content.decode()
        )
        response = self.client.get(self.url_video2)
        self.assertTrue(
            '<span id="favorites_count">1</span>' in response.content.decode()
        )
        response = self.client.get(self.url_video3)
        self.assertTrue(
            '<span id="favorites_count">0</span>' in response.content.decode()
        )
        self.client.logout()
        print(" --->  test_favorites_count ok")

    def test_playlists_count(self) -> None:
        """Test if the playlists counter works correctly."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(self.url_video1)
        self.assertTrue(
            '<span id="addition_playlists_count">4</span>' in response.content.decode()
        )
        response = self.client.get(self.url_video2)
        self.assertTrue(
            '<span id="addition_playlists_count">1</span>' in response.content.decode()
        )
        response = self.client.get(self.url_video3)
        self.assertTrue(
            '<span id="addition_playlists_count">0</span>' in response.content.decode()
        )
        self.client.logout()
        print(" --->  test_playlists_count ok")

    def test_navbar_user_menu_counters(self) -> None:
        """Test test_navbar_user_menu_counters works correctly."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get("/")

        self.assertTrue(
            '<span id="stats-usermenu-video-count">2</span>' in response.content.decode()
        )
        self.assertTrue(
            '<span id="stats-usermenu-playlist-count">2</span>'
            in response.content.decode()
        )
        self.client.logout()

        self.client.force_login(self.user2)
        response = self.client.get("/")

        self.assertTrue(
            '<span id="stats-usermenu-video-count">1</span>' in response.content.decode()
        )
        self.assertTrue(
            '<span id="stats-usermenu-playlist-count">2</span>'
            in response.content.decode()
        )
        self.client.logout()

        print(" --->  test_navbar_user_menu_counters ok")


class TestPrivatePlaylistTestCase(TestCase):
    """Private playlist test case."""

    fixtures = ["initial_data.json"]

    @override_settings(USE_PLAYLIST=True, USE_FAVORITES=True)
    def setUp(self) -> None:
        """Set up tests."""
        self.first_student = User.objects.create(
            username="student", password="student1234student"
        )
        self.second_student = User.objects.create(
            username="student2", password="student1234student"
        )
        self.url_private_playlist = reverse(
            "playlist:content",
            kwargs={"slug": get_favorite_playlist_for_user(self.second_student).slug},
        )

    @override_settings(USE_PLAYLIST=True, USE_FAVORITES=True)
    def test_user_redirect_if_private_playlist_playlists(self) -> None:
        """Test if when an user try to browse a private playlist, he is redirected to the playlists page."""
        importlib.reload(context_processors)
        self.client.force_login(self.first_student)
        response = self.client.get(self.url_private_playlist)
        self.assertEqual(response.status_code, 302)
        self.client.logout()
        print(" --->  test_user_redirect_if_private_playlist_playlists ok")


class TestPlaylistPlayerTestCase(TestCase):
    """Playlist player test case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up tests."""
        self.first_student = User.objects.create(
            username="student", password="student1234student"
        )
        self.second_student = User.objects.create(
            username="student2", password="student1234student"
        )
        self.super_user = User.objects.create(username="admin", password="admin1234admin")
        self.video_first_student = Video.objects.create(
            title="Video First Student",
            owner=self.first_student,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.video_first_student_draft = Video.objects.create(
            title="Video First Student Draft",
            owner=self.first_student,
            video="test.mp4",
            is_draft=True,
            type=Type.objects.get(id=1),
        )
        self.video_second_student = Video.objects.create(
            title="Video Second Student",
            owner=self.second_student,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.video_second_student_draft = Video.objects.create(
            title="Video Second Student Draft",
            owner=self.second_student,
            video="test.mp4",
            is_draft=True,
            type=Type.objects.get(id=1),
        )
        self.video_super_user = Video.objects.create(
            title="Video Second Student Draft",
            owner=self.super_user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.video_super_user = Video.objects.create(
            title="Video Super User",
            owner=self.super_user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.video_super_user_draft = Video.objects.create(
            title="Video Super User Draft",
            owner=self.super_user,
            video="test.mp4",
            is_draft=True,
            type=Type.objects.get(id=1),
        )
        self.playlist_first_video_is_disabled = Playlist.objects.create(
            name="Playlist first video is blocked",
            description="The first video of this playlist is blocked.",
            visibility="public",
            autoplay=True,
            owner=self.first_student,
        )
        self.simple_playlist = Playlist.objects.create(
            name="Simple Playlist",
            description="This playlist is simple.",
            visibility="public",
            autoplay=True,
            owner=self.first_student,
        )
        self.big_playlist = Playlist.objects.create(
            name="Big Playlist",
            description="This playlist is big.",
            visibility="public",
            autoplay=True,
            owner=self.first_student,
        )
        # TODO Make a for boucle to don't repeat function call
        tuples_to_link = [
            (self.playlist_first_video_is_disabled, self.video_second_student_draft),
            (self.playlist_first_video_is_disabled, self.video_first_student),
            (self.simple_playlist, self.video_first_student),
            (self.simple_playlist, self.video_first_student_draft),
            (self.big_playlist, self.video_first_student),
            (self.big_playlist, self.video_first_student_draft),
            (self.big_playlist, self.video_second_student),
            (self.big_playlist, self.video_second_student_draft),
            (self.big_playlist, self.video_super_user),
            (self.big_playlist, self.video_super_user_draft),
        ]
        for tuple in tuples_to_link:
            user_add_video_in_playlist(tuple[0], tuple[1])

    @override_settings(USE_PLAYLIST=True)
    def test_switch_video_in_playlist_player(self) -> None:
        """Test if the video switch correctly when the user click on an other video."""
        importlib.reload(context_processors)
        self.client.force_login(self.first_student)
        response = self.client.get(
            f'{reverse("video:video", kwargs={"slug": self.video_first_student.slug})}?playlist={self.simple_playlist.slug}'
        )
        next_video_url = f'{reverse("video:video", kwargs={"slug": self.video_first_student_draft.slug})}?playlist={self.simple_playlist.slug}'
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        next_video_html_element = soup.find_all(
            attrs={
                "href": next_video_url,
            }
        )
        self.assertIsNotNone(next_video_html_element)
        self.client.logout()
        print(" --->  test_switch_video_in_playlist_player ok")

    @override_settings(USE_PLAYLIST=True)
    def test_draft_videos_in_playlist_player(self) -> None:
        """Test if the draft videos are correctly disabled in the playlist player."""
        importlib.reload(context_processors)
        self.client.force_login(self.second_student)
        next_video_url = f'{reverse("video:video", kwargs={"slug": self.video_first_student_draft.slug})}?playlist={self.simple_playlist.slug}'
        response = self.client.get(
            f'{reverse("video:video", kwargs={"slug": self.video_first_student.slug})}?playlist={self.simple_playlist.slug}'
        )
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        next_video_html_elements = soup.find_all(
            attrs={
                "href": next_video_url,
            }
        )
        self.assertEqual(next_video_html_elements, [])
        self.client.logout()
        print(" --->  test_draft_videos_in_playlist_player ok")

    @override_settings(USE_PLAYLIST=True)
    def test_scrollbar_is_present_in_playlist_player_box(self) -> None:
        """Test if the scrollbar is correctly present in the playlist player box when it has more than 5 videos."""
        importlib.reload(context_processors)
        self.client.force_login(self.first_student)
        response = self.client.get(
            f'{reverse("video:video", kwargs={"slug": self.video_first_student.slug})}?playlist={self.big_playlist.slug}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("scroll-container" in response.content.decode())
        self.client.logout()
        print(" --->  test_scrollbar_is_present_in_playlist_player_box ok")

    @override_settings(USE_PLAYLIST=True)
    def test_scrollbar_is_not_present_in_playlist_player_box(self) -> None:
        """Test if the scrollbar is not present in the playlist player box when it has less than 6 videos."""
        importlib.reload(context_processors)
        self.client.force_login(self.first_student)
        response = self.client.get(
            f'{reverse("video:video", kwargs={"slug": self.video_first_student.slug})}?playlist={self.simple_playlist.slug}'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse("scroll-container" in response.content.decode())
        self.client.logout()
        print(" --->  test_scrollbar_is_not_present_in_playlist_player_box ok")


class StartPlaylistViewTest(TestCase):
    """Start playlist tests."""

    fixtures = ["initial_data.json"]

    def setUp(self):
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
        self.public_playlist_user1 = Playlist.objects.create(
            name="Playlist1",
            description="Ma description",
            visibility="public",
            autoplay=True,
            owner=self.user,
        )
        self.protected_playlist_user1 = Playlist.objects.create(
            name="Playlist2",
            description="Ma description",
            visibility="protected",
            password="password",
            autoplay=True,
            owner=self.user,
        )
        self.private_playlist_user1 = Playlist.objects.create(
            name="Playlist2",
            description="Ma description",
            visibility="private",
            autoplay=True,
            owner=self.user,
        )
        user_add_video_in_playlist(self.public_playlist_user1, self.video)
        user_add_video_in_playlist(self.public_playlist_user1, self.video2)
        user_add_video_in_playlist(self.public_playlist_user1, self.video3)

        user_add_video_in_playlist(self.protected_playlist_user1, self.video)
        user_add_video_in_playlist(self.protected_playlist_user1, self.video2)
        user_add_video_in_playlist(self.protected_playlist_user1, self.video3)

        user_add_video_in_playlist(self.private_playlist_user1, self.video)
        user_add_video_in_playlist(self.private_playlist_user1, self.video2)
        user_add_video_in_playlist(self.private_playlist_user1, self.video3)

    def test_start_playlist_public(self):
        """Test if start a public playlist works."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "playlist:start-playlist",
                kwargs={"slug": self.public_playlist_user1.slug},
            )
        )
        expected_url = get_link_to_start_playlist(
            self.client.request, self.public_playlist_user1
        )
        self.assertRedirects(response, expected_url)
        self.client.logout()
        print(" --->  test_start_playlist_public ok")

    def test_start_playlist_private_owner(self):
        """Test if start a private playlist when owner of it works."""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "playlist:start-playlist",
                kwargs={"slug": self.private_playlist_user1.slug},
            )
        )
        expected_url = get_link_to_start_playlist(
            self.client.request, self.private_playlist_user1
        )
        self.assertRedirects(response, expected_url)
        self.client.logout()
        print(" --->  test_start_playlist_private_owner ok")

    def test_start_playlist_private_not_owner(self):
        """Test if start a private playlist don't works if not owner of it."""
        importlib.reload(context_processors)
        self.client.force_login(self.user2)
        response = self.client.get(
            reverse(
                "playlist:start-playlist",
                kwargs={"slug": self.private_playlist_user1.slug},
            )
        )
        expected_url = reverse("playlist:list")
        self.assertRedirects(response, expected_url)
        self.client.logout()
        print(" --->  test_start_playlist_private_not_owner ok")

    def test_start_playlist_protected_get_request_not_owner(self):
        """Test if form password is present when not owner of a protected playlist"""
        importlib.reload(context_processors)
        self.client.force_login(self.user2)
        response = self.client.get(
            reverse(
                "playlist:start-playlist",
                kwargs={"slug": self.protected_playlist_user1.slug},
            )
        )
        self.assertTemplateUsed(response, "playlist/protected-playlist-form.html")
        print(" --->  test_start_playlist_protected_get_request_not_owner ok")

    def test_start_playlist_protected_get_request_owner(self):
        """Test if form password is not present when owner of a protected playlist"""
        importlib.reload(context_processors)
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "playlist:start-playlist",
                kwargs={"slug": self.protected_playlist_user1.slug},
            )
        )
        expected_url = get_link_to_start_playlist(
            self.client.request, self.protected_playlist_user1
        )
        self.assertRedirects(response, expected_url)
        self.assertTemplateNotUsed(response, "playlist/protected-playlist-form.html")
        print(" --->  test_start_playlist_protected_get_request_owner ok")
