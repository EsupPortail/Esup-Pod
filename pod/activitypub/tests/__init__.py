import json
import os
import httmock

from datetime import datetime
from zoneinfo import ZoneInfo
from django.template.defaultfilters import slugify
from django.test import TestCase
from django.conf import settings

from pod.authentication.models import User
from pod.video.models import VIDEOS_DIR
from pod.video.models import Video
from pod.video.models import Type
from pod.video_encode_transcript.models import VideoRendition
from pod.video_encode_transcript.models import EncodingVideo
from pod.activitypub.models import Following

TIME_ZONE = getattr(settings, "TIME_ZONE", "Europe/Paris")


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
        video_type = Type.objects.create(title="autre")
        filename = "test.mp4"
        fname, dot, extension = filename.rpartition(".")
        self.vr = VideoRendition.objects.get(resolution="640x360")
        self.draft_video = Video.objects.create(
            type=video_type,
            title="Draft video",
            password=None,
            date_added=datetime.now(ZoneInfo(TIME_ZONE)),
            encoding_in_progress=False,
            owner=self.admin_user,
            date_evt=datetime.now(ZoneInfo(TIME_ZONE)),
            video=os.path.join(
                VIDEOS_DIR,
                self.admin_user.owner.hashkey,
                "%s.%s" % (slugify(fname), extension),
            ),
            description="description",
            is_draft=True,
            duration=3,
        )
        self.ev_draft = EncodingVideo.objects.create(
            video=self.draft_video,
            rendition=self.vr,
        )
        self.visible_video = Video.objects.create(
            type=video_type,
            title="Visible video",
            password=None,
            date_added=datetime.now(ZoneInfo(TIME_ZONE)),
            encoding_in_progress=False,
            owner=self.admin_user,
            date_evt=datetime.now(ZoneInfo(TIME_ZONE)),
            video=os.path.join(
                VIDEOS_DIR,
                self.admin_user.owner.hashkey,
                "%s.%s" % (slugify(fname), extension),
            ),
            description="description",
            is_draft=False,
            duration=3,
        )
        self.ev_visible = EncodingVideo.objects.create(
            video=self.visible_video,
            rendition=self.vr,
        )
        self.peertube_test_following = Following.objects.create(
            object="http://peertube.test", status=Following.Status.ACCEPTED
        )
        self.other_peertube_test_following = Following.objects.create(
            object="http://other_peertube.test", status=Following.Status.ACCEPTED
        )

    def tearDown(self):
        del self.admin_user
        del self.draft_video
        del self.visible_video
        del self.vr
        del self.ev_draft
        del self.ev_visible

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
