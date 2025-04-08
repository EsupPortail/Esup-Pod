"""Unit tests for CutVideo views."""

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from pod.cut.models import CutVideo
from pod.video.models import Video, Type
from django.urls import reverse
from pod.main.models import Configuration
from datetime import time
from django.contrib.messages import get_messages
from django.utils.translation import gettext_lazy as _
from .. import views
from importlib import reload

# ggignore-start
# gitguardian:ignore
PWD = "azerty1234"  # nosec
# ggignore-end


class CutVideoViewsTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        self.user = User.objects.create(username="test", password=PWD, is_staff=True)
        self.user2 = User.objects.create(username="test2", password=PWD)
        self.video = Video.objects.create(
            title="videotest",
            owner=self.user,
            video="test.mp4",
            duration=20,
            type=Type.objects.get(id=1),
        )
        self.video.additional_owners.add(self.user2)

    def test_maintenance(self) -> None:
        """Test Pod maintenance mode in CutVideoViewsTestCase."""
        self.client.force_login(self.user)
        url = reverse("cut:video_cut", kwargs={"slug": self.video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        conf = Configuration.objects.get(key="maintenance_mode")
        conf.value = "1"
        conf.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/maintenance/")
        print(" --->  test_maintenance ok")

    def test_get_full_duration(self) -> None:
        """Test test_get_full_duration."""
        CutVideo.objects.create(
            video=self.video, start=time(0, 0, 0), end=time(0, 0, 10), duration="00:00:10"
        )

        duration = self.video.duration_in_time
        if CutVideo.objects.filter(video=self.video).exists():
            cutting = CutVideo.objects.get(video=self.video)
            duration = cutting.duration_in_int

        self.assertEqual(duration, 10)
        print(" --->  test_get_full_duration ok")

    @override_settings(RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=True, USE_CUT=True)
    def test_restrict_edit_video_access_staff_only(self) -> None:
        """Test test_restrict_edit_video_access_staff_only."""
        reload(views)
        self.client.force_login(self.user2)
        url = reverse("cut:video_cut", kwargs={"slug": self.video.slug})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_cut.html")
        self.assertTrue(response.context["access_not_allowed"])

        self.client.logout()
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_cut.html")
        self.assertFalse(response.context["access_not_allowed"])

        print(" --->  test_restrict_edit_video_access_staff_only ok")

    def test_post_cut_valid_form(self) -> None:
        """Test test_post_cut_valid_form."""
        self.client.force_login(self.user)
        post_data = {
            "video": self.video.id,
            "start": "00:00:00",
            "end": "00:00:10",
            "duration": 10,
        }

        response = self.client.post(
            reverse("cut:video_cut", kwargs={"slug": self.video.slug}), data=post_data
        )

        self.assertTrue(CutVideo.objects.filter(video=self.video).exists())
        self.assertRedirects(response, reverse("video:dashboard"))
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(_("The cut was made."), messages)

        print(" --->  test_post_cut_valid_form ok")

    def test_post_cut_invalid_form(self) -> None:
        """Test test_post_cut_invalid_form."""
        self.client.force_login(self.user)
        post_data = {
            "video": self.video.id,
            "start": "00:00:10",
            "end": "00:00:00",
            "duration": 10,
        }
        response = self.client.post(
            reverse("cut:video_cut", kwargs={"slug": self.video.slug}), data=post_data
        )
        self.assertFalse(CutVideo.objects.filter(video=self.video).exists())
        self.assertEqual(response.status_code, 200)

        messages = [m.message for m in get_messages(response.wsgi_request)]
        print("MESSAGE", messages)
        self.assertIn(_("Please select values between 00:00:00 and 00:00:20."), messages)

        print(" --->  test_post_cut_invalid_form ok")
