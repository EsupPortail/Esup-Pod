"""Unit tests for main views.

*  run with 'python manage.py test pod.main.tests.test_views'
"""
from django.conf import settings as django_settings

from django.test import RequestFactory, override_settings
from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from captcha.models import CaptchaStore
from http import HTTPStatus
from pod.main.context_processors import context_settings
from pod.main.models import Configuration
import tempfile
import os
from django.template import Context


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


class XSSTests(TestCase):
    """Tests against some Reflected XSS security breach."""

    def setUp(self):
        """Set up some generic test strings."""
        self.XSS_inject = "</script><script>alert(document.domain)</script>"
        self.XSS_detect = b"<script>alert(document.domain)</script>"

    def test_videos_XSS(self):
        """Test if /videos/ is safe against some XSS."""
        for param in ["owner", "discipline", "tag", "cursus"]:
            response = self.client.get("/videos/?%s=%s" % (param, self.XSS_inject))

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertFalse(self.XSS_detect in response.content)

    def test_search_XSS(self):
        """Test if /search/ is safe against some XSS."""
        for param in ["q", "start_date", "end_date"]:
            response = self.client.get("/search/?%s=%s" % (param, self.XSS_inject))

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertFalse(self.XSS_detect in response.content)

        # Test that even with a recognized facet it doesn't open a breach
        for facet in ["type", "slug"]:
            response = self.client.get(
                "/search/?selected_facets=%s:%s" % (facet, self.XSS_inject)
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertFalse(self.XSS_detect in response.content)


class TestShowVideoButton(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.context = Context()
        User.objects.create(username="admin", password="admin", is_staff=False)

    def test_show_video_button_for_staff_user(self):
        RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY = getattr(
            django_settings,
            "RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY",
            True
        )
        # On met en place la restriction
        request = self.factory.get('/')
        settings = context_settings(request)
        settings["RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY"] = \
            RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY

        # On se connecte
        self.user.is_staff = True
        self.client = Client()
        self.user = User.objects.get(username="admin")
        self.client.force_login(self.user)

        # On envoie la requête
        response = self.client.get('/', context=settings)

        # On vérifie
        self.assertContains(response, 'id="nav-addvideo"')
        self.assertContains(response, 'id="nav-myvideos"')

        """template = Template("{% load navbar %}{% show_video_button user %}")
        rendered = template.render(self.context.flatten())
        self.assertInHTML('id="nav-addvideo"', rendered)
        self.assertInHTML('id="nav-myvideos"', rendered)"""

    """
    def test_show_video_button_for_non_staff_user(self):
        self.user.is_staff = False
        self.client = Client()
        self.user = User.objects.get(username="admin")
        self.client.force_login(self.user)

        template = Template("{% load navbar %}{% show_video_button user %}")
        rendered = template.render(self.context.flatten())
        self.assertNotContains(rendered, '<li id="nav-addvideo">')
        self.assertNotContains(rendered, '<li id="nav-myvideos">')

    def test_show_video_button_for_non_staff_user_not_in_restrict(self):
        self.user.is_staff = False
        self.client = Client()
        self.user = User.objects.get(username="admin")
        self.client.force_login(self.user)

        template = Template("{% load navbar %}{% show_video_button user %}")
        rendered = template.render(self.context.flatten())
        self.assertNotInHTML('id="nav-addvideo"', rendered)
        self.assertNotInHTML('id="nav-myvideos"', rendered)
    """
