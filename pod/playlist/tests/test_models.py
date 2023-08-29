"""Tests the models for playlist module."""

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.test import TestCase

from pod.video.models import Type, Video

from ..models import Playlist, PlaylistContent


# ggignore-start
# gitguardian:ignore
class PlaylistModelTests(TestCase):
    """
    Tests for the Playlist model.

    Args:
        TestCase (::class::`django.test.TestCase`): The test case.
    """

    def setUp(self):
        """
        Set up the tests.
        """
        self.user = User.objects.create_user(username="testuser", password="testpassword")

    def test_create_playlist(self):
        """
        Test the model creation.
        """
        playlist = Playlist.objects.create(
            name="Test Playlist",
            description="Test description",
            visibility="public",
            autoplay=True,
            owner=self.user,
        )
        self.assertEqual(playlist.name, "Test Playlist")
        self.assertEqual(playlist.description, "Test description")
        self.assertEqual(playlist.visibility, "public")
        self.assertTrue(playlist.autoplay)
        self.assertEqual(playlist.owner, self.user)
        print(" --->  test_create_playlist ok")

    def test_default_values(self):
        """
        Test the model default values.
        """
        playlist = Playlist.objects.create(owner=self.user)
        self.assertEqual(playlist.name, _("Playlist"))
        self.assertEqual(playlist.description, "")
        self.assertEqual(playlist.password, "")
        self.assertEqual(playlist.visibility, "private")
        self.assertTrue(playlist.autoplay)
        self.assertTrue(playlist.editable)
        print(" --->  test_default_values ok")

    def test_slug_generation(self):
        """
        Test the model slug generation.
        """
        playlist = Playlist.objects.create(name="Test Playlist", owner=self.user)
        self.assertEqual(playlist.slug, f"{playlist.id}-test-playlist")
        print(" --->  test_slug_generation ok")

    def test_additional_owners(self):
        """
        Test the model additional owners.
        """
        owner1 = User.objects.create_user(username="owner1", password="testpassword")
        owner2 = User.objects.create_user(username="owner2", password="testpassword")
        playlist = Playlist.objects.create(name="Test Playlist", owner=owner1)
        playlist.additional_owners.add(owner2)
        self.assertEqual(playlist.additional_owners.count(), 1)
        self.assertEqual(playlist.additional_owners.first(), owner2)
        print(" --->  test_additional_owners ok")

    def test_date_created_and_updated(self):
        """
        Test the model creation date and update date.
        """
        playlist = Playlist.objects.create(name="Test Playlist", owner=self.user)
        self.assertIsNotNone(playlist.date_created)
        self.assertIsNotNone(playlist.date_updated)
        self.assertLessEqual(playlist.date_created, playlist.date_updated)
        print(" --->  test_date_created_and_updated ok")

    def test_string_representation(self):
        """
        Test the model string representation.
        """
        playlist = Playlist.objects.create(name="Test Playlist", owner=self.user)
        self.assertEqual(str(playlist), playlist.slug)
        print(" --->  test_string_representation ok")


class PlaylistContentModelTests(TestCase):
    """
    Tests for the PlaylistContent model.

    Args:
        TestCase (::class::`django.test.TestCase`): The test case.
    """

    fixtures = ["initial_data.json"]

    def setUp(self):
        """
        Set up the tests.
        """
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.playlist = Playlist.objects.create(name="Test Playlist", owner=self.user)
        self.video = Video.objects.create(
            title="Video",
            owner=self.user,
            video="video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.video2 = Video.objects.create(
            title="Video 2",
            owner=self.user,
            video="video-2.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

    def test_create_playlist_content(self):
        """
        Test the model creation.
        """
        playlist_content = PlaylistContent.objects.create(
            playlist=self.playlist, video=self.video
        )
        self.assertEqual(playlist_content.playlist, self.playlist)
        self.assertEqual(playlist_content.video, self.video)
        self.assertEqual(playlist_content.rank, 1)
        print(" --->  test_create_playlist_content ok")

    def test_unique_constraint(self):
        """
        Test creating two playlist contents with the same playlist and video.
        """
        PlaylistContent.objects.create(playlist=self.playlist, video=self.video)
        with self.assertRaises(Exception):
            PlaylistContent.objects.create(playlist=self.playlist, video=self.video)
        print(" --->  test_unique_constraint ok")

    def test_rank_generation(self):
        """
        Test the rank generation playlist content.
        """
        playlist_content1 = PlaylistContent.objects.create(
            playlist=self.playlist, video=self.video
        )
        playlist_content2 = PlaylistContent.objects.create(
            playlist=self.playlist, video=self.video2
        )
        self.assertEqual(playlist_content1.rank, 1)
        self.assertEqual(playlist_content2.rank, 2)
        print(" --->  test_rank_generation ok")

    def test_string_representation(self):
        """
        Test the string representation models.
        """
        playlist_content = PlaylistContent.objects.create(
            playlist=self.playlist, video=self.video
        )
        expected_string = f"Playlist : {self.playlist} - Video : {self.video} - Rank : {playlist_content.rank}"
        self.assertEqual(str(playlist_content), expected_string)
        print(" --->  test_string_representation ok")


# ggignore-end
