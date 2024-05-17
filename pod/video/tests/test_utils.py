"""Unit tests for Esup-Pod video utilities."""

import json

from django.test import TestCase
from django.contrib.auth.models import User

from pod.video.models import Channel, Theme, Video, Type
from pod.video.utils import pagination_data, get_headband, change_owner, get_videos


class VideoTestUtils(TestCase):
    """TestCase for Esup-Pod video utilities."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
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

    def test_pagination_data(self) -> None:
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

    def test_get_headband(self) -> None:
        self.assertEqual(get_headband(self.c).get("type", None), "channel")
        self.assertEqual(get_headband(self.c, self.theme).get("type", None), "theme")

    def test_change_owner(self) -> None:
        """Change video owner."""
        actual = change_owner(str(self.v.id), self.user2)
        self.assertEqual(actual, True)
        # Must return false with non-existent video id
        self.assertEqual(change_owner(100, self.user2), False)

    def test_get_videos(self) -> None:
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
