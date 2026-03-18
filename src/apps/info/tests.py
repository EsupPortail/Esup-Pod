from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class InfoViewsTests(APITestCase):
    def test_system_info_view(self):
        url = reverse("system_info")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("project", response.data)
        self.assertIn("version", response.data)
        self.assertEqual(response.data["project"], "POD V5")

    def test_config_info_view(self):
        url = reverse("config_info")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)
        self.assertIn("authentication", response.data)
        self.assertIn("use_cas", response.data["authentication"])
