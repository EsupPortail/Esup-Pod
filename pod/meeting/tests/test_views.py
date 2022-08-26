from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client, override_settings

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
        self.create_index_file()
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
