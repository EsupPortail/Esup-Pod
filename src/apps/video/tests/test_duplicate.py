"""
Esup-Pod - Tests for Video duplication.
"""

import os
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.video.models import Video

User = get_user_model()


class VideoDuplicationTests(APITestCase):
    """
    Tests for video duplication API endpoint.
    """

    def setUp(self):
        """
        Setup test users, site, and an initial video.
        """
        self.user = User.objects.create_user(
            username="testuser", password="password"
        )  # nosec
        self.other_user = User.objects.create_user(
            username="otheruser", password="password"
        )
        self.site = Site.objects.get_current()

        # Create a dummy video file
        self.temp_dir = tempfile.mkdtemp()
        self.dummy_video_path = os.path.join(self.temp_dir, "test.mp4")
        with open(self.dummy_video_path, "wb") as f:
            f.write(b"dummy video content")

        self.video_file = SimpleUploadedFile(
            "test.mp4", b"dummy video content", content_type="video/mp4"
        )

        self.video = Video.objects.create(
            title="Original Video",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )
        self.video.sites.set([self.site])
        # Save the file using the field's save method to ensure it's in the proper storage
        self.video.video_file.save("test.mp4", self.video_file)

        from src.apps.video.conf import video_settings

        video_settings.use_duplicate = True

    def test_duplicate_video_success(self):
        """
        Test successful duplication of a video by its owner.
        """
        self.client.force_authenticate(user=self.user)
        url = reverse("video-duplicate", kwargs={"slug": self.video.slug})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        duplicated_slug = response.data["slug"]
        duplicated_video = Video.objects.get(slug=duplicated_slug)

        self.assertEqual(duplicated_video.title, f"Copy of {self.video.title}")
        self.assertEqual(duplicated_video.status, Video.Status.DRAFT)
        self.assertEqual(duplicated_video.owner, self.user)
        self.assertTrue(duplicated_video.video_file.name.endswith(".mp4"))
        self.assertNotEqual(duplicated_video.video_file.name, self.video.video_file.name)

    def test_duplicate_video_unauthorized(self):
        """
        Test that an unauthenticated user cannot duplicate a video.
        """
        # Unauthenticated user
        url = reverse("video-duplicate", kwargs={"slug": self.video.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_video_forbidden(self):
        """
        Test that a user who is not the owner cannot duplicate the video.
        """
        # Authenticated but not owner
        self.client.force_authenticate(user=self.other_user)
        url = reverse("video-duplicate", kwargs={"slug": self.video.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_video_disabled(self):
        """
        Test that duplication fails if use_duplicate setting is False.
        """
        from src.apps.video.conf import video_settings

        video_settings.use_duplicate = False

        self.client.force_authenticate(user=self.user)
        url = reverse("video-duplicate", kwargs={"slug": self.video.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "Duplication is disabled.")

        # Re-enable for other tests
        video_settings.use_duplicate = True
