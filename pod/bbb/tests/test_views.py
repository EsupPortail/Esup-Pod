"""
Unit tests for BBB views
"""

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from ..models import BBB_Meeting as Meeting, Attendee, Livestream
from django.utils import timezone


class MeetingViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        meeting1 = Meeting.objects.create(
            id=1,
            meeting_id="id1",
            internal_meeting_id="internalid1",
            meeting_name="Session BBB1",
            recorded=True,
            recording_available=True,
            encoding_step=0,
        )
        userJohnDoe = User.objects.create(username="pod")
        Attendee.objects.create(
            id=1,
            full_name="John Doe",
            role="MODERATOR",
            username="pod",
            meeting=meeting1,
            user=userJohnDoe,
        )
        print(" --->  SetUp of MeetingViewsTestCase : OK !")

    def test_list_meeting(self):
        self.client = Client()
        response = self.client.get("/bbb/list_meeting/")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get("/bbb/list_meeting/")
        self.assertTrue(b"Session BBB1" in response.content)
        self.assertEqual(response.status_code, 200)

        print("   --->  test_list_meeting of MeetingViewsTestCase : OK !")

    def test_publish_meeting(self):
        self.client = Client()
        response = self.client.get("/bbb/publish_meeting/1")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="pod")
        self.user.is_staff = True
        self.user.save()

        response = self.client.post("/bbb/publish_meeting/1")
        # Possible status : 200 or 301
        if response.status_code == 200:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 301)
        print("   --->  test_publish_meeting of MeetingViewsTestCase : OK !")


class LivestreamViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        meeting1 = Meeting.objects.create(
            id=1,
            meeting_id="id1",
            internal_meeting_id="internalid1",
            meeting_name="Session BBB1",
            session_date=timezone.now(),
            encoding_step=0,
        )
        userJohnDoe = User.objects.create(username="john.doe")
        Attendee.objects.create(
            id=1,
            full_name="John Doe",
            role="MODERATOR",
            username="john.doe",
            meeting=meeting1,
            user=userJohnDoe,
        )

        Livestream.objects.create(
            id=1,
            start_date=timezone.now(),
            meeting=meeting1,
            status=0,
            user=userJohnDoe,
        )
        print(" --->  SetUp of LivestreamViewsTestCase : OK !")

    def test_live_list_meeting(self):
        self.client = Client()
        response = self.client.get("/bbb/live_list_meeting/")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="john.doe")
        self.user.is_staff = True
        self.user.save()

        self.client.force_login(self.user)
        response = self.client.get("/bbb/live_list_meeting/")
        self.assertTrue(b"Session BBB1" in response.content)
        self.assertEqual(response.status_code, 200)

        print("   ---> test_live_list_meeting of LivestreamViewsTestCase : OK !")

    def test_live_publish_meeting(self):
        self.client = Client()
        response = self.client.get("/bbb/live_publish_meeting/1")
        self.assertRaises(PermissionDenied)

        self.user = User.objects.get(username="john.doe")
        self.user.is_staff = True
        self.user.save()

        response = self.client.post("/bbb/live_publish_meeting/1")
        # Possible status : 200 or 301
        if response.status_code == 200:
            self.assertEqual(response.status_code, 200)
        else:
            self.assertEqual(response.status_code, 301)
        print("   ---> test_live_publish_meeting of LivestreamViewsTestCase:OK!")
