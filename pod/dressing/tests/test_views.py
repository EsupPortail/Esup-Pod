"""Unit tests for Esup-Pod dressing views."""

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from pod.dressing.forms import DressingDeleteForm
from pod.dressing.models import Dressing
from pod.video.models import Type, Video


class VideoDressingViewTest(TestCase):
    """Dressing page test case."""

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

    def test_video_dressing_view(self):
        """Test for video_dressing view."""

        print(" ---> test_video_dressing_view: OK! --- VideoDressingViewTest")


class DressingDeleteViewTest(TestCase):
    """Dressing delete page test case."""

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

    def test_dressing_delete_view_get(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("dressing:dressing_delete", args=[self.dressing.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dressing_delete.html")
        self.assertEqual(response.context["dressing"], self.dressing)
        self.assertIsInstance(response.context["form"], DressingDeleteForm)

    def test_dressing_delete_view_get_not_authenticated(self):
        response = self.client.get(
            reverse("dressing:dressing_delete", args=[self.dressing.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login page

    def test_dressing_delete_view_post(self):
        self.client.force_login(self.user)
        form_data = {"confirm_deletion": True}
        response = self.client.post(
            reverse("dressing:dressing_delete", args=[self.dressing.id]), data=form_data
        )
        self.assertEqual(response.status_code, 200)  # Redirect after successful deletion

    def test_dressing_delete_view_post_not_authenticated(self):
        form_data = {"confirm_deletion": True}
        response = self.client.post(
            reverse("dressing:dressing_delete", args=[self.dressing.id]), data=form_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login page
        self.assertEqual(Dressing.objects.filter(id=self.dressing.id).count(), 1)

    def test_dressing_delete_view_post_invalid_form(self):
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

    def test_dressing_delete_view_permission_denied(self):
        user_without_permission = User.objects.create_user(
            username="nopermuser", password="testpass"
        )
        self.client.force_login(user_without_permission)
        self.client.get(reverse("dressing:dressing_delete", args=[self.dressing.id]))

    def test_dressing_delete_view_not_authenticated(self):
        self.client.logout()
        response = self.client.get(
            reverse("dressing:dressing_delete", args=[self.dressing.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login page

    def test_dressing_video_delete(self):
        """Test for dressing_delete view."""
        print(" ---> test_dressing_video_delete: OK! --- DressingDeleteViewTest")


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
        self.client.login(username="user", password="password")
        response = self.client.get(reverse("dressing:dressing_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dressing_edit.html")

    def test_dressing_create_view_unauthenticated_user(self):
        response = self.client.get(reverse("dressing:dressing_create"))
        self.assertEqual(response.status_code, 302)  # Redirect to login page

    def test_dressing_create_form_submission(self):
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

    def test_dressing_video_create(self):
        """Test for dressing_create view."""
        print(" ---> test_dressing_video_create: OK! --- DressingCreateViewTest")
