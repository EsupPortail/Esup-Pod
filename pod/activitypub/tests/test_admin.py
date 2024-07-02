from . import ActivityPubTestCase
from unittest.mock import patch
import httmock
from pod.activitypub.models import Following


class AdminActivityPubTestCase(ActivityPubTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin_user)

    def test_send_federation_request(self):
        """Nominal case test for the admin 'send_federation_request' action."""

        following = Following.objects.create(
            object="http://peertube.test", status=Following.Status.NONE
        )

        with httmock.HTTMock(
            self.mock_nodeinfo, self.mock_application_actor, self.mock_inbox
        ):
            response = self.client.post(
                "/admin/activitypub/following/",
                {
                    "action": "send_federation_request",
                    "_selected_action": [
                        str(following.id),
                    ],
                },
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            str(list(response.context["messages"])[0]),
            "The federation requests have been sent",
        )

        following.refresh_from_db()
        self.assertEqual(following.status, Following.Status.REQUESTED)

    def test_reindex_videos(self):
        """Nominal case test for the admin 'reindex_videos' action."""

        following = Following.objects.create(
            object="http://peertube.test", status=Following.Status.NONE
        )

        with httmock.HTTMock(
            self.mock_nodeinfo,
            self.mock_application_actor,
            self.mock_outbox,
            self.mock_get_video,
        ), patch(
            "pod.activitypub.network.ap_video_to_external_video"
        ) as ap_video_to_external_video:
            response = self.client.post(
                "/admin/activitypub/following/",
                {
                    "action": "reindex_videos",
                    "_selected_action": [
                        str(following.id),
                    ],
                },
                follow=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                str(list(response.context["messages"])[0]),
                "The video indexations have started",
            )
            self.assertTrue(ap_video_to_external_video.called)
