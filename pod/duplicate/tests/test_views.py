"""Unit tests for Duplicate views."""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from pod.video.models import Video, Type

# ggignore-start
# gitguardian:ignore
PWD = "azerty1234"  # nosec
# ggignore-end


class VideoDuplicateViewTest(TestCase):
    """Test case for duplicating videos."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up required objects for the tests."""
        self.user = User.objects.create_user(
            username="testuser", password=PWD, is_staff=True
        )
        self.type = Type.objects.create(title="Test Type")
        self.video = Video.objects.create(
            title="Original Video",
            video="test.mp4",
            slug="original-video",
            type=self.type,
            owner=self.user,
            description="Original description",
            description_fr="Description originale",
            description_en="Original description",
            date_evt="2023-01-01",
            main_lang="en",
            licence="CC BY-SA",
            is_draft=False,
            is_restricted=False,
            allow_downloading=True,
            is_360=False,
            disable_comment=False,
        )
        self.video.save()

    def test_video_duplicate(self) -> None:
        """Test duplicating a video."""
        self.client.force_login(self.user)
        url = reverse("duplicate:video_duplicate", args=[self.video.slug])
        response = self.client.get(url)

        # Check that the duplicated video exists
        duplicated_video = Video.objects.get(slug="0002-copy-of-original-video")
        self.assertEqual(duplicated_video.title, "Copy of Original Video")
        self.assertEqual(duplicated_video.type, self.type)
        self.assertEqual(duplicated_video.owner, self.user)
        self.assertEqual(duplicated_video.description, "Original description")
        self.assertEqual(duplicated_video.description_fr, "Description originale")
        self.assertEqual(duplicated_video.description_en, "Original description")
        self.assertEqual(duplicated_video.date_evt.strftime("%Y-%m-%d"), "2023-01-01")
        self.assertEqual(duplicated_video.main_lang, "en")
        self.assertEqual(duplicated_video.licence, "CC BY-SA")
        self.assertTrue(duplicated_video.is_draft)
        self.assertEqual(duplicated_video.is_restricted, False)
        self.assertEqual(duplicated_video.allow_downloading, True)
        self.assertEqual(duplicated_video.is_360, False)
        self.assertEqual(duplicated_video.disable_comment, False)

        # Check the response status code
        self.assertEqual(
            response.status_code, 302
        )  # Redirect after successful duplication"
        print(" --->  test_video_duplicate ok")
