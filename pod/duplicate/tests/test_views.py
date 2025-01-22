# pod/video/tests/test_video_duplicate.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from pod.video.models import Video, Type, Discipline, Channel, Theme


class VideoDuplicateViewTest(TestCase):
    """Test case for duplicating videos."""

    def setUp(self):
        """Set up required objects for the tests."""
        self.user = User.objects.create_user(username="testuser", password="password")
        self.type = Type.objects.create(title="Test Type")
        self.discipline = Discipline.objects.create(title="Test Discipline")
        self.channel = Channel.objects.create(title="Test Channel", slug="test-channel")
        self.theme = Theme.objects.create(title="Test Theme")
        self.video = Video.objects.create(
            title="Original Video",
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
            date_delete="2024-01-01",
            disable_comment=False,
        )
        self.video.discipline.add(self.discipline)
        self.video.channel.add(self.channel)
        self.video.theme.add(self.theme)
        self.client.login(username="testuser", password="password")

    def test_video_duplicate(self):
        """Test duplicating a video."""
        response = self.client.post(reverse("video_duplicate", args=[self.video.slug]))

        # Check that the duplicated video exists
        duplicated_video = Video.objects.get(slug="original-video-copy")
        self.assertEqual(duplicated_video.title, "Copy of Original Video")
        self.assertEqual(duplicated_video.type, self.type)
        self.assertEqual(duplicated_video.owner, self.user)
        self.assertEqual(duplicated_video.description, "Original description")
        self.assertEqual(duplicated_video.description_fr, "Description originale")
        self.assertEqual(duplicated_video.description_en, "Original description")
        self.assertEqual(duplicated_video.date_evt, "2023-01-01")
        self.assertEqual(duplicated_video.main_lang, "en")
        self.assertEqual(duplicated_video.licence, "CC BY-SA")
        self.assertTrue(duplicated_video.is_draft)
        self.assertEqual(duplicated_video.is_restricted, False)
        self.assertEqual(duplicated_video.allow_downloading, True)
        self.assertEqual(duplicated_video.is_360, False)
        self.assertEqual(duplicated_video.date_delete, "2024-01-01")
        self.assertEqual(duplicated_video.disable_comment, False)

        # Check many-to-many relations
        self.assertEqual(list(duplicated_video.discipline.all()), [self.discipline])
        self.assertEqual(list(duplicated_video.channel.all()), [self.channel])
        self.assertEqual(list(duplicated_video.theme.all()), [self.theme])

        # Check the response status code
        self.assertEqual(
            response.status_code, 302
        )  # Redirect after successful duplication
