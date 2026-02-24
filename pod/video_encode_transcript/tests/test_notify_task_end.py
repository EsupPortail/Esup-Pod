"""
Notify-task-end authentication tests for Esup-Pod.

Run with `python manage.py test pod.video_encode_transcript.tests.test_notify_task_end`
"""

import json
from unittest.mock import patch

from django.contrib.sites.models import Site
from django.test import RequestFactory, TestCase

from pod.video_encode_transcript.models import RunnerManager, Task
from pod.video_encode_transcript.views import notify_task_end


class NotifyTaskEndAuthTests(TestCase):
    """Authentication coverage for the notify_task_end endpoint."""

    def setUp(self) -> None:
        """Create a runner manager and a pending task used in all test cases."""
        self.factory = RequestFactory()
        site = Site.objects.filter(pk=1).first() or Site.objects.first()
        if site is None:
            site = Site.objects.create(domain="example.com", name="example.com")

        self.runner_manager = RunnerManager.objects.create(
            name="rm-test",
            priority=1,
            url="https://runner.example.com/",
            token="runner-token",
            site=site,
        )
        self.task = Task.objects.create(
            task_id="task-123",
            runner_manager=self.runner_manager,
            status="pending",
        )

    def _post_notify(self, authorization: str | None = None, status: str = "running"):
        """Send a JSON notify_task_end request with an optional bearer token."""
        headers = {}
        if authorization is not None:
            headers["HTTP_AUTHORIZATION"] = authorization
        return notify_task_end(
            self.factory.post(
                "/runner/notify_task_end/",
                data=json.dumps({"task_id": self.task.task_id, "status": status}),
                content_type="application/json",
                **headers,
            )
        )

    def test_notify_task_end_requires_bearer_token(self):
        """Return 401 and keep task unchanged when the Authorization header is missing."""
        response = self._post_notify()
        self.assertEqual(response.status_code, 401)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "pending")

    def test_notify_task_end_rejects_invalid_bearer_token(self):
        """Return 403 and keep task unchanged when the bearer token is invalid."""
        response = self._post_notify("Bearer wrong-token")
        self.assertEqual(response.status_code, 403)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "pending")

    def test_notify_task_end_accepts_runner_manager_token(self):
        """Accept a valid runner token and update the task status from payload data."""
        response = self._post_notify("Bearer runner-token")
        self.assertEqual(response.status_code, 200)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "running")

    @patch("pod.video_encode_transcript.views.send_email_item")
    def test_notify_task_end_sends_alert_on_failed_status(self, mock_send_email_item):
        """Send an alert email when runner notifies a failed task."""
        response = self._post_notify("Bearer runner-token", status="failed")
        self.assertEqual(response.status_code, 200)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "failed")
        mock_send_email_item.assert_called_once_with(
            f"Task {self.task.id} failed", "Task", self.task.task_id
        )
