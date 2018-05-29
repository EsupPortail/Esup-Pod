from django.test import TestCase
from django.test import override_settings
from django.conf import settings
from django.test import Client

from pod.video.models import Channel
from pod.video.models import Theme

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
        Channel.objects.create(title="ChannelTest1")
        Channel.objects.create(title="ChannelTest2")
        Theme.objects.create(
            title="Theme1", slug="blabla",
            channel=Channel.objects.get(title="ChannelTest1"))
        owner1 = Owner.objects.get(user__username="pod")
        Video.objects.create(
            title="Video1", owner=owner1, video="test.mp4")

    def test_get_channel_view(self):
        self.client = Client()
        response = self.client.get(
            "/%s/" % Channel.objects.get(title="ChannelTest1").slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context[u"channel"],
            Channel.objects.get(title="ChannelTest1"))
        self.assertEqual(
            response.context[u"theme"], None)
        print(
            "   --->  test_channel_without_theme"
            "_in_argument of ChannelTestView : OK !"
        )
        response = self.client.get(
            "/%s/" % Channel.objects.get(title="ChannelTest2").slug)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context[u"channel"],
            Channel.objects.get(title="ChannelTest2"))
        self.assertEqual(
            response.context[u"theme"], None)
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
