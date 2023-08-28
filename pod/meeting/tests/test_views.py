"""Tests the views for meeting module."""
import random
import requests

from .. import views
from ..models import Meeting, InternalRecording
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from http import HTTPStatus
from importlib import reload
from pod.authentication.models import AccessGroup


VIDEO_TEST = getattr(settings, "VIDEO_TEST", "pod/main/static/video_test/pod.mp4")
ROOT_URLCONF = getattr(settings, "ROOT_URLCONF", "http://testserver")


class meeting_TestView(TestCase):
    """List of Meetings list View tests.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        Meeting.objects.create(id=1, name="test", owner=user)
        print(" --->  SetUp of meeting_TestView: OK!")

    def test_meeting_TestView_get_request(self):
        self.client = Client()
        url = reverse("meeting:my_meetings", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        list_id = [meeting.id for meeting in response.context["meetings"]]
        self.assertEqual(
            list_id,
            list(self.user.owner_meeting.all().values_list("id", flat=True)),
        )
        print(" --->  test_meeting_TestView_get_request of meeting_TestView: OK!")

    @override_settings(DEBUG=True, RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY=True)
    def test_meeting_TestView_get_request_restrict(self):
        reload(views)
        self.client = Client()
        url = reverse("meeting:my_meetings", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEquals(response.context["access_not_allowed"], True)
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        list_id = [meeting.id for meeting in response.context["meetings"]]
        self.assertEqual(
            list_id,
            list(self.user.owner_meeting.all().values_list("id", flat=True)),
        )
        print(
            " --->  test_meeting_TestView_get_request_restrict ",
            "of meeting_TestView: OK!",
        )


class MeetingAddEditTestView(TestCase):
    """List of tests for editing views of a meeting.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        Meeting.objects.create(id=1, name="test", owner=user, site=site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of MeetingAddEditTestView: OK!")

    def test_meeting_add_edit_get_request(self):
        self.client = Client()
        url = reverse("meeting:add", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].instance.id, None)
        self.assertEqual(response.context["form"].current_user, self.user)
        meeting = Meeting.objects.get(name="test")
        url = reverse("meeting:edit", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        url = reverse("meeting:edit", kwargs={"meeting_id": meeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["form"].instance, meeting)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        print(" --->  test_meeting_add_edit_get_request of MeetingEditTestView: OK!")

    def test_meeting_add_post_request(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        nb_meeting = Meeting.objects.all().count()
        url = reverse("meeting:add", kwargs={})
        response = self.client.post(
            url,
            {
                "name": "test1",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["form"].errors)
        response = self.client.post(
            url,
            {
                "name": "test1",
                "voice_bridge": 70000 + random.randint(0, 9999),
                "attendee_password": "1234",
                "start": "2022-08-26",
                "start_time": "21:00:00",
                "expected_duration": "2",
                "frequency": "1",
                "monthly_type": "date_day",
                "max_participants": 100,
                "welcome_text": "Hello",
            },
            follow=True,
        )
        self.assertTrue(b"The changes have been saved." in response.content)
        # check if meeting has been updated
        m = Meeting.objects.get(name="test1")
        self.assertEqual(m.attendee_password, "1234")
        self.assertEqual(Meeting.objects.all().count(), nb_meeting + 1)
        self.assertEqual(m.start_at, timezone.make_aware(datetime(2022, 8, 26, 21, 0, 0)))
        print("   --->  test_meeting_add_post_request of MeetingEditTestView: OK!")

    def test_meeting_edit_post_request(self):
        self.client = Client()
        meeting = Meeting.objects.get(name="test")
        url = reverse("meeting:edit", kwargs={"meeting_id": meeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.post(
            url,
            {
                "name": "test1",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["form"].errors)
        response = self.client.post(
            url,
            {
                "name": "test1",
                "voice_bridge": 70000 + random.randint(0, 9999),
                "attendee_password": "1234",
                "start": "2022-08-26",
                "start_time": "14:00:00",
                "expected_duration": "2",
                "frequency": "1",
                "monthly_type": "date_day",
                "max_participants": 100,
                "welcome_text": "Hello",
            },
            follow=True,
        )
        self.assertTrue(b"The changes have been saved." in response.content)
        # check if meeting has been updated
        m = Meeting.objects.get(name="test1")
        self.assertEqual(m.attendee_password, "1234")
        self.assertEqual(m.start_at, timezone.make_aware(datetime(2022, 8, 26, 14, 0, 0)))
        print("   --->  test_meeting_edit_post_request of MeetingEditTestView: OK!")


class MeetingDeleteTestView(TestCase):
    """List of tests for deleting views from a meeting.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        Meeting.objects.create(id=1, name="test", owner=user, site=site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of MeetingDeleteTestView: OK!")

    def test_meeting_delete_get_request(self):
        self.client = Client()
        # check auth
        url = reverse("meeting:delete", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth
        # check meeting
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse("meeting:delete", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # check access right
        meeting = Meeting.objects.get(name="test")
        url = reverse("meeting:delete", kwargs={"meeting_id": meeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("form" in response.context)

        print(" --->  test_meeting_delete_get_request of MeetingDeleteTestView: OK!")

    def test_meeting_delete_post_request(self):
        self.client = Client()

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        meeting = Meeting.objects.get(name="test")
        url = reverse("meeting:delete", kwargs={"meeting_id": meeting.meeting_id})
        response = self.client.post(
            url,
            {
                "name": "test1",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["form"].errors)
        response = self.client.post(
            url,
            {"agree": False},
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response.context["form"].errors)
        # check if meeting has not been deleted
        self.assertEqual(Meeting.objects.all().count(), 1)
        response = self.client.post(url, {"agree": True}, follow=True)
        self.assertTrue(b"The meeting has been deleted." in response.content)
        # check if meeting has been deleted
        self.assertEqual(Meeting.objects.all().count(), 0)
        print(" --->  test_meeting_delete_post_request of MeetingDeleteTestView: OK!")


class MeetingJoinTestView(TestCase):
    """List of view tests for joining a meeting.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        Meeting.objects.create(id=1, name="test", owner=user, site=site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of MeetingJoinTestView: OK!")

    def test_meeting_join_get_request(self):
        self.client = Client()
        # check meeting
        url = reverse("meeting:join", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)  # SuspiciousOperation
        url = reverse("meeting:join", kwargs={"meeting_id": "2-test"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)  # Not found

        meeting = Meeting.objects.get(name="test")
        self.assertEqual(meeting.is_running, False)
        url = reverse("meeting:join", kwargs={"meeting_id": meeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # meeting is not running - go to waiting room
        self.assertEqual(response.context["form"], None)

        # join as moderator to make meeting running
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        url = reverse("meeting:join", kwargs={"meeting_id": meeting.meeting_id})
        response = self.client.get(url)
        self.assertTrue(response.status_code == 302 or response.status_code == 200)
        # self.assertEqual(response.status_code, 302)  # Redirect
        # update the meeting after creating to get last info
        newmeeting = Meeting.objects.get(name="test")
        fullname = (
            self.user.get_full_name()
            if (self.user.get_full_name() != "")
            else self.user.get_username()
        )
        join_url = newmeeting.get_join_url(
            fullname, "MODERATOR", self.user.get_username()
        )
        self.assertRedirects(
            response,
            join_url,
            status_code=302,
            target_status_code=200,
            msg_prefix="",
            fetch_redirect_response=False,
        )
        # check if meeting is created, try to join it
        response = requests.get(join_url)
        self.assertEqual(response.status_code, 200)  # OK
        # fake running meeting
        newmeeting.is_running = True
        newmeeting.save()
        # Anonymous User --> ask for name and attendee_password
        self.client.logout()
        url = reverse("meeting:join", kwargs={"meeting_id": newmeeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)  # OK: NOT redirect
        self.assertTrue("form" in response.context)
        self.assertTrue("name" in response.context["form"].fields)
        self.assertTrue("password" in response.context["form"].fields)

        # check to send name and password
        response = self.client.post(
            url, {"name": "anonymous", "password": newmeeting.attendee_password}
        )
        join_url = newmeeting.get_join_url("anonymous", "VIEWER")
        self.assertRedirects(
            response,
            join_url,
            status_code=302,
            target_status_code=200,
            msg_prefix="",
            fetch_redirect_response=False,
        )

        # Authenticated User --> ask for name and attendee_password
        self.user2 = User.objects.get(username="pod2")
        self.client.force_login(self.user2)
        url = reverse("meeting:join", kwargs={"meeting_id": newmeeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)  # OK: NOT redirect
        self.assertTrue("form" in response.context)
        self.assertFalse("name" in response.context["form"].fields)
        self.assertTrue("password" in response.context["form"].fields)

        # check to send password
        response = self.client.post(
            url,
            {"password": newmeeting.attendee_password},
            # follow=True,
        )
        fullname = (
            self.user2.get_full_name()
            if (self.user2.get_full_name() != "")
            else self.user2.get_username()
        )
        join_url = newmeeting.get_join_url(fullname, "VIEWER", self.user2.get_username())
        self.assertRedirects(
            response,
            join_url,
            status_code=302,
            target_status_code=200,
            msg_prefix="",
            fetch_redirect_response=False,
        )
        # check to send bad password
        response = self.client.post(
            url,
            {"password": "bad password"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(b"Password given is not correct." in response.content)

        # meeting with restricted access
        newmeeting.is_restricted = True
        newmeeting.save()

        # Anonymous user asks to auth
        self.client.logout()
        url = reverse("meeting:join", kwargs={"meeting_id": newmeeting.meeting_id})
        response = self.client.get(url)
        redirect_url = "%s?referrer=%s" % (settings.LOGIN_URL, url)
        self.assertRedirects(
            response,
            redirect_url,
            status_code=302,
            target_status_code=302,
            msg_prefix="",
            fetch_redirect_response=True,
        )

        # Auth user can have access and ask password
        self.user2 = User.objects.get(username="pod2")
        self.client.force_login(self.user2)
        url = reverse("meeting:join", kwargs={"meeting_id": newmeeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)  # OK: NOT redirect
        self.assertTrue("form" in response.context)
        self.assertFalse("name" in response.context["form"].fields)
        self.assertTrue("password" in response.context["form"].fields)

        # restrict access to group
        ag = AccessGroup.objects.create(code_name="group1", display_name="Group 1")
        newmeeting.restrict_access_to_groups.add(ag)
        newmeeting.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # PermissionDenied
        self.assertTrue(b"You cannot access to this meeting." in response.content)

        self.user2.owner.accessgroup_set.add(ag)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)  # OK: NOT redirect
        self.assertTrue("form" in response.context)
        self.assertFalse("name" in response.context["form"].fields)
        self.assertTrue("password" in response.context["form"].fields)

        print(" --->  test_meeting_join_get_request of MeetingJoinTestView: OK!")


class MeetingStatusTestView(TestCase):
    """List of meeting status view tests.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        Meeting.objects.create(id=1, name="test", owner=user, site=site)
        print(" --->  SetUp of MeetingStatusTestView: OK!")

    def test_meeting_status_get_request(self):
        self.client = Client()
        # check meeting
        url = reverse("meeting:status", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)  # SuspiciousOperation

        meeting = Meeting.objects.get(name="test")
        self.assertEqual(meeting.is_running, False)
        url = reverse("meeting:status", kwargs={"meeting_id": meeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertJSONEqual(
            str(response.content, encoding="utf8"), {"status": meeting.is_running}
        )
        meeting.is_running = True
        meeting.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertJSONEqual(
            str(response.content, encoding="utf8"), {"status": meeting.is_running}
        )
        print(" --->  test_meeting_status_get_request of MeetingStatusTestView: OK!")


class MeetingEndTestView(TestCase):
    """List of meeting end view tests.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        Meeting.objects.create(id=1, name="test", owner=user, site=site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of MeetingEndTestView: OK!")

    def test_meeting_end_get_request(self):
        self.client = Client()
        # check auth
        url = reverse("meeting:end", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth
        # check meeting
        self.user2 = User.objects.get(username="pod2")
        self.client.force_login(self.user2)
        url = reverse("meeting:end", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # check access right with user2
        meeting = Meeting.objects.get(name="test")
        url = reverse("meeting:end", kwargs={"meeting_id": meeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # permission denied

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)

        self.assertRedirects(
            response,
            reverse("meeting:my_meetings"),
            status_code=302,
            target_status_code=200,
            msg_prefix="",
            fetch_redirect_response=True,
        )
        print(" --->  test_meeting_end_get_request of MeetingEndTestView: OK!")


class MeetingRecordingTestView(TestCase):
    """List of tests of the views of the internal recordings of a meeting.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        meeting = Meeting.objects.create(id=1, name="test", owner=user, site=site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        InternalRecording.objects.create(
            id=1,
            name="test recording1",
            recording_id="d058c39d3dc59d9e9516d95f76eb",
            meeting=meeting,
            site=site,
            owner=user,
        )
        print(" --->  SetUp of MeetingEndTestView: OK!")

    def test_meeting_recordings_get_request(self):
        self.client = Client()
        # check auth
        url = reverse(
            "meeting:internal_recordings", kwargs={"meeting_id": "slugauhasard"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth
        # check meeting
        self.user2 = User.objects.get(username="pod2")
        self.client.force_login(self.user2)
        url = reverse(
            "meeting:internal_recordings", kwargs={"meeting_id": "slugauhasard"}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # check access right with user2
        meeting = Meeting.objects.get(name="test")
        url = reverse(
            "meeting:internal_recordings", kwargs={"meeting_id": meeting.meeting_id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # permission denied

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)  # permission ok

        self.assertEqual(response.context["recordings"], [])

        print(" --->  test_meeting_recordings_get_request of MeetingEndTestView: OK!")

    def test_meeting_delete_internal_recordings_get_request(self):
        self.client = Client()
        # check auth
        url = reverse(
            "meeting:delete_internal_recording",
            kwargs={
                "meeting_id": "slugauhasard",
                "recording_id": "slugauhasard",
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth

        # check meeting
        self.user2 = User.objects.get(username="pod2")
        self.client.force_login(self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)  # not found

        # check access right with user2
        meeting = Meeting.objects.get(name="test")
        url = reverse(
            "meeting:delete_internal_recording",
            kwargs={
                "meeting_id": meeting.meeting_id,
                "recording_id": "slugauhasard",
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # permission denied

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        recording = InternalRecording.objects.get(id=1)
        url = reverse(
            "meeting:delete_internal_recording",
            kwargs={
                "meeting_id": meeting.meeting_id,
                "recording_id": recording.recording_id,
            },
        )
        # response = self.client.get(url)

        response = self.client.post(
            url,
            {},
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        print(
            " --->  test_meeting_delete_internal_recordings_get_request",
            " of MeetingEndTestView: OK!",
        )


class MeetingGetInfoTestView(TestCase):
    """List of tests for views to get information from a meeting.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        Meeting.objects.create(id=1, name="test", owner=user, site=site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of MeetingEndTestView: OK!")

    def test_meeting_get_info_get_request(self):
        self.client = Client()
        # check auth
        url = reverse("meeting:get_meeting_info", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth
        # check meeting
        self.user2 = User.objects.get(username="pod2")
        self.client.force_login(self.user2)
        url = reverse("meeting:get_meeting_info", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # check access right with user2
        meeting = Meeting.objects.get(name="test")
        url = reverse(
            "meeting:get_meeting_info", kwargs={"meeting_id": meeting.meeting_id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # permission denied

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        # meeting is not running in test, we just check that is http correct
        self.assertEqual(response.status_code, 200)
        print(" --->  test_meeting_get_info_get_request of MeetingGetInfoTestView: OK!")


class MeetingEndCallbackTestView(TestCase):
    """List of tests for views to end callback from a meeting.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        Meeting.objects.create(id=1, name="test", owner=user, site=site)
        print(" --->  SetUp of MeetingEndCallbackTestView: OK!")

    def test_meeting_end_callback_get_request(self):
        self.client = Client()
        url = reverse("meeting:end_callback", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        meeting = Meeting.objects.get(name="test")
        self.assertEqual(meeting.is_running, False)
        url = reverse("meeting:end_callback", kwargs={"meeting_id": meeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        meeting1 = Meeting.objects.get(name="test")
        self.assertEqual(meeting1.is_running, False)
        meeting1.is_running = True
        meeting1.save()
        meeting2 = Meeting.objects.get(name="test")
        self.assertEqual(meeting2.is_running, True)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        meeting3 = Meeting.objects.get(name="test")
        self.assertEqual(meeting3.is_running, False)
        msg = "--->  test_meeting_end_callback_get_request"
        msg += "of MeetingEndCallbackTestView: OK!"
        print(msg)


class MeetingInviteTestView(TestCase):
    """List of tests for views to invite users to a meeting.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        Meeting.objects.create(id=1, name="test", owner=user, site=site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of MeetingInviteTestView: OK!")

    def test_meeting_invite_get_request(self):
        self.client = Client()
        # check auth
        url = reverse("meeting:invite", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth
        # check meeting
        self.user2 = User.objects.get(username="pod2")
        self.client.force_login(self.user2)
        url = reverse("meeting:invite", kwargs={"meeting_id": "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # check access right with user2
        meeting = Meeting.objects.get(name="test")
        url = reverse("meeting:invite", kwargs={"meeting_id": meeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # permission denied

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("form" in response.context)
        self.assertTrue("emails" in response.context["form"].fields)
        msg = "--->  test_meeting_invite_get_request"
        msg += "of MeetingInviteTestView: OK!"
        print(msg)

    def test_meeting_invite_post_request(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        meeting = Meeting.objects.get(name="test")
        url = reverse("meeting:invite", kwargs={"meeting_id": meeting.meeting_id})
        emails = "test@univ.fr\n\rtest2@univ.fr, test3@univ-lille.fr test4@univ-lille.fr"
        response = self.client.post(
            url,
            {"emails": emails},
        )
        self.assertRedirects(
            response,
            reverse("meeting:my_meetings"),
            status_code=302,
            target_status_code=200,
            msg_prefix="",
            fetch_redirect_response=True,
        )
        # check if not valid email
        response = self.client.post(url, {"emails": "test@univ"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue("form" in response.context)
        self.assertTrue("emails" in response.context["form"].fields)
        self.assertTrue(response.context["form"].errors)
        msg = "--->  test_meeting_invite_post_request"
        msg += "of MeetingInviteTestView: OK!"
        print(msg)


class InternalRecordingDeleteTestView(TestCase):
    """List of view tests for deleting an internal recording.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        meeting = Meeting.objects.create(id=1, name="test", owner=user, site=site)
        InternalRecording.objects.create(
            id=1,
            name="test recording1",
            recording_id="d058c39d3dc59d9e9516d95f76eb",
            meeting=meeting,
            site=site,
            owner=user,
        )
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of InternalRecordingDeleteTestView: OK!")

    def test_recording_TestView_get_request_restrict(self):
        """Test the list of internal recordings."""
        self.client = Client()
        meeting = Meeting.objects.get(id=1)
        url = reverse(
            "meeting:internal_recordings", kwargs={"meeting_id": meeting.meeting_id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertTrue(b"Permission denied" in response.content)

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertTrue(b"Meeting recordings" in response.content)
        print(
            " --->  test_recording_TestView_get_request_restrict ",
            "of recording_TestView: OK!",
        )

    def test_recording_delete_get_request(self):
        """Test recording delete with Get request."""
        self.client = Client()
        # check auth
        url = reverse(
            "meeting:delete_internal_recording",
            kwargs={"meeting_id": "slugauhasard", "recording_id": "idauhasard"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth
        # check meeting / recording
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse(
            "meeting:delete_internal_recording",
            kwargs={"meeting_id": "slugauhasard", "recording_id": "idauhasard"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # check access right
        meeting = Meeting.objects.get(name="test")
        recording = InternalRecording.objects.get(name="test recording1")
        url = reverse(
            "meeting:delete_internal_recording",
            kwargs={
                "meeting_id": meeting.meeting_id,
                "recording_id": recording.recording_id,
            },
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        # No POST request
        self.assertEqual(response.status_code, 403)

        # With POST, good user, good URL
        response = self.client.post(
            url,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        print(" --->  test_recording_delete_get_request of RecordingDeleteTestView: OK!")


class InternalRecordingUploadTestView(TestCase):
    """List of view tests for upload to Pod an internal recording.

    Args:
        TestCase (class): test case
    """

    def setUp(self):
        """Setup for tests views."""
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user.save()
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        user2.save()
        meeting = Meeting.objects.create(id=1, name="test", owner=user, site=site)
        InternalRecording.objects.create(
            id=1,
            name="test recording1",
            recording_id="d058c39d3dc59d9e9516d95f76eb",
            meeting=meeting,
            site=site,
            owner=user,
        )
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of InternalRecordingUploadTestView: OK!")

    def test_recording_upload_get_request(self):
        """Test recording upload with Get request."""
        self.client = Client()
        # check auth
        url = reverse(
            "meeting:upload_internal_recording_to_pod",
            kwargs={"meeting_id": "slugauhasard", "recording_id": "idauhasard"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth
        # check meeting / recording
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse(
            "meeting:upload_internal_recording_to_pod",
            kwargs={"meeting_id": "slugauhasard", "recording_id": "idauhasard"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # check access right
        meeting = Meeting.objects.get(name="test")
        recording = InternalRecording.objects.get(name="test recording1")
        url = reverse(
            "meeting:upload_internal_recording_to_pod",
            kwargs={
                "meeting_id": meeting.meeting_id,
                "recording_id": recording.recording_id,
            },
        )
        # Get Request
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_recording_upload_post_request(self):
        """Test recording upload with Post request."""
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        meeting = Meeting.objects.get(name="test")
        url = reverse(
            "meeting:upload_internal_recording_to_pod",
            kwargs={
                "meeting_id": meeting.meeting_id,
                "recording_id": "e058c39d3dc59d9e9516d95f76eb",
            },
        )

        # Check upload to Pod for internal recording
        response = self.client.post(
            url,
            {"recording_name": "test recording2", "source_url": "pod.mp4"},
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        print(" --->  test_recording_upload_get_request of RecordingUploadTestView: OK!")
