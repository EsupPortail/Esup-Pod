import json

import httmock
from django.test import TestCase
from pod.authentication.models import User


class ActivityPubTestCase(TestCase):
    """ActivityPub test case."""

    maxDiff = None
    fixtures = ["initial_data.json"]
    headers = {
        "HTTP_ACCEPT": "application/activity+json, application/ld+json",
    }

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            first_name="Super",
            last_name="User",
            password="SuperPassword1234",
        )

    def tearDown(self):
        del self.admin_user

    @httmock.urlmatch(path=r"^/.well-known/nodeinfo$")
    def mock_nodeinfo(self, url, request):
        with open("pod/activitypub/tests/fixtures/nodeinfo.json") as fd:
            payload = json.load(fd)

        return httmock.response(200, payload)

    @httmock.urlmatch(path=r"^/accounts/peertube$")
    def mock_application_actor(self, url, request):
        with open("pod/activitypub/tests/fixtures/application_actor.json") as fd:
            payload = json.load(fd)

        return httmock.response(200, payload)

    @httmock.urlmatch(path=r"^/accounts/peertube/inbox$")
    def mock_inbox(self, url, request):
        return httmock.response(204, "")

    @httmock.urlmatch(path=r"^/accounts/peertube/outbox$")
    def mock_outbox(self, url, request):
        if url.query == "page=1":
            fixture = "pod/activitypub/tests/fixtures/outbox-page-1.json"
        else:
            fixture = "pod/activitypub/tests/fixtures/outbox.json"

        with open(fixture) as fd:
            payload = json.load(fd)

        return httmock.response(200, payload)

    @httmock.urlmatch(path=r"^/videos/watch.*")
    def mock_get_video(self, url, request):
        with open("pod/activitypub/tests/fixtures/peertube_video.json") as fd:
            payload = json.load(fd)

        return httmock.response(200, payload)

    @httmock.urlmatch(path=r"^/video-channels/.*")
    def mock_get_channel(self, url, request):
        with open("pod/activitypub/tests/fixtures/channel.json") as fd:
            payload = json.load(fd)

        return httmock.response(200, payload)
