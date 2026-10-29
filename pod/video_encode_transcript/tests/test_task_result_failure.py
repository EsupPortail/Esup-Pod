"""Esup-Pod tests for missing Runner results and retryable download failures."""

import json
from contextlib import ExitStack
from datetime import timedelta
from tempfile import TemporaryDirectory
from unittest.mock import patch

import requests
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import RequestFactory, TestCase
from django.utils import timezone

from pod.video.models import Type, Video
from pod.video_encode_transcript import views
from pod.video_encode_transcript.management.commands.process_tasks import Command
from pod.video_encode_transcript.models import EncodingStep, RunnerManager, Task


class TaskResultFailureTests(TestCase):
    """Stop polling missing results without treating transient failures as terminal."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Create an aged task with existing logs and isolate its import lock."""
        self.contexts = ExitStack()
        self.addCleanup(self.contexts.close)
        media_root = self.contexts.enter_context(TemporaryDirectory())
        self.contexts.enter_context(self.settings(MEDIA_ROOT=media_root))
        self.site = Site.objects.get(pk=1)
        self.runner = RunnerManager.objects.create(
            name="missing-result-runner",
            url="https://runner.example.com/",
            token="missing-result-token",
            site=self.site,
        )
        self.video = Video.objects.create(
            title="Missing result video",
            owner=User.objects.create(username="missing-result-owner"),
            video="missing-result.mp4",
            type=Type.objects.get(pk=1),
            encoding_in_progress=True,
        )
        self.task = Task.objects.create(
            task_id="missing-result-task",
            runner_manager=self.runner,
            video=self.video,
            status="running",
            script_output="Existing runner output\n",
            date_added=timezone.now() - timedelta(days=8),
        )
        self.download = self.contexts.enter_context(
            patch.object(views, "_save_manifest_files")
        )
        self.finalize = self.contexts.enter_context(
            patch.object(views, "_finalize_task_import")
        )
        self.command = Command()
        self.command._configure_output_logger(verbose=False, quiet=True)

    def _response(self, status: int, payload: dict) -> requests.Response:
        """Use actual Responses to preserve requests' falsey HTTP error behavior."""
        response = requests.Response()
        response.status_code = status
        response._content = json.dumps(payload).encode()
        return response

    def _assert_missing_result_failed(self) -> None:
        """Check persisted task details, video state and interrupted artifact import."""
        self.task.refresh_from_db()
        self.video.refresh_from_db()
        self.assertEqual(self.task.status, "failed")
        self.assertTrue(self.task.script_output.startswith("Existing runner output\n"))
        self.assertIn("HTTP 404", self.task.script_output)
        self.assertIn("MAX_FILE_AGE_DAYS", self.task.script_output)
        self.assertFalse(self.video.encoding_in_progress)
        encoding_step = EncodingStep.objects.get(video=self.video)
        self.assertEqual(encoding_step.num_step, -1)
        self.assertIn("HTTP 404", encoding_step.desc_step)
        self.download.assert_not_called()
        self.finalize.assert_not_called()

    def test_cron_fails_missing_result_and_stops_polling(self) -> None:
        """Fail completed/warning tasks when cleanup removed their remote result."""
        for remote_status in ("completed", "warning"):
            with self.subTest(remote_status=remote_status):
                Task.objects.filter(pk=self.task.pk).update(
                    status="running", script_output="Existing runner output\n"
                )
                Video.objects.filter(pk=self.video.pk).update(encoding_in_progress=True)
                with patch.object(
                    views.requests,
                    "get",
                    side_effect=[
                        self._response(200, {"status": remote_status}),
                        self._response(
                            404, {"detail": "Error fetching result from runner"}
                        ),
                    ],
                ) as get:
                    self.assertEqual(self.command._check_running_tasks(self.site), 1)
                    self._assert_missing_result_failed()
                    self.assertEqual(self.command._check_running_tasks(self.site), 0)

                self.assertEqual(get.call_count, 2)
                self.assertEqual(
                    get.call_args.args[0],
                    f"{self.runner.url}task/result/{self.task.task_id}",
                )

    def test_completion_callback_fails_missing_result(self) -> None:
        """Apply the same terminal error when a completion callback fetches a 404."""
        request = RequestFactory().post(
            "/runner/notify_task_end/",
            data=json.dumps({"task_id": self.task.task_id, "status": "completed"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.runner.token}",
        )
        with patch.object(
            views.requests,
            "get",
            return_value=self._response(
                404, {"detail": "Error fetching result from runner"}
            ),
        ):
            response = views.notify_task_end(request)

        self.assertEqual(response.status_code, 200)
        self._assert_missing_result_failed()

    def test_missing_result_fails_all_task_types_without_video(self) -> None:
        """Also fail transcription and Studio tasks without requiring a linked video."""
        for task_type, _ in Task.TYPE:
            with self.subTest(task_type=task_type):
                task = Task.objects.create(
                    task_id=f"missing-{task_type}",
                    type=task_type,
                    status="running",
                    runner_manager=self.runner,
                )
                with patch.object(
                    views.requests,
                    "get",
                    return_value=self._response(404, {"detail": "Not found"}),
                ):
                    views.download_and_import_task_result(task)

                task.refresh_from_db()
                self.assertEqual(task.status, "failed")
                self.assertIn("HTTP 404", task.script_output)

        self.download.assert_not_called()
        self.finalize.assert_not_called()

    def test_other_http_errors_remain_retryable(self) -> None:
        """Keep task logs and video state intact on authentication or server errors."""
        for status in (401, 403, 429, 500, 503):
            with self.subTest(status=status), patch.object(
                views.requests, "get", return_value=self._response(status, {})
            ):
                views.download_and_import_task_result(self.task)
                self._assert_retryable_failure()

    def test_network_errors_remain_retryable(self) -> None:
        """Keep the task running after a timeout or an interrupted connection."""
        for error in (requests.Timeout("timeout"), requests.ConnectionError("offline")):
            with self.subTest(error=error), patch.object(
                views.requests, "get", side_effect=error
            ):
                views.download_and_import_task_result(self.task)
                self._assert_retryable_failure()

    def _assert_retryable_failure(self) -> None:
        """Ensure transient download failures do not finalize the task or video."""
        self.task.refresh_from_db()
        self.video.refresh_from_db()
        self.assertEqual(self.task.status, "running")
        self.assertEqual(self.task.script_output, "Existing runner output\n")
        self.assertTrue(self.video.encoding_in_progress)
        self.assertFalse(
            EncodingStep.objects.filter(video=self.video, num_step=-1).exists()
        )
        self.download.assert_not_called()
        self.finalize.assert_not_called()
