"""Tests utils for meeting module, useful for webinar."""

from ..models import Meeting
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from pod.authentication.models import AccessGroup
from pod.live.models import Building, Broadcaster
from pod.meeting.models import LiveGateway
from pod.meeting.webinar import (
    chat_rtmp_gateway,
    start_webinar_livestream,
    stop_webinar_livestream,
    toggle_rtmp_gateway,
)
from pod.meeting.webinar_utils import manage_webinar
from pod.video.models import Type


class MeetingTestUtils(TestCase):
    """Meetings utils tests list.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        AccessGroup.objects.create(code_name="faculty", display_name="Group Faculty")
        # User with faculty affiliation
        user_faculty = User.objects.create(
            username="pod_faculty", password="pod1234pod", email="pod@univ.fr"
        )
        user_faculty.owner.auth_type = "CAS"
        user_faculty.owner.affiliation = "faculty"
        user_faculty.owner.sites.add(Site.objects.get_current())
        user_faculty.owner.accessgroup_set.add(
            AccessGroup.objects.get(code_name="faculty")
        )
        user_faculty.owner.save()

        Meeting.objects.create(
            id=1,
            name="webinar_faculty",
            owner=user_faculty,
            site=site,
            is_webinar=True,
        )

        # Default event type
        Type.objects.create(title="type1")

        # Create a broadcaster
        building = Building.objects.create(name="building1")
        broadcaster = Broadcaster.objects.create(
            name="broadcaster1",
            url="http://test.live",
            status=True,
            enable_add_event=True,
            is_restricted=True,
            building=building,
        )
        # Create a live gateway
        LiveGateway.objects.create(
            id=1,
            rtmp_stream_url="rtmp://127.0.0.1:1935/live/sipmediagw",
            broadcaster=broadcaster,
            site=site,
        )

        print(" --->  SetUp of MeetingTestUtils: OK!")

    def test_sipmediagw_commands1(self):
        """Check start and stop SIPMediaGW commands (on 127.0.0.1, so management of exceptions)."""
        meeting = Meeting.objects.get(id=1)
        live_gateway = LiveGateway.objects.get(id=1)
        # Manage the livestream and the event when the webinar is created
        manage_webinar(meeting, True, live_gateway)
        # Start
        try:
            start_webinar_livestream("https://127.0.0.1", 1)
        except ValueError as ve:
            self.assertTrue("/start?room=" in str(ve))
            self.assertTrue(
                "&domain=https%3A%2F%2F127.0.0.1%2Fmeeting%2F0001-webinar_faculty"
                in str(ve)
            )
        # Stop
        try:
            stop_webinar_livestream(1, True)
        except ValueError as ve:
            self.assertTrue("/stop?room=" in str(ve))
        print("   --->  test_sipmediagw_commands1 of MeetingTestUtils: OK!")

    def test_sipmediagw_commands2(self):
        """Check chat and toggle SIPMediaGW commands (on 127.0.0.1, so management of exceptions)."""
        meeting = Meeting.objects.get(id=1)
        live_gateway = LiveGateway.objects.get(id=1)
        # Manage the livestream and the event when the webinar is created
        manage_webinar(meeting, True, live_gateway)
        # Toggle
        try:
            toggle_rtmp_gateway(1)
        except Exception as e:
            self.assertTrue("&toggle=True" in str(e))
        # Chat
        try:
            chat_rtmp_gateway(1, "Message")
        except Exception as e:
            self.assertTrue("/chat" in str(e))
        print("   --->  test_sipmediagw_commands2 of MeetingTestUtils: OK!")
