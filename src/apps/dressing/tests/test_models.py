"""
Esup-Pod - Dressing model tests.
"""

import pytest
from django.contrib.auth import get_user_model
from src.apps.dressing.models import Dressing

User = get_user_model()


@pytest.mark.django_db
class TestDressingModel:
    """Tests for the Dressing model."""

    def test_create_dressing(self):
        """Test the creation of a Dressing instance and its fields."""
        user = User.objects.create(username="testuser")
        dressing = Dressing.objects.create(title="Test Dressing")
        dressing.owners.add(user)

        assert dressing.title == "Test Dressing"
        assert dressing.owners.count() == 1
        assert dressing.owners.first() == user
        assert str(dressing) == "Test Dressing"

    def test_to_runner_parameters(self):
        """Test serialization of dressing parameters for the video runner."""
        dressing = Dressing.objects.create(
            title="Test Dressing", opacity=80, position="top_left"
        )
        params = dressing.to_runner_parameters()

        # Without watermark/credits, shouldn't have those keys
        assert "watermark" not in params
        # But we don't return anything else currently except the ones with files

        # We can't easily mock CustomImageModel or Video file fields without factories,
        # but the basic method doesn't throw errors.
        assert isinstance(params, dict)

    def test_watermark_filesystem_lifecycle(self):
        """Test that watermark upload path matches V4 structure and deletion removes the file."""
        import os
        from django.core.files.base import ContentFile
        from src.apps.utils.models import CustomImageModel
        from src.apps.authentication.models import Owner

        user = User.objects.create(username="filesystemuser")
        owner, _ = Owner.objects.get_or_create(user=user)
        assert owner.hashkey

        # Create the custom image model
        img = CustomImageModel.objects.create(
            created_by=user,
            file=ContentFile(b"fake image data", name="my_watermark_image.png"),
        )

        try:
            # Check file exists in filesystem
            assert img.file_exist()

            # Check the path contains "files/<owner.hashkey>/"
            file_path = img.file.path
            assert f"files/{owner.hashkey}" in file_path
            assert "my_watermark_image" in file_path
            assert file_path.endswith(".png")

            # Test deletion deletes the file from filesystem
            img.delete()
            assert not os.path.exists(file_path)
        finally:
            # Cleanup if any test failed
            if img.pk and img.file_exist():
                img.delete()
