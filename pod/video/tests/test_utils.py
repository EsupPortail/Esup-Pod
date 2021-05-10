from django.test import TestCase
from django.contrib.auth.models import User

from pod.video.models import Video, Type
from pod.video.utils import pagination_data


class ChannelTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        self.v = Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

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
