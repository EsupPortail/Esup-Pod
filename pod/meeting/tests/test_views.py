from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client, override_settings
from django.contrib.sites.models import Site

from http import HTTPStatus
from importlib import reload

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
        self.assertEqual(response.context["meetings"], self.user.owner_meeting.all())
        print(" --->  test_meeting_TestView_get_request of meeting_TestView: OK!")

    @override_settings(DEBUG=True, RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=True)
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
        self.assertEqual(response.context["meetings"], self.user.owner_meeting.all())
        print(
            " --->  test_studio_podTestView_get_request_restrict ",
            "of studio_podTestView: OK!",
        )


class MeetingEditTestView(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        site = Site.objects.get(id=1)
        user = User.objects.create(username="pod", password="pod1234pod")
        user2 = User.objects.create(username="pod2", password="pod1234pod")

        user = User.objects.create(username="pod", password="pod1234pod")
        Meeting.objects.create(id=1, name='test', owner=user, site=site)
        print(" --->  SetUp of meeting_TestView: OK!")

        user.owner.sites.add(Site.objects.get_current())
        user.owner.save()

        user2.owner.sites.add(Site.objects.get_current())
        user2.owner.save()

        print(" --->  SetUp of MeetingEditTestView: OK!")

    def test_meeting_edit_get_request(self):
        self.client = Client()
        meeting = Meeting.objects.get(name='test')
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
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
        print(" --->  test_meeting_edit_get_request of MeetingEditTestView: OK!")

    def test_meeting_edit_post_request(self):
        self.client = Client()
        meeting = Meeting.objects.get(name='test')
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        url = reverse("meeting:edit", kwargs={'meeting_id': meeting.meeting_id})
        response = self.client.post(
            url,
            {"name": "test1"},
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(b"The changes have been saved." in response.content)
        Meeting.objects.get(name="test1")
        print("   --->  test_meeting_edit_post_request of MeetingEditTestView: OK!")
