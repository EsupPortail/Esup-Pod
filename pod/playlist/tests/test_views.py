"""
Unit tests for playlist views
"""
import json

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from pod.video.models import Video
from pod.video.models import Type
from pod.playlist.models import Playlist
from pod.playlist.models import PlaylistElement
from django.contrib.sites.models import Site


class PlaylistViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        owner = User.objects.create(username='test', password='azerty')
        owner.set_password('hello')
        owner.save()
        videotype = Type.objects.create(
            title='others'
        )
        Video.objects.create(
            title='video1',
            type=videotype,
            owner=owner,
            video='video1.mp4',
            duration=20,
            is_draft=False)
        Video.objects.create(
            title='video2',
            type=videotype,
            owner=owner,
            video='video2.mp4',
            duration=30,
            is_draft=False)

        owner.owner.sites.add(Site.objects.get_current())
        owner.owner.save()

    def test_myplaylist(self):
        response = self.client.get('/my_playlists/')
        self.assertEqual(response.status_code, 302)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/my_playlists/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_playlists.html')

        print(" [ BEGIN PLAYLIST VIEWS ] ")
        print(" ---> test_myplaylist : OK!")

    def test_playlist_create(self):
        owner = User.objects.get(id=1)
        response = self.client.get('/playlist/')
        self.assertEqual(response.status_code, 302)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/playlist/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'playlist.html')
        self.assertContains(response, 'playlist_form')
        self.assertContains(response, _('Add a new playlist'))
        response = self.client.post(
            '/playlist/',
            data={'action': 'edit',
                  'playlist_id': None,
                  'title': 'playlist1',
                  'owner': owner.id,
                  'description': 'test',
                  'visible': False})
        self.assertEqual(response.status_code, 200)
        result = Playlist.objects.all()
        self.assertTrue(result)
        self.assertTemplateUsed(response, 'playlist.html')
        self.assertContains(response, _('Editing the playlist'))
        self.assertContains(response, 'playlist1')

        print(" ---> test_playlist_create : OK!")

    def test_playlist_add(self):
        owner = User.objects.get(id=1)
        playlist = Playlist.objects.create(
            title='playlist1',
            owner=owner,
            description='test',
            visible=False
        )
        video1 = Video.objects.get(id=1)
        video2 = Video.objects.get(id=2)
        response = self.client.get('/playlist/{0}/'.format(playlist.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/playlist/{0}/'.format(playlist.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'playlist.html')
        self.assertContains(response, 'playlist_form')
        self.assertContains(response, _('Editing the playlist'))
        self.assertContains(response, 'playlist1')
        response = self.client.post(
            '/playlist/{0}/'.format(playlist.slug),
            data={'action': 'add',
                  'video': video1.slug})
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            '/playlist/{0}/'.format(playlist.slug),
            {'action': 'add',
             'video': video1.slug},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'success')
        result = PlaylistElement.objects.get(
            playlist=playlist, video=video1, position=1)
        self.assertTrue(result)
        response = self.client.post(
            '/playlist/{0}/'.format(playlist.slug),
            {'action': 'add',
             'video': video2.slug},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'success')
        result = PlaylistElement.objects.get(
            playlist=playlist, video=video2, position=2)
        self.assertTrue(result)

        print(" ---> test_playlist_add : OK!")

    def test_playlist_remove(self):
        owner = User.objects.get(id=1)
        playlist = Playlist.objects.create(
            title='playlist1',
            owner=owner,
            description='test',
            visible=False
        )
        video1 = Video.objects.get(id=1)
        video2 = Video.objects.get(id=2)
        PlaylistElement.objects.create(
            playlist=playlist,
            video=video1,
            position=1
        )
        PlaylistElement.objects.create(
            playlist=playlist,
            video=video2,
            position=2
        )
        response = self.client.get('/playlist/{0}/'.format(playlist.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/playlist/{0}/'.format(playlist.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'playlist.html')
        self.assertContains(response, 'playlist_form')
        self.assertContains(response, _('Editing the playlist'))
        self.assertContains(response, 'playlist1')
        self.assertContains(response, 'video1')
        self.assertContains(response, 'video2')
        response = self.client.post(
            '/playlist/{0}/'.format(playlist.slug),
            data={'action': 'remove',
                  'video': video1.slug})
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            '/playlist/{0}/'.format(playlist.slug),
            {'action': 'remove',
             'video': video1.slug},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(response.status_code, 200)
        self.assertContains(response, 'success')
        result = PlaylistElement.objects.all()
        self.assertTrue(result.count() == 1)
        self.assertEqual(result.first().position, 1)

        print(" ---> test_playlist_remove : OK!")
        print(" [ END PLAYLIST VIEWS ] ")

    def test_playlist_move(self):
        owner = User.objects.get(id=1)
        playlist = Playlist.objects.create(
            title='playlist1',
            owner=owner,
            description='test',
            visible=False
        )
        video1 = Video.objects.get(id=1)
        video2 = Video.objects.get(id=2)
        PlaylistElement.objects.create(
            playlist=playlist,
            video=video1,
            position=1
        )
        PlaylistElement.objects.create(
            playlist=playlist,
            video=video2,
            position=2
        )
        response = self.client.get('/playlist/{0}/'.format(playlist.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/playlist/{0}/'.format(playlist.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'playlist.html')
        self.assertContains(response, 'playlist_form')
        self.assertContains(response, _('Editing the playlist'))
        self.assertContains(response, 'playlist1')
        self.assertContains(response, 'video1')
        self.assertContains(response, 'video2')
        response = self.client.post(
            '/playlist/{0}/'.format(playlist.slug),
            data={'action': 'move',
                  'videos': {
                      'video1': 2,
                      'video2': 1
                  }})
        self.assertEqual(response.status_code, 400)
        json_data = json.dumps(
            {video1.slug: 2, video2.slug: 1})
        response = self.client.post(
            '/playlist/{0}/'.format(playlist.slug),
            data={'action': 'move',
                  'videos': json_data},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'success')
        result = PlaylistElement.objects.get(
            playlist=playlist,
            video=video1)
        self.assertEqual(result.position, 2)
        result = PlaylistElement.objects.get(
            playlist=playlist,
            video=video2)
        self.assertEqual(result.position, 1)

        print(" ---> test_playlist_move : OK!")

    def test_playlist_delete(self):
        owner = User.objects.get(id=1)
        playlist = Playlist.objects.create(
            title='playlist1',
            owner=owner,
            description='test',
            visible=False
        )
        video1 = Video.objects.get(id=1)
        PlaylistElement.objects.create(
            playlist=playlist,
            video=video1,
            position=1
        )
        response = self.client.get('/playlist/{0}/'.format(playlist.slug))
        self.assertEqual(response.status_code, 302)
        authenticate(username='test', password='hello')
        login = self.client.login(username='test', password='hello')
        self.assertTrue(login)
        response = self.client.get('/playlist/{0}/'.format(playlist.slug))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'playlist.html')
        self.assertContains(response, 'playlist_form')
        self.assertContains(response, _('Editing the playlist'))
        self.assertContains(response, 'playlist1')
        self.assertContains(response, 'video1')
        response = self.client.post(
            '/playlist/{0}/'.format(playlist.slug),
            data={'action': 'delete'})
        self.assertEqual(response.status_code, 400)
        response = self.client.post(
            '/playlist/{0}/'.format(playlist.slug),
            {'action': 'delete'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = Playlist.objects.all()
        self.assertFalse(result)
        result = PlaylistElement.objects.all()
        self.assertFalse(result)

        print(" ---> test_playlist_delete : OK!")
