from django.test import TestCase
from django.urls import reverse
from django.test import Client  # , override_settings
from http import HTTPStatus
import json


class xapi_statement_TestView(TestCase):
    def setUp(self):
        """initialize the Django test client"""
        self.client = Client()
        print(" --->  SetUp of xapi_statement_TestView: OK!")

    def test_xapi_statment_TestView_get_request(self):
        
        bad_url = reverse("xapi:statement", kwargs={})
        response = self.client.get(bad_url)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST) # need post request and video app parameter

        good_url = reverse("xapi:statement", kwargs={"app":"video"})
        response = self.client.get(good_url)
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST) # need post request 

        response = self.client.post(
            good_url,
            json.dumps({}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, HTTPStatus.OK) # ok

        """
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        list_id = [meeting.id for meeting in response.context["meetings"]]
        self.assertEqual(
            list_id,
            list(self.user.owner_meeting.all().values_list("id", flat=True)),
        )
        """
        print(" --->  test_xapi_statment_TestView_get_request of xapi_statement_TestView: OK!")