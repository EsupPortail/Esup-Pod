import json

from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User

from pod.video.models import Channel, Theme
from pod.video.models import Video, Type
from pod.video.utils import pagination_data, get_headband
from pod.video.utils import change_owner, get_videos, add_default_thumbnail_to_video

if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel


class VideoTestUtils(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        self.user = User.objects.create(username="pod", password="pod1234pod")
        self.user2 = User.objects.create(username="pod2", password="pod1234pod2")
        self.c = Channel.objects.create(title="ChannelTest1")
        self.theme = Theme.objects.create(title="Theme1", slug="blabla", channel=self.c)
        self.v = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        if FILEPICKER:
            homedir, created = UserFolder.objects.get_or_create(name="Home", owner=self.user)
            self.thumbnail = CustomImageModel.objects.create(
                folder=homedir, created_by=self.user, file="blabla.jpg"
            )
            self.thumbnail2 = CustomImageModel.objects.create(
                folder=homedir, created_by=self.user, file="piapia.jpg"
            )
        else:
            self.thumbnail = CustomImageModel.objects.create(file="blabla.jpg")
            self.thumbnail2 = CustomImageModel.objects.create(file="piapia.jpg")

    def test_pagination_data(self):
        # First data, previous_url = None
        data_length = 9
        offset = 0
        limit = 5
        path = "/videos/"
        expected = (
            "{}?limit={}&offset={}".format(path, limit, offset + limit),
            None,
            "1/2",
        )
        actual = pagination_data(path, offset, limit, data_length)
        self.assertEqual(actual, expected)

        # last data, next_url = None
        offset = 5
        expected = (
            None,
            "{}?limit={}&offset={}".format(path, limit, offset - limit),
            "2/2",
        )
        actual = pagination_data(path, offset, limit, data_length)
        self.assertEqual(actual, expected)

    def test_get_headband(self):
        self.assertEqual(get_headband(self.c).get("type", None), "channel")
        self.assertEqual(get_headband(self.c, self.theme).get("type", None), "theme")

    def test_change_owner(self):
        actual = change_owner(str(self.v.id), self.user2)
        self.assertEqual(actual, True)
        # test video doesn't exist
        self.assertEqual(change_owner(100, self.user2), False)

    def test_get_videos(self):
        actual = get_videos(self.v.title, self.user.id)
        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "page_infos": "1/1",
            "results": [
                {
                    "id": self.v.id,
                    "title": self.v.title,
                    "thumbnail": self.v.get_thumbnail_url(),
                },
            ],
        }
        self.assertEqual(json.loads(actual.content.decode("utf-8")), expected)

        # Test with search
        actual = get_videos(self.v.title, self.user.id, search="not found")
        expected = {**expected, "count": 0, "page_infos": "0/0", "results": []}
        self.assertEqual(json.loads(actual.content.decode("utf-8")), expected)

    def test_add_default_thumbnail_to_video(self):
        add_default_thumbnail_to_video(self.v.id, self.thumbnail)
        self.assertEqual(Video.objects.get(id=self.v.id).thumbnail.file, "blabla.jpg")
        add_default_thumbnail_to_video(self.v.id, self.thumbnail2)
        self.assertEqual(Video.objects.get(id=self.v.id).thumbnail.file, "blabla.jpg")
