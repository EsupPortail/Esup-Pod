"""
Unit tests for playlist models
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from pod.video.models import Video
from pod.video.models import Type
from pod.playlist.models import Playlist
from pod.playlist.models import PlaylistElement


class PlaylistModelTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        owner = User.objects.create(username='test')
        playlist = Playlist.objects.create(
            title='playlist',
            owner=owner,
        )
        videotype = Type.objects.create(
            title='others'
        )
        video = Video.objects.create(
            title='video1',
            type=videotype,
            owner=owner,
            video='test.mp4',
            is_draft=False
        )
        video2 = Video.objects.create(
            title='video2',
            type=videotype,
            owner=owner,
            video='test.mp4',
            is_draft=False
        )
        Playlist.objects.create(
            title='playlist2',
            owner=owner,
            description='description',
            visible=True
        )
        PlaylistElement.objects.create(
            playlist=playlist,
            video=video,
            position=1
        )
        PlaylistElement.objects.create(
            playlist=playlist,
            video=video2,
            position=2
        )

    def test_attributs(self):
        playlist = Playlist.objects.get(id=1)
        owner = User.objects.get(id=1)
        self.assertEqual(playlist.title, 'playlist')
        self.assertEqual(playlist.slug, '1-playlist')
        self.assertEqual(playlist.owner, owner)
        self.assertEqual(playlist.description, None)
        self.assertFalse(playlist.visible)

        print(" ---> test_attributs : OK ! --- PlaylistModel")

    def test_attributs_full(self):
        playlist = Playlist.objects.get(id=2)
        owner = User.objects.get(id=1)
        self.assertEqual(playlist.title, 'playlist2')
        self.assertEqual(playlist.slug, '2-playlist2')
        self.assertEqual(playlist.owner, owner)
        self.assertEqual(playlist.description, 'description')
        self.assertTrue(playlist.visible)

        print(" ---> test_attributs_full : OK ! --- PlaylistModel")

    def test_first(self):
        playlist = Playlist.objects.get(id=1)
        element = PlaylistElement.objects.get(id=1)
        self.assertEqual(playlist.first(), element)

        print(" ---> test_first : OK ! --- PlaylistModel")

    def test_last(self):
        playlist = Playlist.objects.get(id=1)
        playlist2 = Playlist.objects.get(id=2)
        self.assertEqual(playlist.last(), 3)
        self.assertEqual(playlist2.last(), 1)

        print(" ---> test_last : OK ! --- PlaylistModel")

    def test_videos(self):
        playlist = Playlist.objects.get(id=1)
        video = Video.objects.get(id=1)
        video2 = Video.objects.get(id=2)
        self.assertTrue(len(playlist.videos()) == 2)
        self.assertEqual(playlist.videos()[0], video)
        self.assertEqual(playlist.videos()[1], video2)

        print(" ---> test_videos : OK ! --- PlaylistModel")
        print(" [ END PLAYLIST_TEST MODEL ] ")

    def test_delete(self):
        Playlist.objects.get(id=1).delete()
        Playlist.objects.get(id=2).delete()
        self.assertEqual(Playlist.objects.all().count(), 0)
        self.assertEqual(PlaylistElement.objects.all().count(), 0)

        print(" ---> test_delete : OK ! --- PlaylistModel")


class PlaylistElementModelTestCase(TestCase):

    def setUp(self):
        owner = User.objects.create(username='test')
        playlist = Playlist.objects.create(
            title='playlist',
            owner=owner,
        )
        videotype = Type.objects.create(
            title='others'
        )
        video = Video.objects.create(
            title='video1',
            type=videotype,
            owner=owner,
            video='test.mp4',
            is_draft=False
        )
        video2 = Video.objects.create(
            title='video2',
            type=videotype,
            owner=owner,
            video='test.mp4',
            is_draft=False
        )
        Video.objects.create(
            title='video3',
            type=videotype,
            owner=owner,
            video='test.mp4'
        )
        Video.objects.create(
            title='video4',
            type=videotype,
            owner=owner,
            video='test.mp4',
            is_draft=False,
            password='test'
        )
        PlaylistElement.objects.create(
            playlist=playlist,
            video=video
        )
        PlaylistElement.objects.create(
            playlist=playlist,
            video=video2,
            position=2
        )

    def test_attributs(self):
        element = PlaylistElement.objects.get(id=1)
        video = Video.objects.get(id=1)
        playlist = Playlist.objects.get(id=1)
        self.assertEqual(element.playlist, playlist)
        self.assertEqual(element.video, video)
        self.assertEqual(element.position, 1)

        print(" ---> test_attributs : OK ! --- PlaylistElementModel")

    def test_attributs_full(self):
        element = PlaylistElement.objects.get(id=2)
        video2 = Video.objects.get(id=2)
        playlist = Playlist.objects.get(id=1)
        self.assertEqual(element.playlist, playlist)
        self.assertEqual(element.video, video2)
        self.assertEqual(element.position, 2)

        print(" ---> test_attributs_full : OK ! --- PlaylistElementModel")

    def test_delete(self):
        PlaylistElement.objects.get(id=1).delete()
        PlaylistElement.objects.get(id=2).delete()
        self.assertTrue(PlaylistElement.objects.all().count() == 0)
        self.assertTrue(Playlist.objects.all().count() == 1)

        print(" ---> test_delete : OK ! --- PlaylistElementModel")

    def test_add_draft(self):
        playlist = Playlist.objects.get(id=1)
        video = Video.objects.get(id=3)
        element = PlaylistElement()
        element.playlist = playlist
        element.video = video
        self.assertRaises(ValidationError, element.clean)

        print(" [ BEGIN PLAYLIST_TEST MODEL ] ")
        print(" ---> test_add_draft : OK ! -- PlaylistElementModel")

    def test_add_password(self):
        playlist = Playlist.objects.get(id=1)
        video = Video.objects.get(id=4)
        element = PlaylistElement()
        element.playlist = playlist
        element.video = video
        self.assertRaises(ValidationError, element.clean)

        print(" ---> test_add_password : OK ! -- PlaylistElementModel")
