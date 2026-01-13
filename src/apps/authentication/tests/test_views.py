from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
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
        self.remote_user_header = "REMOTE_USER"  # Default setting

    def test_shibboleth_success(self):
        headers = {
            "REMOTE_USER": "shibuser",
            "HTTP_SHIBBOLETH_MAIL": "shib@example.com",  # This might need adjustment based on how code reads it but let's try standard header simulation
        }
        # Assuming no security header required by default test settings or mocked

        response = self.client.get(self.url, **headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(User.objects.filter(username="shibuser").exists())

    def test_shibboleth_missing_header(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_shibboleth_security_check_fail(self):
        with self.settings(
            SHIB_SECURE_HEADER="HTTP_X_SECURE", SHIB_SECURE_VALUE="secret"
        ):
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
    def test_oidc_success(self, mock_get, mock_post):
        # Mock Token response
        mock_token_resp = MagicMock()
        mock_token_resp.json.return_value = {"access_token": "fake_access_token"}
        mock_token_resp.status_code = 200
        mock_post.return_value = mock_token_resp

        # Mock UserInfo response
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

        # We need to ensure OIDC settings are present
        with self.settings(
            OIDC_OP_TOKEN_ENDPOINT="http://oidc/token",
            OIDC_OP_USER_ENDPOINT="http://oidc/userinfo",
            OIDC_RP_CLIENT_ID="client",
            OIDC_RP_CLIENT_SECRET="secret",
        ):
            response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(username="oidcuser").exists())

