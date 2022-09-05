"""Unit tests for main views.

*  run with 'python manage.py test pod.main.tests.test_views'
"""
from django.test import override_settings
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from captcha.models import CaptchaStore
from http import HTTPStatus
from pod.main.models import Configuration
import tempfile
import os


class MainViewsTestCase(TestCase):
    """Main views test cases."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create fictive user who will make tests."""
        User.objects.create(username="pod", password="podv3")
        print(" --->  SetUp of MainViewsTestCase: OK!")

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_download_file(self):
        """Test download folder."""
        self.client = Client()

        # GET method is used
        response = self.client.get("/download/")
        self.assertRaises(PermissionDenied)

        # POST method is used
        # filename is not set
        response = self.client.post("/download/")
        self.assertRaises(PermissionDenied)
        # filename is properly set
        temp_file = tempfile.NamedTemporaryFile()
        response = self.client.post("/download/", {"filename": temp_file.name})
        self.assertEqual(
            response["Content-Disposition"],
            'attachment; filename="%s"' % (os.path.basename(temp_file.name)),
        )
        self.assertEqual(response.status_code, 200)

        print("   --->  download_file of mainViewsTestCase: OK!")

    def test_contact_us(self):
        """Test the "contact us" form."""
        self.client = Client()

        # GET method is used.
        response = self.client.get("/contact_us/")
        self.assertTemplateUsed(response, "contact_us.html")

        # POST method is used
        # Form is valid
        hashcode = CaptchaStore.generate_key()
        captcha = CaptchaStore.objects.get(hashkey=hashcode)  # Forcing captcha
        response = self.client.post(
            "/contact_us/",
            {
                "name": "pod",
                "email": "pod@univ.fr",
                "subject": "info",
                "description": "pod",
                "captcha_0": captcha.hashkey,
                "captcha_1": captcha.response,
                "url_referrer": "http://localhost:8000/",
                "firstname": "",
            },
        )
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), _("Your message has been sent."))
        self.assertRedirects(response, "http://localhost:8000/")
        print("   --->  test_contact_us of mainViewsTestCase: OK!")
        # Form is not valid
        #  /!\  voir fonction clean de ContactUsForm segment if
        response = self.client.post(
            "/contact_us/",
            {
                "name": "",
                "email": "",
                "subject": "info",
                "description": "",
                "captcha": "",
                "firstname": "",
            },
        )
        self.assertTemplateUsed(response, "contact_us.html")
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), _("One or more errors have been found in the form.")
        )
        self.assertTemplateUsed(response, "contact_us.html")

        print("   --->  test_contact_us of mainViewsTestCase: OK!")


class MaintenanceViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        User.objects.create(username="pod", password="podv3")

    def test_maintenance(self):
        """Test Pod maintenance mode."""
        self.client = Client()
        self.user = User.objects.get(username="pod")
        self.client.force_login(self.user)
        # GET method is used
        url = reverse("video:video_edit", kwargs={})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        conf = Configuration.objects.get(key="maintenance_mode")
        conf.value = "1"
        conf.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/maintenance/")
        print("   --->  test_maintenance of MaintenanceViewsTestCase: OK!")


class RobotsTxtTests(TestCase):
    """Robots.txt test cases."""

    def test_robots_get(self):
        """Test if we get a robot.txt file."""
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["content-type"], "text/plain")
        lines = response.content.decode().splitlines()
        self.assertEqual(lines[0], "User-Agent: *")

    def test_robots_post_disallowed(self):
        """Test if POST method is disallowed when getting robot.txt file."""
        response = self.client.post("/robots.txt")

        self.assertEqual(HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
