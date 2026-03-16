from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..conf import AuthConfig
from ..models import Owner

User = get_user_model()


class LoginViewTests(APITestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )
        Owner.objects.get_or_create(user=self.user)
        self.url = reverse("token_obtain_pair")

    def test_login_success(self):
        data = {"username": self.username, "password": self.password}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_failure(self):
        data = {"username": self.username, "password": "wrongpassword"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ShibbolethLoginViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("token_obtain_pair_shibboleth")
        self.remote_user_header = "REMOTE_USER"

    def test_shibboleth_success(self):
        headers = {
            "REMOTE_USER": "shibuser",
            "HTTP_SHIBBOLETH_MAIL": "shib@example.com",
        }
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(username="shibuser").exists())

    def test_shibboleth_missing_header(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch(
        "src.apps.authentication.services.providers.shibboleth.auth_settings",
        new_callable=lambda: AuthConfig(
            remote_user_header="REMOTE_USER",
            shib_secure_header="HTTP_X_SECURE",
            shib_secure_value="secret",
        ),
    )
    def test_shibboleth_security_check_fail(self, mock_settings):
        """Test that missing security header returns 403."""
        headers = {
            "HTTP_REMOTE_USER": "shibuser",
        }
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OIDCLoginViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("token_obtain_pair_oidc")

    @patch("requests.post")
    @patch("requests.get")
    @patch(
        "src.apps.authentication.services.providers.oidc.auth_settings",
        new_callable=lambda: AuthConfig(
            use_oidc=True,
        ),
    )
    def test_oidc_success(self, mock_settings, mock_get, mock_post):
        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {"access_token": "fake_access_token"}
        mock_token_resp.status_code = 200
        mock_post.return_value = mock_token_resp

        mock_user_resp = MagicMock()
        mock_user_resp.json.return_value = {
            "preferred_username": "oidcuser",
            "email": "oidc@example.com",
            "given_name": "OIDC",
            "family_name": "User",
        }
        mock_user_resp.status_code = 200
        mock_get.return_value = mock_user_resp

        data = {"code": "auth_code", "redirect_uri": "http://localhost/callback"}
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(username="oidcuser").exists())
