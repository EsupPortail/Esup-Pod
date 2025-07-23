import json

import httmock

from . import ActivityPubTestCase
from pod.activitypub.models import ExternalVideo
from pod.activitypub.models import Following


class VideoUpdateTest(ActivityPubTestCase):
    def test_video_creation(self):
        """Test video creation activities on the inbox.

        When a Video is created on peertube, it sends several announces:
        - one for the video creation on the meta account;
        - one for the video creation on the user profile;
        - one for the video addition on the user channel.

        This tests the situation where the account announce is received first.
        """

        assert len(ExternalVideo.objects.all()) == 0

        with open(
            "pod/activitypub/tests/fixtures/video_creation_account_announce.json"
        ) as fd:
            account_announce_payload = json.load(fd)

        assert not len(ExternalVideo.objects.all())

        with httmock.HTTMock(self.mock_application_actor, self.mock_get_video):
            response = self.client.post(
                "/ap/inbox",
                json.dumps(account_announce_payload),
                content_type="application/json",
                **self.headers,
            )
            self.assertEqual(response.status_code, 204)

        assert len(ExternalVideo.objects.all()) == 1

        with open(
            "pod/activitypub/tests/fixtures/video_creation_channel_announce.json"
        ) as fd:
            channel_announce_payload = json.load(fd)

        with httmock.HTTMock(self.mock_get_channel, self.mock_get_video):
            response = self.client.post(
                "/ap/inbox",
                json.dumps(channel_announce_payload),
                content_type="application/json",
                **self.headers,
            )
            self.assertEqual(response.status_code, 204)

        assert len(ExternalVideo.objects.all()) == 1

    def test_video_creation_fails_for_unfollowed_instance(self):
        """Test video creation activities are ignored for unfollowed instances"""

        assert len(ExternalVideo.objects.all()) == 0

        self.peertube_test_following.status = Following.Status.NONE
        self.peertube_test_following.save()

        with open(
            "pod/activitypub/tests/fixtures/video_creation_account_announce.json"
        ) as fd:
            account_announce_payload = json.load(fd)

        assert not len(ExternalVideo.objects.all())

        with httmock.HTTMock(self.mock_application_actor, self.mock_get_video):
            response = self.client.post(
                "/ap/inbox",
                json.dumps(account_announce_payload),
                content_type="application/json",
                **self.headers,
            )
            self.assertEqual(response.status_code, 204)

        assert len(ExternalVideo.objects.all()) == 0

        with open(
            "pod/activitypub/tests/fixtures/video_creation_channel_announce.json"
        ) as fd:
            channel_announce_payload = json.load(fd)

        with httmock.HTTMock(self.mock_get_channel, self.mock_get_video):
            response = self.client.post(
                "/ap/inbox",
                json.dumps(channel_announce_payload),
                content_type="application/json",
                **self.headers,
            )
            self.assertEqual(response.status_code, 204)

        assert len(ExternalVideo.objects.all()) == 0

    def test_video_view(self):
        """Test that View activities are ignored"""

        with open("pod/activitypub/tests/fixtures/video_view.json") as fd:
            payload = json.load(fd)

        self.client.post(
            "/ap/inbox",
            json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )

    def test_video_update(self):
        """Test the video update activity on the inbox"""

        with open(
            "pod/activitypub/tests/fixtures/video_creation_account_announce.json"
        ) as fd:
            account_announce_payload = json.load(fd)

        assert not len(ExternalVideo.objects.all())

        with httmock.HTTMock(self.mock_application_actor, self.mock_get_video):
            response = self.client.post(
                "/ap/inbox",
                json.dumps(account_announce_payload),
                content_type="application/json",
                **self.headers,
            )
            self.assertEqual(response.status_code, 204)

        assert ExternalVideo.objects.first().title == "Titre de la vidéo"

        with open("pod/activitypub/tests/fixtures/video_update.json") as fd:
            payload = json.load(fd)

        response = self.client.post(
            "/ap/inbox",
            json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )
        self.assertEqual(response.status_code, 204)

        assert ExternalVideo.objects.first().title == "terre"

    def test_video_update_fails_for_unfollowed_instance(self):
        """Test the video update forbidden for unfollowed instances"""

        with open(
            "pod/activitypub/tests/fixtures/video_creation_account_announce.json"
        ) as fd:
            account_announce_payload = json.load(fd)

        assert not len(ExternalVideo.objects.all())

        with httmock.HTTMock(self.mock_application_actor, self.mock_get_video):
            self.client.post(
                "/ap/inbox",
                json.dumps(account_announce_payload),
                content_type="application/json",
                **self.headers,
            )

        assert ExternalVideo.objects.first().title == "Titre de la vidéo"

        self.peertube_test_following.status = Following.Status.NONE
        self.peertube_test_following.save()

        with open("pod/activitypub/tests/fixtures/video_update.json") as fd:
            payload = json.load(fd)

        self.client.post(
            "/ap/inbox",
            json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )

        assert ExternalVideo.objects.first().title == "Titre de la vidéo"

    def test_video_update_fails_for_unrelated_instance(self):
        """Test the video update forbidden for unrelated instances"""

        with open(
            "pod/activitypub/tests/fixtures/video_creation_account_announce.json"
        ) as fd:
            account_announce_payload = json.load(fd)

        assert not len(ExternalVideo.objects.all())

        with httmock.HTTMock(self.mock_application_actor, self.mock_get_video):
            self.client.post(
                "/ap/inbox",
                json.dumps(account_announce_payload),
                content_type="application/json",
                **self.headers,
            )

        assert ExternalVideo.objects.first().title == "Titre de la vidéo"

        with open("pod/activitypub/tests/fixtures/video_update_not_owner.json") as fd:
            payload = json.load(fd)

        self.client.post(
            "/ap/inbox",
            json.dumps(payload),
            content_type="application/json",
            **self.headers,
        )

        assert ExternalVideo.objects.first().title == "Titre de la vidéo"

    def test_video_delete(self):
        """Test the video delete activity on the inbox"""

        with open(
            "pod/activitypub/tests/fixtures/video_creation_account_announce.json"
        ) as fd:
            account_announce_payload = json.load(fd)

        assert not len(ExternalVideo.objects.all())

        with httmock.HTTMock(self.mock_application_actor, self.mock_get_video):
            response = self.client.post(
                "/ap/inbox",
                json.dumps(account_announce_payload),
                content_type="application/json",
                **self.headers,
            )
            self.assertEqual(response.status_code, 204)

        assert len(ExternalVideo.objects.all()) == 1

        with open("pod/activitypub/tests/fixtures/video_delete.json") as fd:
            payload = json.load(fd)

        with httmock.HTTMock(self.mock_get_video):
            response = self.client.post(
                "/ap/inbox",
                json.dumps(payload),
                content_type="application/json",
                **self.headers,
            )
            self.assertEqual(response.status_code, 204)

        assert not len(ExternalVideo.objects.all())

    def test_video_delete_fails_for_unfollowed_instance(self):
        """Test video deletion forbidden for unfollowed instances"""

        self.other_peertube_test_following.delete()

        with open(
            "pod/activitypub/tests/fixtures/video_creation_account_announce.json"
        ) as fd:
            account_announce_payload = json.load(fd)

        assert not len(ExternalVideo.objects.all())

        with httmock.HTTMock(self.mock_application_actor, self.mock_get_video):
            self.client.post(
                "/ap/inbox",
                json.dumps(account_announce_payload),
                content_type="application/json",
                **self.headers,
            )

        assert len(ExternalVideo.objects.all()) == 1

        self.peertube_test_following.status = Following.Status.NONE
        self.peertube_test_following.save()

        with open("pod/activitypub/tests/fixtures/video_delete.json") as fd:
            payload = json.load(fd)

        with httmock.HTTMock(self.mock_get_video):
            self.client.post(
                "/ap/inbox",
                json.dumps(payload),
                content_type="application/json",
                **self.headers,
            )

        assert len(ExternalVideo.objects.all()) == 1

    def test_video_delete_fails_for_unrelated_instance(self):
        """Test video deletion forbidden for unrelated instances"""

        with open(
            "pod/activitypub/tests/fixtures/video_creation_account_announce.json"
        ) as fd:
            account_announce_payload = json.load(fd)

        assert not len(ExternalVideo.objects.all())

        with httmock.HTTMock(self.mock_application_actor, self.mock_get_video):
            self.client.post(
                "/ap/inbox",
                json.dumps(account_announce_payload),
                content_type="application/json",
                **self.headers,
            )

        assert len(ExternalVideo.objects.all()) == 1

        with open("pod/activitypub/tests/fixtures/video_delete_not_owner.json") as fd:
            payload = json.load(fd)

        with httmock.HTTMock(self.mock_get_video):
            self.client.post(
                "/ap/inbox",
                json.dumps(payload),
                content_type="application/json",
                **self.headers,
            )

        assert len(ExternalVideo.objects.all()) == 1
