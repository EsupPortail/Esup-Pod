"""Unit tests for Esup-Pod video search utilities.

*  run with 'python manage.py test pod.video_search.tests.test_utils'
"""

from django.test import TestCase
from django.contrib.auth.models import User
from elasticsearch import Elasticsearch

from pod.video.models import Video, Type
from .. import utils
from ..utils import index_es, delete_es


class VideoSearchTestUtils(TestCase):
    """TestCase for Esup-Pod video utilities."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        # ping() hides connection/API errors and only returns False. Let info()
        # expose the original failure before creating or indexing a test video.
        with Elasticsearch(
            utils.ES_URL,
            request_timeout=utils.ES_TIMEOUT,
            max_retries=utils.ES_MAX_RETRIES,
            retry_on_timeout=True,
            **utils.ES_OPTIONS,
        ) as es:
            es.info()

        self.user = User.objects.create(username="pod", password="pod1234pod")
        self.v = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

    def test_index_and_delete_es(self) -> None:
        self.assertNotEqual(
            self.v.get_json_to_index(),
            "{}",
            "The test video could not be serialized. Check its related objects "
            "and the video model logs before testing Elasticsearch indexing.",
        )
        res = index_es(self.v)
        self.assertIsNotNone(
            res,
            "Elasticsearch indexing returned no response. Check ES_URL, ES_OPTIONS "
            "and the video_search logs for connection or indexing errors.",
        )
        self.assertTrue(res["result"] in ["created", "updated"])
        self.assertEqual(res["_id"], str(self.v.id))
        delete = delete_es(self.v.id)
        self.assertIsNotNone(
            delete,
            "Elasticsearch deletion returned no response. Check ES_URL, ES_OPTIONS "
            "and the video_search logs for connection or deletion errors.",
        )
        self.assertEqual(delete["result"], "deleted")
        self.assertEqual(delete["_id"], str(self.v.id))
        print("--> test_index_and_delete_es ok! ")
