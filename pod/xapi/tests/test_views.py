"""Esup-Pod Xapi views tests."""

from django.test import TestCase
from django.urls import reverse
from django.test import Client  # , override_settings
from http import HTTPStatus
import json


class xapi_statement_TestView(TestCase):
    def setUp(self):
        """Initialize the Django test client."""
        self.client = Client()
        print(" --->  SetUp of xapi_statement_TestView: OK!")

    def test_xapi_statment_TestView_get_request(self):
        bad_url = reverse("xapi:statement", kwargs={})
        response = self.client.get(bad_url)
        # need post request and video app parameter
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        good_url = reverse("xapi:statement", kwargs={"app": "video"})
        response = self.client.get(good_url)
        # video app parameter ok but need post data
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        response = self.client.post(
            good_url,
            json.dumps({}),
            "json",
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)  # 200
        self.assertEqual(response["Content-Type"], "application/json")
        response_unicode = response.content.decode("utf-8")
        data = json.loads(response_unicode)
        self.assertTrue(data["actor"]["name"] != "")
        print(
            " --->  test_xapi_statment_TestView_get_request ",
            "of xapi_statement_TestView: OK!",
        )
