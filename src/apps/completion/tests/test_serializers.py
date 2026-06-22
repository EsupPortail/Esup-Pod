"""
Esup-Pod - Completion serializers tests.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from src.apps.video.models import Video
from src.apps.completion.models import Overlay
from src.apps.completion.serializers import OverlaySerializer

User = get_user_model()


class OverlaySerializerTests(TestCase):
    """Tests for OverlaySerializer."""

    def setUp(self):
        """Set up the test environment."""
        self.user = User.objects.create_user(
            username="owner", password="password"  # nosec
        )
        self.video = Video.objects.create(
            title="Test Video",
            owner=self.user,
            status=Video.Status.PUBLISHED,
        )

    def test_link_superposition_enabled(self):
        """Test URL transformation when LINK_SUPERPOSITION is True."""
        from src.apps.completion.conf import completion_settings

        old_val = completion_settings.link_superposition
        completion_settings.link_superposition = True
        data = {
            "video": self.video.id,
            "title": "Overlay Test",
            "time_start": 10,
            "time_end": 20,
            "content": "Visit https://example.com for more info.",
        }
        serializer = OverlaySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertTrue(
            '<a href="https://example.com" target="_blank">https://example.com</a>'
            in serializer.validated_data["content"]
        )
        completion_settings.link_superposition = old_val

    def test_link_superposition_disabled(self):
        """Test URL is not transformed when LINK_SUPERPOSITION is False."""
        from src.apps.completion.conf import completion_settings

        old_val = completion_settings.link_superposition
        completion_settings.link_superposition = False
        data = {
            "video": self.video.id,
            "title": "Overlay Test",
            "time_start": 10,
            "time_end": 20,
            "content": "Visit https://example.com for more info.",
        }
        serializer = OverlaySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn("<a href=", serializer.validated_data["content"])
        completion_settings.link_superposition = old_val

    def test_time_validation_fail(self):
        """Test that time_start >= time_end fails validation."""
        data = {
            "video": self.video.id,
            "title": "Overlay Test",
            "time_start": 20,
            "time_end": 10,
            "content": "Test",
        }
        serializer = OverlaySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(serializer.errors["non_field_errors"][0].code, "invalid")

    def test_partial_update_validation(self):
        """Test that partial updates correctly merge data and pass validation."""
        overlay = Overlay.objects.create(
            video=self.video,
            title="Original",
            time_start=10,
            time_end=20,
            content="Original content",
        )
        data = {"title": "Updated Title"}
        serializer = OverlaySerializer(overlay, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        # Test partial update with invalid times
        data = {"time_start": 30}  # end is 20, so 30 > 20 should fail
        serializer = OverlaySerializer(overlay, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
