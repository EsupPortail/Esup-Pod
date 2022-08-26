from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client, override_settings
from django.contrib.sites.models import Site

from http import HTTPStatus
from importlib import reload
import random

from .. import views
from ..models import Meeting


class meeting_TestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        Meeting.objects.create(id=1, name='test', owner=user)
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
        self.assertEqual(
            list(response.context["meetings"].values_list('id', flat=True)),
            list(self.user.owner_meeting.all().values_list('id', flat=True))
        )
        print(" --->  test_meeting_TestView_get_request of meeting_TestView: OK!")

    @override_settings(DEBUG=True, RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY=True)
    def test_studio_podTestView_get_request_restrict(self):
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
        self.assertEqual(
            list(response.context["meetings"].values_list('id', flat=True)),
            list(self.user.owner_meeting.all().values_list('id', flat=True))
        )
        print(
            " --->  test_studio_podTestView_get_request_restrict ",
            "of studio_podTestView: OK!",
        )


class MeetingAddEditTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        Meeting.objects.create(id=1, name='test', owner=user, site=site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of MeetingAddEditTestView: OK!")

    def test_meeting_add_edit_get_request(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        url = reverse("meeting:add", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].instance.id, None)
        self.assertEqual(response.context["form"].current_user, self.user)
        meeting = Meeting.objects.get(name='test')
        url = reverse("meeting:edit", kwargs={'meeting_id': "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        url = reverse("meeting:edit", kwargs={'meeting_id': meeting.meeting_id})
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
                "start_at_0": "2022-08-26",
                "start_at_1": "16:43:58",
                "end_at_0": "2022-08-26",
                "end_at_1": "18:43:58",
                "max_participants": 100,
                "welcome_text": "Hello"
            },
            follow=True,
        )
        self.assertTrue(b"The changes have been saved." in response.content)
        # check if meeting has been updated
        m = Meeting.objects.get(name="test1")
        self.assertEqual(m.attendee_password, "1234")
        self.assertEqual(Meeting.objects.all().count(), nb_meeting + 1)
        print("   --->  test_meeting_add_post_request of MeetingEditTestView: OK!")

    def test_meeting_edit_post_request(self):
        self.client = Client()
        meeting = Meeting.objects.get(name='test')
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        url = reverse("meeting:edit", kwargs={'meeting_id': meeting.meeting_id})
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
                "start_at_0": "2022-08-26",
                "start_at_1": "16:43:58",
                "end_at_0": "2022-08-26",
                "end_at_1": "18:43:58",
                "max_participants": 100,
                "welcome_text": "Hello"
            },
            follow=True,
        )
        self.assertTrue(b"The changes have been saved." in response.content)
        # check if meeting has been updated
        m = Meeting.objects.get(name="test1")
        self.assertEqual(m.attendee_password, "1234")
        print("   --->  test_meeting_edit_post_request of MeetingEditTestView: OK!")


class MeetingDeleteTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")
        Meeting.objects.create(id=1, name='test', owner=user, site=site)
        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()
        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()
        print(" --->  SetUp of MeetingDeleteTestView: OK!")

    def test_meeting_delete_get_request(self):
        self.client = Client()
        # check auth
        url = reverse("meeting:delete", kwargs={'meeting_id': "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # not auth
        # check meeting
        self.user = User.objects.get(username="pod2")
        self.client.force_login(self.user)
        url = reverse("meeting:delete", kwargs={'meeting_id': "slugauhasard"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # check access right
        meeting = Meeting.objects.get(name='test')
        url = reverse("meeting:delete", kwargs={'meeting_id': meeting.meeting_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("form" in response.context)

        print(" --->  test_meeting_delete_get_request of MeetingEditTestView: OK!")

    def test_meeting_delete_post_request(self):
        self.client = Client()

        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        meeting = Meeting.objects.get(name='test')
        url = reverse("meeting:delete", kwargs={'meeting_id': meeting.meeting_id})
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
        print(" --->  test_meeting_delete_post_request of MeetingEditTestView: OK!")
