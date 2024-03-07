from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from pod.ai_enhancement.models import AIEnrichment
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
        self.ai_enrichment = AIEnrichment.objects.create(video=self.video)

    def test_create_ai_enrichment(self):
        """Test the model creation."""
        self.assertEqual(self.ai_enrichment.video, self.video)
        print(" --->  test_create_ai_enrichment ok")
