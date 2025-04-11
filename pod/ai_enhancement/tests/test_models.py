"""Test the models for ai_enhancement module."""

from django.contrib.auth.models import User
from django.test import TestCase

from pod.ai_enhancement.models import AIEnhancement
from pod.video.models import Video, Type


class AIEnrichmentModelTest(TestCase):
    """
    Test the AIEnrichment model.

    Args:
        TestCase (::class::`django.test.TestCase`): The test case.
    """

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Set up the tests."""
        self.owner = User.objects.create_user(username="testuser")
        self.video = Video.objects.create(
            owner=self.owner,
            type=Type.objects.create(title="Test Type"),
        )
        self.ai_enhancement = AIEnhancement.objects.create(
            video=self.video, ai_enhancement_id_in_aristote="test_id"
        )

    def test_create_ai_enhancement(self):
        """Test the model creation."""
        self.assertEqual(self.ai_enhancement.video, self.video)
        self.assertEqual(self.ai_enhancement.ai_enhancement_id_in_aristote, "test_id")
        print(" --->  test_create_ai_enhancement ok")

    def test_str(self):
        """Test the string representation."""
        self.assertEqual(str(self.ai_enhancement), f"{self.video.title} - test_id")
        print(" --->  test_str ok")

    def test_sites(self):
        """Test the sites property."""
        self.assertEqual(self.ai_enhancement.sites, self.video.sites)
        print(" --->  test_sites ok")
