"""
Esup-Pod - Completion views functionality tests.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.video.models import Video
from src.apps.completion.models import Contributor, Contribution, Overlay

User = get_user_model()


class CompletionViewsTests(APITestCase):
    """Test suite for completion app views functionality (filters, search, etc)."""

    def setUp(self):
        """Set up the test environment."""
        self.user = User.objects.create_user(
            username="owner", password="password"  # nosec
        )
        self.client.force_authenticate(user=self.user)

        self.video1 = Video.objects.create(title="Video 1", owner=self.user)
        self.video2 = Video.objects.create(title="Video 2", owner=self.user)

        # Contributors
        self.c1 = Contributor.objects.create(
            first_name="Alice", last_name="Smith", email_address="alice@test.com"
        )
        self.c2 = Contributor.objects.create(
            first_name="Bob", last_name="Johnson", email_address="bob@test.com"
        )

        # Contributions
        self.contrib1 = Contribution.objects.create(
            video=self.video1, contributor=self.c1, role="author", job_title="Writer"
        )
        self.contrib2 = Contribution.objects.create(
            video=self.video2, contributor=self.c2, role="speaker", job_title="Speaker"
        )

        # Overlays
        self.ov1 = Overlay.objects.create(
            video=self.video1, title="Overlay 1", time_start=10, time_end=20
        )
        self.ov2 = Overlay.objects.create(
            video=self.video1, title="Overlay 2", time_start=5, time_end=15
        )
        self.ov3 = Overlay.objects.create(
            video=self.video2, title="Overlay 3", time_start=10, time_end=20
        )

    # --- Contributor ---
    def test_contributor_search(self):
        """Test search filter on Contributor."""
        url = reverse("contributor-list") + "?search=Alice"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["first_name"], "Alice")

    # --- Contribution ---
    def test_contribution_filter_by_video(self):
        """Test filtering contributions by video."""
        url = reverse("contribution-list") + f"?video={self.video1.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["role"], "author")

    def test_contribution_filter_by_role(self):
        """Test filtering contributions by role."""
        url = reverse("contribution-list") + "?role=speaker"
        response = self.client.get(url)
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["contributor_details"]["first_name"], "Bob")

    # --- Overlay ---
    def test_overlay_filter_by_video(self):
        """Test filtering overlays by video."""
        url = reverse("overlay-list") + f"?video={self.video1.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(results), 2)

    def test_overlay_ordering(self):
        """Test ordering overlays by time_start (default behavior)."""
        url = reverse("overlay-list") + f"?video={self.video1.id}"
        response = self.client.get(url)
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        # ov2 starts at 5, ov1 starts at 10, so ov2 should be first
        self.assertEqual(results[0]["title"], "Overlay 2")
        self.assertEqual(results[1]["title"], "Overlay 1")
