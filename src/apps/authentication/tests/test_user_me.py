from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ..models import Owner

User = get_user_model()

class UserMeViewTests(APITestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username=self.username, password=self.password
        )
        Owner.objects.filter(user=self.user).update(affiliation="student", establishment="Etab_1")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("user_me")

    def test_user_me_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.username)
        self.assertEqual(response.data["affiliation"], "student")
        self.assertEqual(response.data["establishment"], "Etab_1")

    def test_user_me_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_detail_still_works(self):
        # Ensure that moving the URL didn't break standard user detail access if needed
        # Note: UserViewSet is registered with router, so 'user-detail' should exist.
        detail_url = reverse("user-detail", kwargs={"pk": self.user.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.username)
