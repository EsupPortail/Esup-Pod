"""Esup-Pod - Regression tests for joining a webinar from multiple browsers."""

from unittest.mock import patch

import requests
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import Client, TestCase
from django.urls import reverse

from pod.live.models import Broadcaster, Building
from pod.meeting.models import LiveGateway, Livestream, Meeting, MeetingSessionLog
from pod.meeting.webinar_utils import manage_webinar
from pod.video.models import Type


class WebinarJoinTests(TestCase):
    """Exercise real join views with mocked BBB and SIPMediaGW services."""

    def setUp(self):
        self.user = User.objects.create_user(username="webinar_owner")
        site = Site.objects.get_current()
        self.user.owner.sites.add(site)
        self.meeting = Meeting.objects.create(
            name="Webinar", owner=self.user, site=site, is_webinar=True
        )
        Type.objects.create(id=1, title="Webinar")
        building = Building.objects.create(name="Building")
        broadcaster = Broadcaster.objects.create(
            name="Broadcaster", building=building, url="https://media.example.com/live"
        )
        gateway = LiveGateway.objects.create(
            broadcaster=broadcaster,
            site=site,
            sipmediagw_server_url="https://gateway.example.com",
        )
        manage_webinar(self.meeting, True, gateway)
        self.livestream = Livestream.objects.get(meeting=self.meeting)
        self.url = reverse("meeting:join", args=[self.meeting.meeting_id])
        self.client.force_login(self.user)
        self.other_browser = Client()
        self.other_browser.force_login(self.user)

        self.gateway_get = self.enterContext(patch("pod.meeting.webinar.requests.get"))
        self.gateway_get.return_value.text = '{"status": "success", "res": "ok"}'
        self.stop_thread = self.enterContext(
            patch("pod.meeting.webinar.threading.Thread")
        )
        self.enterContext(
            patch.object(
                Meeting,
                "get_is_meeting_running",
                autospec=True,
                side_effect=lambda meeting: meeting.is_running,
            )
        )
        self.create_meeting = self.enterContext(
            patch.object(Meeting, "create", autospec=True, side_effect=self.create_bbb)
        )
        self.enterContext(
            patch.object(
                Meeting, "get_join_url", return_value="https://bbb.example.com/join"
            )
        )

    def create_bbb(self, meeting, request):
        """Record a successful BBB creation without contacting an external service."""
        meeting.is_running = True
        meeting.save()
        return True

    def assert_joined(self, client):
        """Check that a browser can still enter the BBB meeting as a moderator."""
        response = client.get(self.url)
        self.assertRedirects(
            response, "https://bbb.example.com/join", fetch_redirect_response=False
        )

    def gateway_actions(self):
        """Return the gateway endpoints called in order."""
        return [
            call.args[0].rsplit("/", 1)[-1] for call in self.gateway_get.call_args_list
        ]

    def test_owner_rejoins_from_another_browser_without_gateway_requests(self):
        """Start and configure the gateway only once, with either chat setting."""
        for enable_chat in (False, True):
            with self.subTest(enable_chat=enable_chat):
                self.meeting.enable_chat = enable_chat
                self.meeting.save(update_fields=["enable_chat"])
                self.livestream.status = 0
                self.livestream.save()
                self.gateway_get.reset_mock()
                self.stop_thread.reset_mock()

                self.assert_joined(self.client)
                actions = ["start"] if enable_chat else ["start", "chat"]
                self.assertEqual(self.gateway_actions(), actions)
                self.assert_joined(self.other_browser)
                self.assert_joined(self.client)

                self.assertEqual(self.gateway_actions(), actions)
                self.stop_thread.assert_called_once()
                self.stop_thread.return_value.start.assert_called_once()
                self.livestream.refresh_from_db()
                self.assertEqual(self.livestream.status, 1)

        self.create_meeting.assert_called_once()
        session = MeetingSessionLog.objects.get(meeting=self.meeting)
        self.assertEqual(len(session.get_moderators()), 6)

    def test_owner_can_start_live_after_another_moderator_started_bbb(self):
        """A running BBB meeting can still need its first gateway startup."""
        self.meeting.is_running = True
        self.meeting.save()
        MeetingSessionLog.objects.create(meeting=self.meeting, creator=self.user)

        self.assert_joined(self.client)

        self.create_meeting.assert_not_called()
        self.assertEqual(self.gateway_actions(), ["start", "chat"])

    def test_failed_gateway_start_can_be_retried_from_another_browser(self):
        """A failed start must not leave the livestream marked as running."""
        self.gateway_get.side_effect = requests.RequestException("Gateway unavailable")

        self.assert_joined(self.client)

        self.livestream.refresh_from_db()
        self.assertEqual(self.livestream.status, 0)
        self.stop_thread.assert_not_called()
        self.gateway_get.side_effect = None
        self.gateway_get.reset_mock()

        self.assert_joined(self.other_browser)

        self.assertEqual(self.gateway_actions(), ["start", "chat"])
        self.livestream.refresh_from_db()
        self.assertEqual(self.livestream.status, 1)

    def test_explicit_restart_still_restarts_the_gateway(self):
        """The restart action must stop the active gateway before starting it again."""
        self.assert_joined(self.client)
        self.gateway_get.reset_mock()

        response = self.other_browser.get(
            reverse("meeting:restart_live", args=[self.meeting.meeting_id])
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.gateway_actions(), ["stop", "start", "chat"])
        self.assertEqual(self.stop_thread.call_count, 2)
        self.livestream.refresh_from_db()
        self.assertEqual(self.livestream.status, 1)

    def test_stopped_livestream_can_start_again(self):
        """Only an active livestream should suppress automatic startup."""
        self.livestream.status = 2
        self.livestream.save()

        self.assert_joined(self.client)

        self.assertEqual(self.gateway_actions(), ["start", "chat"])
        self.livestream.refresh_from_db()
        self.assertEqual(self.livestream.status, 1)

    def test_regular_meeting_does_not_call_the_gateway(self):
        """Keep ordinary moderator joins independent of SIPMediaGW."""
        self.meeting.is_webinar = False
        self.meeting.save()

        self.assert_joined(self.client)
        self.assert_joined(self.other_browser)

        self.gateway_get.assert_not_called()
        self.stop_thread.assert_not_called()
