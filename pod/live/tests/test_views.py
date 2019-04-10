"""
Unit tests for live views
"""
import os

from django.conf import settings
from django.test import override_settings
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from pod.live.models import Building, Broadcaster


if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    },
    LANGUAGE_CODE='en',
    THIRD_PARTY_APPS=['live']
)
class LiveViewsTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        user = User.objects.create(username='pod', password='podv2')
        building = Building.objects.create(name="bulding1")
        if FILEPICKER:
            homedir, created = UserFolder.objects.get_or_create(
                name='Home',
                owner=user)
            poster = CustomImageModel.objects.create(
                folder=homedir,
                created_by=user,
                file="blabla.jpg")
        else:
            poster = CustomImageModel.objects.create(file="blabla.jpg")
        Broadcaster.objects.create(
            name="broadcaster1",
            poster=poster,
            url="http://test.live",
            status=True,
            is_restricted=True,
            building=building)
        Broadcaster.objects.create(
            name="broadcaster2",
            poster=poster,
            url="http://test2.live",
            status=True,
            is_restricted=False,
            building=building)

        print(" --->  SetUp of liveViewsTestCase : OK !")

    def test_lives(self):
        self.client = Client()
        response = self.client.get('/live/')
        self.assertTemplateUsed(response, 'live/lives.html')

        print(
            "   --->  test_lives of liveViewsTestCase : OK !")

    def test_video_live(self):
        self.client = Client()
        self.user = User.objects.get(username='pod')

        # User not loged in
        # Broadcaster restricted
        self.broadcaster = Broadcaster.objects.get(name='broadcaster1')
        response = self.client.get('/live/%s/' % self.broadcaster.id)
        self.assertRedirects(
            response,
            '%s?referrer=%s' % (
                settings.LOGIN_URL,
                '/live/%s/' % self.broadcaster.id), target_status_code=302)
        # Broadcaster not restricted
        self.broadcaster = Broadcaster.objects.get(name='broadcaster2')
        response = self.client.get('/live/%s/' % self.broadcaster.id)
        self.assertTemplateUsed(response, "live/live.html")

        # User loged in
        self.client.force_login(self.user)
        # Broadcaster restricted
        self.broadcaster = Broadcaster.objects.get(name='broadcaster1')
        response = self.client.get('/live/%s/' % self.broadcaster.id)
        self.assertTemplateUsed(response, "live/live.html")
        # Broadcaster not restricted
        self.broadcaster = Broadcaster.objects.get(name='broadcaster2')
        response = self.client.get('/live/%s/' % self.broadcaster.id)
        self.assertTemplateUsed(response, "live/live.html")

        print(
            "   --->  test_video_live of liveViewsTestCase : OK !")
