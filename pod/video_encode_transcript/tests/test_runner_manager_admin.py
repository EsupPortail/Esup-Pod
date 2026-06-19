"""
Runner manager admin interface tests for Esup-Pod.

Run with `python manage.py test pod.video_encode_transcript.tests.test_runner_manager_admin`
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.sites.models import Site
from django.test import TestCase
from django.urls import reverse
from requests import RequestException

from pod.video_encode_transcript.models import RunnerManager


class RunnerManagerAdminTests(TestCase):
    """Ensure admin actions and feedback for runner manager connectivity."""

    def setUp(self) -> None:
        """Create a superuser client session and one runner manager instance."""
        user_model = get_user_model()
        self.admin_user = user_model.objects.create_superuser(
            username="admin-rm-test",
            email="admin-rm-test@example.com",
            password="admin-rm-test",
        )
        self.client.force_login(self.admin_user)

        site = Site.objects.filter(pk=1).first() or Site.objects.first()
        if site is None:
            site = Site.objects.create(domain="example.com", name="example.com")

        self.runner_manager = RunnerManager.objects.create(
            name="rm-admin-test",
            priority=1,
            url="https://runner.example.com/",
            token="runner-token",
            site=site,
        )
        self.change_url = reverse(
            "admin:video_encode_transcript_runnermanager_change",
            args=[self.runner_manager.pk],
        )
        self.test_connection_url = reverse(
            "admin:video_encode_transcript_runnermanager_test_connection",
            args=[self.runner_manager.pk],
        )

    def _messages(self, response):
        """Extract Django message strings from a response."""
        return [str(message) for message in get_messages(response.wsgi_request)]

    def test_change_page_displays_test_connection_button(self):
        """Display the custom test-connection button on the admin change form."""
        response = self.client.get(self.change_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test connection")
        self.assertContains(response, "test-connection-link")
        self.assertContains(response, self.test_connection_url)
        self.assertContains(response, "runner-admin-link")
        self.assertContains(response, "https://runner.example.com/admin")

    def test_change_page_runner_admin_link_handles_url_without_trailing_slash(self):
        """Build remote admin URL correctly when runner URL has no trailing slash."""
        self.runner_manager.url = "https://runner-no-slash.example.com"
        self.runner_manager.save(update_fields=["url"])

        response = self.client.get(self.change_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "runner-admin-link")
        self.assertContains(response, "https://runner-no-slash.example.com/admin")

    def test_changelist_displays_activation_badge(self):
        """Display activation badge in runner manager changelist."""
        changelist_url = reverse("admin:video_encode_transcript_runnermanager_changelist")
        source_app_url = reverse(
            "admin:app_list",
            kwargs={"app_label": "video_encode_transcript"},
        )

        response = self.client.get(changelist_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bg-success")
        self.assertContains(response, "Active")
        self.assertContains(response, "runner-admin-list-link")
        self.assertContains(response, "https://runner.example.com/admin")
        self.assertContains(response, "Runner managers")
        self.assertNotContains(response, f'href="{source_app_url}"')

        self.runner_manager.is_active = False
        self.runner_manager.save(update_fields=["is_active"])
        response = self.client.get(changelist_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bg-secondary")
        self.assertContains(response, "Inactive")

    def test_task_changelist_uses_runner_manager_breadcrumb(self):
        """Display a runner manager breadcrumb entry in task changelist."""
        task_changelist_url = reverse("admin:video_encode_transcript_task_changelist")
        runner_changelist_url = reverse(
            "admin:video_encode_transcript_runnermanager_changelist"
        )

        response = self.client.get(task_changelist_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, runner_changelist_url)
        self.assertContains(response, "Runner managers")

    def test_priority_user_changelist_uses_runner_manager_breadcrumb(self):
        """Display a runner manager breadcrumb entry in priority user changelist."""
        priority_user_changelist_url = reverse(
            "admin:video_encode_transcript_priorityuser_changelist"
        )
        runner_changelist_url = reverse(
            "admin:video_encode_transcript_runnermanager_changelist"
        )

        response = self.client.get(priority_user_changelist_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, runner_changelist_url)
        self.assertContains(response, "Runner managers")

    def test_video_encode_transcript_app_index_hides_runner_models(self):
        """Hide runner manager models from the source app index page."""
        app_index_url = reverse(
            "admin:app_list",
            kwargs={"app_label": "video_encode_transcript"},
        )
        response = self.client.get(app_index_url)

        self.assertEqual(response.status_code, 200)
        app_list = response.context["app_list"]
        self.assertEqual(len(app_list), 1)
        self.assertEqual(app_list[0]["app_label"], "video_encode_transcript")

        model_names = [model["object_name"] for model in app_list[0]["models"]]
        self.assertNotIn("RunnerManager", model_names)
        self.assertNotIn("PriorityUser", model_names)
        self.assertNotIn("Task", model_names)

    def test_admin_index_groups_runner_models_in_dedicated_section(self):
        """Display runner manager admin entries in a dedicated dashboard section."""
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

        app_list = response.context["app_list"]
        runner_app = next(
            (
                app
                for app in app_list
                if app["app_label"] == "runner_managers"
                and app["name"] == "Runner managers"
            ),
            None,
        )
        self.assertIsNotNone(runner_app)

        runner_model_names = [model["object_name"] for model in runner_app["models"]]
        self.assertCountEqual(
            runner_model_names,
            ["RunnerManager", "PriorityUser", "Task"],
        )
        self.assertEqual(
            runner_app["app_url"],
            reverse("admin:video_encode_transcript_runnermanager_changelist"),
        )

        encode_app = next(
            (app for app in app_list if app["app_label"] == "video_encode_transcript"),
            None,
        )
        self.assertIsNotNone(encode_app)
        encode_model_names = [model["object_name"] for model in encode_app["models"]]
        self.assertNotIn("RunnerManager", encode_model_names)
        self.assertNotIn("PriorityUser", encode_model_names)
        self.assertNotIn("Task", encode_model_names)

    @patch("pod.video_encode_transcript.admin.requests.get")
    def test_test_connection_reports_unreachable_runner(self, mocked_get):
        """Show an explicit error message when the runner endpoint is unreachable."""
        mocked_get.side_effect = RequestException("connection refused")

        response = self.client.get(self.test_connection_url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(
                "Unable to reach runner manager" in message
                for message in self._messages(response)
            )
        )

    @patch("pod.video_encode_transcript.admin.requests.get")
    def test_test_connection_reports_invalid_token(self, mocked_get):
        """Show an authentication error when runner manager rejects the token."""
        mocked_get.return_value = Mock(status_code=401)

        response = self.client.get(self.test_connection_url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(
                "rejected authentication" in message
                for message in self._messages(response)
            )
        )
        mocked_get.assert_called_once_with(
            "https://runner.example.com/manager/health",
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer runner-token",
            },
            timeout=15,
        )

    @patch("pod.video_encode_transcript.admin.requests.get")
    def test_test_connection_reports_success(self, mocked_get):
        """Show a success message when health endpoint validates the runner token."""
        mocked_get.return_value = Mock(status_code=200)

        response = self.client.get(self.test_connection_url, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(
                "Connection to runner manager" in message
                for message in self._messages(response)
            )
        )
        mocked_get.assert_called_once_with(
            "https://runner.example.com/manager/health",
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer runner-token",
            },
            timeout=15,
        )
