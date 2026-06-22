"""
Esup-Pod - Completion permissions and endpoints tests.
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from src.apps.video.models import Video
from src.apps.completion.models import Contributor, Contribution, Document, Overlay

User = get_user_model()


class CompletionPermissionsTests(APITestCase):
    """Test suite for completion app permissions and views."""

    def setUp(self):
        """Set up test environment."""
        # Users
        self.user_owner = User.objects.create_user(
            username="owner", password="password"  # nosec
        )
        self.user_co_owner = User.objects.create_user(
            username="co_owner", password="password"  # nosec
        )
        self.user_other = User.objects.create_user(
            username="other", password="password"  # nosec
        )
        self.user_staff = User.objects.create_user(
            username="staff", password="password", is_staff=True  # nosec
        )
        self.user_superuser = User.objects.create_superuser(
            username="admin", password="password"  # nosec
        )

        # Video
        self.video = Video.objects.create(
            title="Test Video",
            owner=self.user_owner,
            status=Video.Status.PUBLISHED,
        )
        self.video.co_owners.add(self.user_co_owner)

        # Contributor
        self.contributor = Contributor.objects.create(
            first_name="John", last_name="Doe", email_address="john.doe@test.com"
        )

        # Contribution
        self.contribution = Contribution.objects.create(
            video=self.video,
            contributor=self.contributor,
            role="speaker",
            job_title="Dev",
        )

        # Document
        self.public_document = Document.objects.create(
            video=self.video,
            title="Public Doc",
            file=SimpleUploadedFile("public.txt", b"public content"),
            is_private=False,
        )
        self.private_document = Document.objects.create(
            video=self.video,
            title="Private Doc",
            file=SimpleUploadedFile("private.txt", b"private content"),
            is_private=True,
        )

        # Overlay
        self.overlay = Overlay.objects.create(
            video=self.video,
            title="Test Overlay",
            time_start=10,
            time_end=20,
            content="Hello",
        )

    # -----------------------
    # Contributor Tests
    # -----------------------
    def test_contributor_list_authenticated(self):
        """Any authenticated user can list contributors."""
        self.client.force_authenticate(user=self.user_other)
        url = reverse("contributor-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(results), 1)

    def test_contributor_create_superuser(self):
        """Only superusers can create contributors via API."""
        self.client.force_authenticate(user=self.user_superuser)
        url = reverse("contributor-list")
        data = {"first_name": "Jane", "last_name": "Smith"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_contributor_create_normal_user_denied(self):
        """Normal users cannot create contributors."""
        self.client.force_authenticate(user=self.user_owner)
        url = reverse("contributor-list")
        data = {"first_name": "Jane", "last_name": "Smith"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -----------------------
    # Contribution Tests
    # -----------------------
    def test_contribution_create_by_owner(self):
        """Owner can add a contribution."""
        self.client.force_authenticate(user=self.user_owner)
        contributor2 = Contributor.objects.create(first_name="Jane", last_name="Doe")
        url = reverse("contribution-list")
        data = {
            "video": self.video.id,
            "contributor_id": contributor2.id,
            "role": "author",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_contribution_create_by_co_owner(self):
        """Co-owner can add a contribution."""
        self.client.force_authenticate(user=self.user_co_owner)
        contributor3 = Contributor.objects.create(first_name="Marc", last_name="Dup")
        url = reverse("contribution-list")
        data = {
            "video": self.video.id,
            "contributor_id": contributor3.id,
            "role": "director",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_contribution_create_by_other_denied(self):
        """Random user cannot add a contribution."""
        self.client.force_authenticate(user=self.user_other)
        url = reverse("contribution-list")
        data = {
            "video": self.video.id,
            "contributor_id": self.contributor.id,
            "role": "author",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -----------------------
    # Document Tests
    # -----------------------
    def test_document_list_for_other_user(self):
        """Other users only see public documents in the list."""
        self.client.force_authenticate(user=self.user_other)
        url = reverse("document-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Public Doc")

    def test_document_list_for_owner(self):
        """Owner sees both public and their own private documents."""
        self.client.force_authenticate(user=self.user_owner)
        url = reverse("document-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data.get("results", response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertEqual(len(results), 2)

    def test_document_create_by_owner(self):
        """Owner can add a document."""
        self.client.force_authenticate(user=self.user_owner)
        url = reverse("document-list")
        data = {
            "video": self.video.id,
            "title": "New Doc",
            "file": SimpleUploadedFile("new.txt", b"new content"),
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_document_create_by_other_denied(self):
        """Other users cannot add a document to someone else's video."""
        self.client.force_authenticate(user=self.user_other)
        url = reverse("document-list")
        data = {
            "video": self.video.id,
            "title": "New Doc",
            "file": SimpleUploadedFile("new.txt", b"new content"),
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_document_download_public(self):
        """Anyone can download a public document."""
        self.client.force_authenticate(user=self.user_other)
        url = reverse("document-download", kwargs={"pk": self.public_document.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_document_download_private_by_owner(self):
        """Owner can download a private document."""
        self.client.force_authenticate(user=self.user_owner)
        url = reverse("document-download", kwargs={"pk": self.private_document.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_document_download_private_by_other_denied(self):
        """Random users cannot download a private document (it is not found)."""
        self.client.force_authenticate(user=self.user_other)
        url = reverse("document-download", kwargs={"pk": self.private_document.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_document_download_private_by_staff_denied(self):
        """Staff cannot download a private document (bypass removed)."""
        self.client.force_authenticate(user=self.user_staff)
        url = reverse("document-download", kwargs={"pk": self.private_document.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # -----------------------
    # Overlay Tests
    # -----------------------
    def test_overlay_create_by_co_owner(self):
        """Co-owner can add an overlay."""
        self.client.force_authenticate(user=self.user_co_owner)
        url = reverse("overlay-list")
        data = {
            "video": self.video.id,
            "title": "New Overlay",
            "time_start": 30,
            "time_end": 40,
            "content": "Test",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_overlay_create_by_other_denied(self):
        """Random user cannot add an overlay."""
        self.client.force_authenticate(user=self.user_other)
        url = reverse("overlay-list")
        data = {
            "video": self.video.id,
            "title": "New Overlay",
            "time_start": 30,
            "time_end": 40,
            "content": "Test",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_overlay_update_by_owner(self):
        """Owner can update an overlay."""
        self.client.force_authenticate(user=self.user_owner)
        url = reverse("overlay-detail", kwargs={"pk": self.overlay.id})
        data = {"title": "Updated Overlay"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.overlay.refresh_from_db()
        self.assertEqual(self.overlay.title, "Updated Overlay")

    def test_overlay_delete_by_other_denied(self):
        """Other user cannot delete an overlay."""
        self.client.force_authenticate(user=self.user_other)
        url = reverse("overlay-detail", kwargs={"pk": self.overlay.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
