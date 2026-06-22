"""
Esup-Pod - Dressing views tests.
"""

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from src.apps.dressing.models import Dressing

User = get_user_model()

# ggignore-start
# gitguardian:ignore
TEST_PASSWORD = "testpassword"  # nosec
# ggignore-end


@pytest.fixture
def api_client():
    """Fixture to obtain an APIClient instance."""
    return APIClient()


@pytest.fixture
def user():
    """Fixture to create a standard User."""
    return User.objects.create_user(username="testuser", password=TEST_PASSWORD)


@pytest.fixture
def superuser():
    """Fixture to create a superuser User."""
    return User.objects.create_superuser(username="admin", password=TEST_PASSWORD)


@pytest.mark.django_db
class TestDressingViewSet:
    """Tests for the DressingViewSet API endpoints."""

    def test_list_dressings_unauthenticated(self, api_client):
        """Test listing dressings without authentication (should be 401)."""
        response = api_client.get("/api/dressing/dressing/")
        assert response.status_code == 401

    def test_list_dressings_authenticated(self, api_client, user):
        """Test listing dressings with authenticated user, showing only owned/user dressings."""
        Dressing.objects.create(title="Dressing 1")
        dressing2 = Dressing.objects.create(title="Dressing 2")
        dressing2.owners.add(user)

        api_client.force_authenticate(user=user)
        response = api_client.get("/api/dressing/dressing/")

        assert response.status_code == 200
        # Should only see Dressing 2 because user is owner
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["title"] == "Dressing 2"

    def test_create_dressing(self, api_client, user):
        """Test creating a dressing instance and verifying default ownership."""
        api_client.force_authenticate(user=user)
        response = api_client.post("/api/dressing/dressing/", {"title": "New Dressing"})

        assert response.status_code == 201
        assert response.data["title"] == "New Dressing"

        # User should automatically be an owner
        dressing = Dressing.objects.get(id=response.data["id"])
        assert user in dressing.owners.all()

    def test_superuser_sees_all(self, api_client, superuser, user):
        """Test that superusers can see all dressing configurations."""
        Dressing.objects.create(title="Dressing 1")
        dressing2 = Dressing.objects.create(title="Dressing 2")
        dressing2.owners.add(user)

        api_client.force_authenticate(user=superuser)
        response = api_client.get("/api/dressing/dressing/")

        assert response.status_code == 200
        assert len(response.data["results"]) == 2

    def test_dressing_disabled(self, api_client, user):
        """Test that if use_dressing is False, endpoints return 403."""
        from src.apps.dressing.conf import dressing_settings

        dressing_settings.use_dressing = False
        try:
            api_client.force_authenticate(user=user)
            response = api_client.get("/api/dressing/dressing/")
            assert response.status_code == 403
        finally:
            dressing_settings.use_dressing = True

    def test_allow_user_custom_dressing_disabled(self, api_client, user, superuser):
        """Test that standard users cannot create dressings if allow_user_custom_dressing is False."""
        from src.apps.dressing.conf import dressing_settings

        dressing_settings.allow_user_custom_dressing = False
        try:
            # Standard user should get 403 on POST
            api_client.force_authenticate(user=user)
            response = api_client.post("/api/dressing/dressing/", {"title": "Restricted"})
            assert response.status_code == 403

            # Superuser should still be allowed to POST
            api_client.force_authenticate(user=superuser)
            response = api_client.post(
                "/api/dressing/dressing/", {"title": "Allowed for admin"}
            )
            assert response.status_code == 201
        finally:
            dressing_settings.allow_user_custom_dressing = True

    def test_credits_duration_validation(self, api_client, user):
        """Test validation of opening/ending credits video duration limits."""
        from src.apps.dressing.conf import dressing_settings
        from src.apps.video.models import Video
        from django.core.files.base import ContentFile

        # Create mock videos with durations exceeding and within the limit
        limit = dressing_settings.max_credits_duration_seconds
        video_ok = Video.objects.create(
            title="Intro Video",
            duration=limit - 5,
            video_file=ContentFile(b"fake video content", name="intro.mp4"),
            owner=user,
        )
        video_bad = Video.objects.create(
            title="Too Long Intro",
            duration=limit + 5,
            video_file=ContentFile(b"fake video content", name="too_long.mp4"),
            owner=user,
        )

        api_client.force_authenticate(user=user)

        # Valid credits should succeed
        response = api_client.post(
            "/api/dressing/dressing/",
            {"title": "Valid Dressing", "opening_credits": video_ok.id},
        )
        assert response.status_code == 201

        # Invalid credits should fail
        response = api_client.post(
            "/api/dressing/dressing/",
            {"title": "Invalid Dressing", "opening_credits": video_bad.id},
        )
        assert response.status_code == 400
        assert "opening_credits" in response.data

    def test_watermark_size_validation(self, api_client, user):
        """Test validation of watermark size limits."""
        from src.apps.utils.models import CustomImageModel
        from unittest.mock import patch
        from django.core.files.base import ContentFile

        img = CustomImageModel.objects.create(
            file=ContentFile(b"fake image content", name="watermark.png")
        )

        api_client.force_authenticate(user=user)

        # Mock the limit to a low value (1 MB) to ensure the test does not depend on default settings
        from src.apps.dressing.conf import dressing_settings

        original_limit = dressing_settings.max_watermark_size_mb
        dressing_settings.max_watermark_size_mb = 1

        try:
            # Mock file_size property and file_exist to simulate a file that is too large
            with (
                patch.object(CustomImageModel, "file_exist", return_value=True),
                patch.object(
                    CustomImageModel,
                    "file_size",
                    new=property(lambda self: 2 * 1024 * 1024),
                ),
            ):
                # Since limit is temporarily 1 MB, 2 MB should fail
                response = api_client.post(
                    "/api/dressing/dressing/",
                    {"title": "Too Large Watermark Dressing", "watermark": img.id},
                )
                assert response.status_code == 400
                assert "watermark" in response.data
        finally:
            dressing_settings.max_watermark_size_mb = original_limit
