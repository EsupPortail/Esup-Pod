"""Unit tests for Duplicate views."""

from datetime import date
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from pod.video import forms as video_forms
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
        media_dir = TemporaryDirectory()
        self.addCleanup(media_dir.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_dir.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        self.user = User.objects.create_user(
            username="testuser", password=PWD, is_staff=True
        )
        self.type = Type.objects.create(title="Test Type")
        self.video = Video.objects.create(
            title="Original Video",
            video=ContentFile(b"source video content", name="test.mp4"),
            slug="original-video",
            type=self.type,
            owner=self.user,
            description="Original description",
            description_fr="Description originale",
            description_en="Original description",
            date_evt=date(2023, 1, 1),
            main_lang="en",
            licence="CC BY-SA",
            is_draft=False,
            is_restricted=False,
            allow_downloading=True,
            is_360=False,
            disable_comment=False,
        )

    def test_video_duplicate(self) -> None:
        """Test duplicating a video."""
        self.client.force_login(self.user)
        url = reverse("duplicate:video_duplicate", args=[self.video.slug])
        with patch.object(video_forms.encode, video_forms.ENCODE_VIDEO) as start_encode:
            response = self.client.get(url)

        # Check that the duplicated video exists
        duplicated_video = Video.objects.get(slug="0002-copy-of-original-video")
        start_encode.assert_called_once_with(duplicated_video.id)
        self.assertNotEqual(duplicated_video.video.name, self.video.video.name)
        with duplicated_video.video.open("rb") as copied_file:
            self.assertEqual(copied_file.read(), b"source video content")
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

        self.assertRedirects(
            response,
            reverse("video:video_edit", args=[duplicated_video.slug]),
            fetch_redirect_response=False,
        )
        print(" --->  test_video_duplicate ok")
