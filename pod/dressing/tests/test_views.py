"""Unit tests for Esup-Pod dressing views.

*  run with 'python manage.py test pod.dressing.tests.test_views'
"""

import unittest

from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from pod.dressing.forms import DressingDeleteForm
from pod.dressing.models import Dressing
from pod.video.models import Type, Video
from pod.main.models import Configuration

USE_DRESSING = getattr(settings, "USE_DRESSING", False)


@unittest.skipUnless(
    USE_DRESSING, "Set USE_DRESSING to True before testing Dressing stuffs."
)
class VideoDressingViewTest(TestCase):
    """Dressing page test case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up VideoDressingViewTest."""

        self.user = User.objects.create_user(
            username="user", password="password", is_staff=1
        )
        self.first_video = Video.objects.create(
            title="First video",
            slug="first-video",
            owner=self.user,
            video="first_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.dressing = Dressing.objects.create(title="Test Dressing")
        self.dressing.owners.set([self.user])
        self.dressing.users.set([self.user])
        self.dressing.videos.set([self.first_video])

    def test_maintenance(self) -> None:
        """Test Pod maintenance mode in VideoDressingViewTest."""
        self.client.force_login(self.user)
        url = reverse("dressing:video_dressing", args=[self.first_video.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        conf = Configuration.objects.get(key="maintenance_mode")
        conf.value = "1"
        conf.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/maintenance/")
        print(" --->  test_maintenance ok")

    def test_video_dressing_page(self) -> None:
        """Test test_video_dressing_page in MyDressingViewTest."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("dressing:video_dressing", args=[self.first_video.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "video_dressing.html")
        print(" --->  test_video_dressing_page ok")

    def test_video_encoding_in_progress(self) -> None:
        """Test video encoding in progress in VideoDressingViewTest."""
        self.first_video.encoding_in_progress = True
        self.first_video.save()
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("dressing:video_dressing", args=[self.first_video.slug])
        )
        messages = [m for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertEqual(messages[0].message, _("The video is currently being encoded."))
        print(" --->  test_video_encoding_in_progress ok")

    def test_video_dressing_permission_denied(self) -> None:
        """Test test_video_dressing_permission_denied in VideoDressingViewTest."""
        user_without_permission = User.objects.create_user(
            username="useless_user", password="testpass"
        )
        self.client.force_login(user_without_permission)
        response = self.client.get(
            reverse("dressing:video_dressing", args=[self.first_video.slug])
        )
        messages = [m for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertEqual(messages[0].message, _("You cannot dress this video."))
        print(" --->  test_video_dressing_permission_denied ok")


@unittest.skipUnless(
    USE_DRESSING, "Set USE_DRESSING to True before testing Dressing stuffs."
)
class MyDressingViewTest(TestCase):
    """My dressing page tests case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up MyDressingViewTest."""
        self.user = User.objects.create_user(
            username="user", password="password", is_staff=1
        )
        self.first_video = Video.objects.create(
            title="First video",
            slug="first-video",
            owner=self.user,
            video="first_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.dressing = Dressing.objects.create(title="Test Dressing")
        self.dressing.owners.set([self.user])
        self.dressing.users.set([self.user])
        self.dressing.videos.set([self.first_video])

    def test_maintenance(self) -> None:
        """Test Pod maintenance mode in MyDressingViewTest."""
        self.client.force_login(self.user)
        url = reverse("dressing:my_dressings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        conf = Configuration.objects.get(key="maintenance_mode")
        conf.value = "1"
        conf.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/maintenance/")
        print(" --->  test_maintenance ok")

    def test_my_dressing_page(self):
        """Test test_my_dressing_page in MyDressingViewTest."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("dressing:my_dressings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "my_dressings.html")
        print(" --->  test_my_dressing_page ok")

    def test_my_dressing_permission_denied(self):
        """Test test_my_dressing_permission_denied in MyDressingViewTest."""
        user_without_permission = User.objects.create_user(
            username="useless_user", password="testpass"
        )
        self.client.force_login(user_without_permission)
        response = self.client.get(reverse("dressing:my_dressings"))
        messages = [m for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "error")
        self.assertEqual(messages[0].message, _("You cannot access this page."))
        print(" --->  test_my_dressing_permission_denied ok")


@unittest.skipUnless(
    USE_DRESSING, "Set USE_DRESSING to True before testing Dressing stuffs."
)
class DressingEditViewTest(TestCase):
    """Dressing edit page tests case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up DressingEditViewTest."""
        self.user = User.objects.create_user(
            username="user", password="password", is_staff=1
        )
        self.first_video = Video.objects.create(
            title="First video",
            slug="first-video",
            owner=self.user,
            video="first_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.dressing = Dressing.objects.create(title="Test Dressing")
        self.dressing.owners.set([self.user])
        self.dressing.users.set([self.user])
        self.dressing.videos.set([self.first_video])

    def test_dressing_edit_page(self):
        """Test test_dressing_edit_page."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("dressing:dressing_edit", args=[self.dressing.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dressing_edit.html")
        print(" --->  test_my_dressing_page ok")

    def test_dressing_edit_view_permission_denied(self):
        """Test test_dressing_create_view_permission_denied."""
        user_without_permission = User.objects.create_user(
            username="nopermuser", password="testpass"
        )
        self.client.force_login(user_without_permission)
        response = self.client.get(
            reverse("dressing:dressing_edit", args=[self.dressing.id])
        )
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(_("You cannot edit this dressing."), messages)
        print(" --->  test_dressing_create_view_permission_denied ok")


@unittest.skipUnless(
    USE_DRESSING, "Set USE_DRESSING to True before testing Dressing stuffs."
)
class DressingDeleteViewTest(TestCase):
    """Dressing delete page test case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up DressingDeleteViewTest."""
        self.user = User.objects.create_user(
            username="user", password="password", is_staff=1
        )
        self.first_video = Video.objects.create(
            title="First video",
            slug="first-video",
            owner=self.user,
            video="first_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.dressing = Dressing.objects.create(title="Test Dressing")
        self.dressing.owners.set([self.user])
        self.dressing.users.set([self.user])
        self.dressing.videos.set([self.first_video])

    def test_maintenance(self):
        """Test Pod maintenance mode in VideoDressingViewTest."""
        self.client.force_login(self.user)
        url = reverse("dressing:dressing_delete", args=[self.dressing.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        conf = Configuration.objects.get(key="maintenance_mode")
        conf.value = "1"
        conf.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/maintenance/")
        print(" --->  test_maintenance ok")

    def test_dressing_delete_view_get(self):
        """Test test_dressing_delete_view_get."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("dressing:dressing_delete", args=[self.dressing.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dressing_delete.html")
        self.assertEqual(response.context["dressing"], self.dressing)
        self.assertIsInstance(response.context["form"], DressingDeleteForm)
        print(" --->  test_dressing_delete_view_get ok")

    def test_dressing_delete_view_get_not_authenticated(self):
        """Test test_dressing_delete_view_get_not_authenticated."""
        response = self.client.get(
            reverse("dressing:dressing_delete", args=[self.dressing.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        print(" --->  test_dressing_delete_view_get_not_authenticated ok")

    def test_dressing_delete_view_post(self):
        """Test test_dressing_delete_view_post."""
        self.client.force_login(self.user)
        self.assertEqual(Dressing.objects.filter(id=self.dressing.id).count(), 1)
        form_data = {"agree": True}
        response = self.client.post(
            reverse("dressing:dressing_delete", args=[self.dressing.id]), data=form_data
        )
        self.assertEqual(Dressing.objects.filter(id=self.dressing.id).count(), 0)
        self.assertRedirects(
            response,
            reverse("dressing:my_dressings"),
            status_code=302,
            target_status_code=200,
        )
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(_("The dressing has been deleted."), messages)
        print(" --->  test_dressing_delete_view_post ok")

    def test_dressing_delete_view_post_not_authenticated(self):
        """Test test_dressing_delete_view_post_not_authenticated."""
        form_data = {"agree": True}
        response = self.client.post(
            reverse("dressing:dressing_delete", args=[self.dressing.id]), data=form_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        self.assertEqual(Dressing.objects.filter(id=self.dressing.id).count(), 1)
        print(" --->  test_dressing_delete_view_post_not_authenticated ok")

    def test_dressing_delete_view_post_invalid_form(self):
        """Test test_dressing_delete_view_post_invalid_form."""
        self.client.force_login(self.user)
        form_data = {}  # Invalid form data
        response = self.client.post(
            reverse("dressing:dressing_delete", args=[self.dressing.id]), data=form_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dressing_delete.html")
        self.assertEqual(response.context["dressing"], self.dressing)
        self.assertIsInstance(response.context["form"], DressingDeleteForm)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn("One or more errors have been found in the form.", messages)
        print(" --->  test_dressing_delete_view_post_invalid_form ok")

    def test_dressing_delete_view_permission_denied(self):
        """Test test_dressing_delete_view_permission_denied."""
        user_without_permission = User.objects.create_user(
            username="nopermuser", password="testpass"
        )
        self.client.force_login(user_without_permission)
        self.client.get(reverse("dressing:dressing_delete", args=[self.dressing.id]))
        print(" --->  test_dressing_delete_view_permission_denied ok")

    def test_dressing_delete_view_not_authenticated(self):
        """Test test_dressing_delete_view_not_authenticated."""
        self.client.logout()
        response = self.client.get(
            reverse("dressing:dressing_delete", args=[self.dressing.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        print(" --->  test_dressing_delete_view_not_authenticated ok")


@unittest.skipUnless(
    USE_DRESSING, "Set USE_DRESSING to True before testing Dressing stuffs."
)
class DressingCreateViewTest(TestCase):
    """Dressing create page test case."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="user", password="password", is_staff=1
        )
        self.first_video = Video.objects.create(
            title="First video",
            slug="first-video",
            owner=self.user,
            video="first_video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.dressing = Dressing.objects.create(title="Test Dressing")
        self.dressing.owners.set([self.user])
        self.dressing.users.set([self.user])

    def test_dressing_create_view_authenticated_user(self):
        """Test test_dressing_create_view_authenticated_user."""
        self.client.login(username="user", password="password")
        response = self.client.get(reverse("dressing:dressing_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dressing_edit.html")
        print(" --->  test_dressing_create_view_authenticated_user ok")

    def test_dressing_create_view_unauthenticated_user(self):
        """Test test_dressing_create_view_unauthenticated_user."""
        response = self.client.get(reverse("dressing:dressing_create"))
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        print(" --->  test_dressing_create_view_unauthenticated_user ok")

    def test_dressing_create_form_submission(self):
        """Test test_dressing_create_form_submission."""
        Dressing.objects.all().delete()
        self.client.login(username="user", password="password")
        form_data = {
            "title": "Dressing test",
            "owners": self.user.id,
            "position": "top_right",
            "opacity": 50,
            "opening_credits": 1,
            "ending_credits": 1,
        }
        response = self.client.post(reverse("dressing:dressing_create"), data=form_data)
        self.assertEqual(
            response.status_code, 302
        )  # Redirect after creation of the video dressing
        self.assertEqual(Dressing.objects.count(), 1)
        print(" --->  test_dressing_create_form_submission ok")

    def test_dressing_create_view_permission_denied(self):
        """Test test_dressing_create_view_permission_denied."""
        user_without_permission = User.objects.create_user(
            username="nopermuser", password="testpass"
        )
        self.client.force_login(user_without_permission)
        response = self.client.get(reverse("dressing:dressing_create"))
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(_("You cannot create a video dressing."), messages)
        print(" --->  test_dressing_create_view_permission_denied ok")
