"""Unit tests for authentication views.

*  run with 'python manage.py test pod.authentication.tests.test_views'
"""

from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class authenticationViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        User.objects.create(username="pod", password="podv3")
        print(" --->  SetUp of authenticationViewsTestCase: OK!")

    def test_authentication_login_gateway(self):
        self.client = Client()
        # CAS_GATEWAY is valued to False
        response = self.client.get("/authentication_login_gateway/")
        self.assertEqual(
            response.content,
            b"You must set CAS_GATEWAY to True to use this view",
        )
        self.assertEqual(response.status_code, 200)

        print(
            "   --->  test_authentication_login_gateway \
            of authenticationViewsTestCase: OK!"
        )

    def test_authentication_login(self) -> None:
        """Test authentication login page."""
        self.client = Client()
        self.user = User.objects.get(username="pod")
        login_url = settings.LOGIN_URL

        # User already authenticated
        self.client.force_login(self.user)
        response = self.client.get(login_url)
        self.assertRedirects(response, "/")

        # User not authenticated and CAS are valued to False
        self.client.logout()
        response = self.client.get(login_url)
        self.assertRedirects(response, "/accounts/login/?next=/")

        print(
            "   --->  test_authentication_login \
            of authenticationViewsTestCase: OK!"
        )

    def test_authentication_logout(self) -> None:
        self.client = Client()
        # USE_CAS is valued to False
        response = self.client.get("/authentication_logout/")
        self.assertRedirects(response, "/accounts/logout/?next=/", target_status_code=302)

        print(
            "   --->  test_authentication_logout \
            of authenticationViewsTestCase: OK!"
        )

    def test_userpicture(self):
        self.client = Client()
        self.user = User.objects.get(username="pod")
        # User is not loged in
        response = self.client.get("/accounts/userpicture/")
        self.assertEqual(response.status_code, 302)  # Redirect to login page

        # User is loged in
        self.client.force_login(self.user)
        # GET method
        response = self.client.get("/accounts/userpicture/")
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "userpicture/userpicture.html")
        # POST method
        # Form is valid
        response = self.client.post("/accounts/userpicture/", {"userpicture": ""})
        # le message a été retiré dans le code
        # messages = list(response.wsgi_request._messages)
        # self.assertEqual(len(messages), 1)
        # self.assertEqual(str(messages[0]), 'Your picture has been saved.')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "userpicture/userpicture.html")
        # Form is not valid
        response = self.client.post("/accounts/userpicture/", {"userpicture": 12})
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), _("One or more errors have been found in the form.")
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "userpicture/userpicture.html")

        print("   --->  test_userpicture of authenticationViewsTestCase: OK!")
