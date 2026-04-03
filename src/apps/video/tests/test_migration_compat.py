"""
Esup-Pod - Tests for migration compatibility.
"""

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings
import hashlib
from src.apps.video.models import Video
from django.contrib.auth import get_user_model

User = get_user_model()


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
class LegacyHashUnlockTest(APITestCase):
    """
    Test the legacy format hash unlocking.
    """

    def setUp(self):
        """
        Setup test objects.
        """
        self.user = User.objects.create_user(username="testuser", password="password")
        self.video = Video.objects.create(
            title="Restricted Video",
            owner=self.user,
            status=Video.Status.RESTRICTED,
            is_auth_required=False,
            password="secretpassword",
        )
        self.valid_hash = hashlib.sha1(
            f"{settings.SECRET_KEY}{self.video.id}".encode()
        ).hexdigest()

    def test_unlock_with_legacy_hash(self):
        """
        Test unlock is successful using legacy v4 hash.
        """
        url = reverse("video-unlock", kwargs={"slug": self.video.slug})
        response = self.client.post(f"{url}?hash={self.valid_hash}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("video_url", response.data)
        self.assertEqual(response.data.get("source"), "legacy_hash")

        self.assertTrue(self.client.session.get(f"video_unlocked_{self.video.id}"))
