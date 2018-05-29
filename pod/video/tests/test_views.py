from django.test import TestCase
from django.test import override_settings
from django.conf import settings
from django.test import Client
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Video

import os


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    },
    LANGUAGE_CODE='en'
)
class ChannelTestView(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        c = Channel.objects.create(title="ChannelTest1")
        Channel.objects.create(title="ChannelTest2")
        Theme.objects.create(
            title="Theme1", slug="blabla",
            channel=Channel.objects.get(title="ChannelTest1"))
        user = User.objects.create(username="pod", password="pod1234pod")
        v = Video.objects.create(
            title="Video1", owner=user, video="test.mp4", is_draft=False)
        v.channel.add(c)
        v.save()

    def test_get_channel_view(self):
        self.client = Client()
        response = self.client.get(
            "/%s/" % Channel.objects.get(title="ChannelTest1").slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["channel"],
            Channel.objects.get(title="ChannelTest1"))
        self.assertEqual(
            response.context["theme"], None)
        self.assertEqual(
            response.context["videos"].paginator.count, 1)
        print(
            "   --->  test_channel_without_theme"
            "_in_argument of ChannelTestView : OK !"
        )
        response = self.client.get(
            "/%s/" % Channel.objects.get(title="ChannelTest2").slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["channel"],
            Channel.objects.get(title="ChannelTest2"))
        self.assertEqual(
            response.context["theme"], None)
        self.assertEqual(
            response.context["videos"].paginator.count, 0)
        print(
            "   --->  test_channel_2_without_theme_in_argument"
            " of ChannelTestView : OK !")
        response = self.client.get(
            "/%s/%s/" % (
                Channel.objects.get(title="ChannelTest1").slug,
                Theme.objects.get(title="Theme1").slug)
        )
        self.assertEqual(response.status_code, 200)
        print(
            "   --->  test_channel_with_theme_in_argument"
            " of ChannelTestView : OK !")


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    },
    LANGUAGE_CODE='en'
)
class MyChannelsTestView(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        c1 = Channel.objects.create(title="ChannelTest1")
        c1.owners.add(user)
        c2 = Channel.objects.create(title="ChannelTest2")
        c2.owners.add(user)
        print(" --->  SetUp of MyChannelsTestView : OK !")

    def test_get_mychannels_view(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/my_channels/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["channels"].count(), 2)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/my_channels/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["channels"].count(), 0)
        print(" --->  test_get_mychannels_view of MyChannelsTestView : OK !")


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    },
    LANGUAGE_CODE='en'
)
class ChannelEditTestView(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        c1 = Channel.objects.create(title="ChannelTest1")
        c1.owners.add(user)
        print(" --->  SetUp of ChannelEditTestView : OK !")

    def test_channel_edit_get_request(self):
        self.client = Client()
        channel = Channel.objects.get(title="ChannelTest1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get("/channel_edit/slugauhasard/")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/channel_edit/%s/" % channel.slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].instance, channel)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get("/channel_edit/%s/" % channel.slug)
        self.assertEqual(response.status_code, 403)
        print(
            " --->  test_channel_edit_get_request of ChannelEditTestView : OK !")

    def test_channel_edit_post_request(self):
        self.client = Client()
        channel = Channel.objects.get(title="ChannelTest1")
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.post(
            '/channel_edit/%s/' % channel.slug, {'title': "ChannelTest1", 'description': '<p>bl</p>\r\n'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"The changes have been saved." in response.content)
        c = Channel.objects.get(title="ChannelTest1")
        self.assertEqual(c.description, '<p>bl</p>')
        print(
            "   --->  test_channel_edit_post_request of ChannelEditTestView : OK !")
