"""
Unit tests for playlist models
"""
from django.test import TestCase
from django.contrib.auth.models import User
from pod.video.models import Video
from pod.playlist.models import Playlist
from pod.playlist.models import PlaylistElement


class PlaylistModelTestCase(TestCase):

	def setUp(self):
		owner = User.objects.create(username='test')
		playlist = Playlist.objects.create(
			title='playlist',
			owner=owner,
		)
		video = Video.objects.create(
			title='video1',
			owner=owner,
			video='test.mp4'
		)
		video2 = Video.objects.create(
			title='video2',
			owner=owner,
			video='test.mp4'
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
		self.assertEqual(playlist.slug, '2-playlist')
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
		element = PlaylistElement.objects.get(id=1)
		element2 = PlaylistElement.objects.get(id=2)
		self.assertTrue(playlist.videos().length == 2)
		self.assertEqual(playlist.videos()[0], element)
		self.assertEqual(playlist.videos()[1], element2)

		print(" ---> test_videos : OK ! --- PlaylistModel")

	def test_delete(self):
		Playlist.objects.get(id=1).delete()
		Playlist.objects.get(id=2).delete()
		self.assertEqual(Playlist.objects.all().count(), 0)
		self.assertEqual(PlaylistElement.objects.all().count(), 0)

		print(" ---> test_delete : OK ! --- PlaylistModel")
