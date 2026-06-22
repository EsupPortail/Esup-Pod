"""Esup-Pod Xapi views tests."""

import json
from http import HTTPStatus
from pathlib import Path

from django.conf import settings
from django.test import Client  # , override_settings
from django.test import TestCase
from django.urls import reverse


class xapi_statement_TestView(TestCase):
    """Tests for Xapi statement endpoints and client-side helpers."""

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

    def test_xapi_script_uses_secure_uuid_randomness(self):
        """Test that the xAPI script uses secure browser randomness for UUIDs."""
        script_path = Path(settings.BASE_DIR) / "xapi" / "static" / "xapi" / "script.js"
        script_content = script_path.read_text(encoding="utf-8")

        self.assertIn("crypto.randomUUID", script_content)
        self.assertIn("crypto.getRandomValues", script_content)
        self.assertNotIn("Math.random", script_content)
        print(
            " --->  test_xapi_script_uses_secure_uuid_randomness ",
            "of xapi_statement_TestView: OK!",
        )
