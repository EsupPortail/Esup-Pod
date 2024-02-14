import json

from . import ActivityPubTestCase
from unittest.mock import patch
import httmock
from pod.activitypub.models import Following
from pod.activitypub.models import ExternalVideo
from pod.activitypub.deserialization.video import create_external_video


class AdminActivityPubTestCase(ActivityPubTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin_user)

    def test_send_federation_request(self):
        """Nominal case test for the admin 'send_federation_request' action."""

        with httmock.HTTMock(
            self.mock_nodeinfo, self.mock_application_actor, self.mock_inbox
        ):
            response = self.client.post(
                "/admin/activitypub/following/",
                {
                    "action": "send_federation_request",
                    "_selected_action": [
                        str(self.peertube_test_following.id),
                    ],
                },
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(list(response.context["messages"])[0]),
            "The federation requests have been sent",
        )

        self.peertube_test_following.refresh_from_db()
        self.assertEqual(
            self.peertube_test_following.status, Following.Status.REQUESTED
        )

    def test_reindex_external_videos(self):
        """Nominal case test for the admin 'reindex_external_videos' action."""

        with (
            httmock.HTTMock(
                self.mock_nodeinfo,
                self.mock_application_actor,
                self.mock_outbox,
                self.mock_get_video,
            ),
            patch(
                "pod.activitypub.network.index_external_videos"
            ) as index_external_videos,
        ):
            response = self.client.post(
                "/admin/activitypub/following/",
                {
                    "action": "reindex_external_videos",
                    "_selected_action": [
                        str(self.peertube_test_following.id),
                    ],
                },
                follow=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                str(list(response.context["messages"])[0]),
                "The video indexations have started",
            )
            self.assertTrue(index_external_videos.called)

    def test_check_missing_external_videos_are_deleted_on_reindexation(self):
        """Reindexation should delete missing ExternalVideo on following instance."""

        with open("pod/activitypub/tests/fixtures/peertube_video.json") as fd:
            payload = json.load(fd)
        video = create_external_video(
            payload, source_instance=self.peertube_test_following
        )

        with open("pod/activitypub/tests/fixtures/peertube_video_second.json") as fd:
            video_to_delete_payload = json.load(fd)
        video_to_delete = create_external_video(
            video_to_delete_payload, source_instance=self.peertube_test_following
        )
        self.assertEqual(
            video_to_delete, ExternalVideo.objects.get(id=video_to_delete.id)
        )

        with httmock.HTTMock(
            self.mock_nodeinfo,
            self.mock_application_actor,
            self.mock_outbox,
            self.mock_get_video,
        ):
            response = self.client.post(
                "/admin/activitypub/following/",
                {
                    "action": "reindex_external_videos",
                    "_selected_action": [
                        str(self.peertube_test_following.id),
                    ],
                },
                follow=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                str(list(response.context["messages"])[0]),
                "The video indexations have started",
            )
            self.assertEqual(video.ap_id, ExternalVideo.objects.get(id=video.id).ap_id)
            self.assertRaises(
                ExternalVideo.DoesNotExist,
                ExternalVideo.objects.get,
                id=video_to_delete.id,
            )
