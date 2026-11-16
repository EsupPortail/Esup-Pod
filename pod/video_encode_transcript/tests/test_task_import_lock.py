"""Regression tests for exclusive Runner result imports and retryable failures."""

import json
import subprocess
import sys
from contextlib import ExitStack
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.sites.models import Site
from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.utils import timezone

from pod.video_encode_transcript import views
from pod.video_encode_transcript.management.commands.process_tasks import Command
from pod.video_encode_transcript.models import RunnerManager, Task


class TaskImportLockTests(TestCase):
    """Serialize callback and cron imports using the actual shared file lock."""

    def setUp(self) -> None:
        """Create an aged Runner task and isolate downloaded artifacts and locks."""
        self.contexts = ExitStack()
        self.addCleanup(self.contexts.close)
        self.media_root = self.contexts.enter_context(TemporaryDirectory())
        self.contexts.enter_context(self.settings(MEDIA_ROOT=self.media_root))
        self.site, _ = Site.objects.get_or_create(
            pk=1, defaults={"domain": "example.com", "name": "example.com"}
        )
        self.runner = RunnerManager.objects.create(
            name="import-lock-runner",
            url="https://runner.example.com/",
            token="import-lock-token",
            site=self.site,
        )
        self.task = Task.objects.create(
            task_id="import-lock-task",
            runner_manager=self.runner,
            status="running",
            date_added=timezone.now() - timedelta(hours=3),
        )
        self.manifest_data = {"files": [{"path": "info_video.json"}]}
        self.manifest = self.contexts.enter_context(
            patch.object(
                views, "_get_task_result_manifest", return_value=self.manifest_data
            )
        )
        self.download = self.contexts.enter_context(
            patch.object(
                views, "_save_manifest_files", return_value=(self.media_root, "")
            )
        )
        self.real_finalize = views._finalize_task_import
        self.finalize = self.contexts.enter_context(
            patch.object(
                views, "_finalize_task_import", side_effect=self._complete_import
            )
        )
        self.command = Command()
        self.command._configure_output_logger(verbose=False, quiet=True)

    def _complete_import(
        self, task: Task, extracted_dir: str, extracted_vtt_path: str
    ) -> None:
        """Represent successful artifact persistence without creating media files."""
        task.status = "completed"
        task.save(update_fields=["status"])

    def _post_completed_callback(self) -> JsonResponse:
        """Send an authenticated completion callback through the actual view."""
        request = RequestFactory().post(
            "/runner/notify_task_end/",
            data=json.dumps({"task_id": self.task.task_id, "status": "completed"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.runner.token}",
        )
        return views.notify_task_end(request)

    def test_callback_during_cron_import_does_not_duplicate_import(self) -> None:
        """Ignore a completion callback while cron already imports the same task."""
        callback_responses = []

        def receive_callback(
            manifest: dict, task: Task, manager_url: str, bearer_token: str
        ) -> tuple[str, str]:
            """Deliver one callback while the outer import holds its file lock."""
            if not callback_responses:
                callback_responses.append(None)
                callback_responses[0] = self._post_completed_callback()
            return self.media_root, ""

        self.download.side_effect = receive_callback
        with patch.object(self.command, "_check_task_status", return_value="completed"):
            self.assertEqual(self.command._check_running_tasks(self.site), 1)

        self.assertEqual(callback_responses[0].status_code, 200)
        self.manifest.assert_called_once()
        self.download.assert_called_once()
        self.finalize.assert_called_once()
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")

    def test_cron_during_callback_import_does_not_duplicate_import(self) -> None:
        """Keep cron from importing an aged task already handled by its callback."""
        checked_tasks = []

        def run_cron(
            manifest: dict, task: Task, manager_url: str, bearer_token: str
        ) -> tuple[str, str]:
            """Run one cron pass during the callback's artifact download."""
            if not checked_tasks:
                checked_tasks.append(None)
                checked_tasks[0] = self.command._check_running_tasks(self.site)
            return self.media_root, ""

        self.download.side_effect = run_cron
        with patch.object(self.command, "_check_task_status", return_value="completed"):
            response = self._post_completed_callback()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(checked_tasks, [1])
        self.manifest.assert_called_once()
        self.download.assert_called_once()
        self.finalize.assert_called_once()

    def test_import_skips_task_completed_after_instance_was_loaded(self) -> None:
        """Read current completion state before starting another artifact download."""
        Task.objects.filter(pk=self.task.pk).update(status="completed")

        views.download_and_import_task_result(self.task)

        self.manifest.assert_not_called()
        self.download.assert_not_called()
        self.finalize.assert_not_called()
        self.assertEqual(self.task.status, "completed")

    def test_stale_completion_callback_does_not_reopen_completed_task(self) -> None:
        """Preserve a concurrent import's completion when persisting callback output."""
        Task.objects.filter(pk=self.task.pk).update(status="completed")

        views._apply_notify_payload_to_task(
            self.task, {"status": "completed", "script_output": "Runner finished"}
        )

        self.assertEqual(self.task.status, "completed")
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")
        self.assertEqual(self.task.script_output, "Runner finished")

    def test_retry_after_manifest_is_unavailable(self) -> None:
        """Release the lock when the Runner manifest cannot yet be retrieved."""
        self.manifest.side_effect = [None, self.manifest_data]

        views.download_and_import_task_result(self.task)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "running")
        self.download.assert_not_called()
        views.download_and_import_task_result(self.task)

        self.assertEqual(self.manifest.call_count, 2)
        self.finalize.assert_called_once()
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")

    def test_retry_after_download_does_not_produce_artifacts(self) -> None:
        """Release the lock when downloaded artifacts are unavailable."""
        self.download.side_effect = [("", ""), (self.media_root, "")]

        views.download_and_import_task_result(self.task)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "running")
        self.finalize.assert_not_called()
        views.download_and_import_task_result(self.task)

        self.assertEqual(self.download.call_count, 2)
        self.finalize.assert_called_once()
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")

    def test_retry_after_finalization_returns_without_completion(self) -> None:
        """Allow retry when finalization handles an error without completing the task."""
        self.task.type = "transcription"
        self.task.save(update_fields=["type"])
        self.finalize.side_effect = self.real_finalize

        with patch.object(
            views,
            "_import_transcription_result",
            side_effect=[RuntimeError("transcription import failed"), None],
        ) as import_transcription:
            views.download_and_import_task_result(self.task)
            self.task.refresh_from_db()
            self.assertEqual(self.task.status, "running")
            views.download_and_import_task_result(self.task)

        self.assertEqual(import_transcription.call_count, 2)
        self.assertEqual(self.finalize.call_count, 2)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")

    def test_retry_after_unhandled_download_exception(self) -> None:
        """Release the file lock even when artifact download raises an exception."""
        self.download.side_effect = [
            RuntimeError("interrupted download"),
            (self.media_root, ""),
        ]

        with self.assertRaisesRegex(RuntimeError, "interrupted download"):
            views.download_and_import_task_result(self.task)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "running")
        views.download_and_import_task_result(self.task)

        self.assertEqual(self.download.call_count, 2)
        self.finalize.assert_called_once()
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")

    def test_separate_tasks_can_import_while_another_task_is_locked(self) -> None:
        """Keep unrelated Runner tasks independent of an active task import."""
        other_task = Task.objects.create(
            task_id="another-import-task", runner_manager=self.runner, status="running"
        )

        with views._task_import_lock(self.task) as acquired:
            self.assertTrue(acquired)
            views.download_and_import_task_result(other_task)

        self.finalize.assert_called_once()
        other_task.refresh_from_db()
        self.assertEqual(other_task.status, "completed")

    def test_file_lock_coordinates_processes_and_survives_file_reuse(self) -> None:
        """Block another process and reuse the stable lock file after each holder exits."""
        lock_path = Path(self.media_root) / ".runner_task_locks" / f"{self.task.pk}.lock"
        child_script = (
            "import sys\n"
            "from django.core.files import locks\n"
            "handle = open(sys.argv[1], 'a+b')\n"
            "print(int(locks.lock(handle, locks.LOCK_EX | locks.LOCK_NB)))\n"
        )

        def acquire_in_child() -> str:
            """Try a real lock in another process and let process exit release it."""
            result = subprocess.run(
                [sys.executable, "-c", child_script, str(lock_path)],
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
            )
            return result.stdout.strip()

        with views._task_import_lock(self.task) as acquired:
            self.assertTrue(acquired)
            inode = lock_path.stat().st_ino
            self.assertEqual(acquire_in_child(), "0")

        self.assertEqual(acquire_in_child(), "1")
        with views._task_import_lock(self.task) as acquired:
            self.assertTrue(acquired)
            self.assertEqual(lock_path.stat().st_ino, inode)
