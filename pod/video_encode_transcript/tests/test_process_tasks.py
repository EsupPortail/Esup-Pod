"""
Tests for the process_tasks management command runner delegation for Esup-Pod.

Run with `python manage.py test pod.video_encode_transcript.tests.test_process_tasks`
"""

import re
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from pod.video_encode_transcript.management.commands.process_tasks import Command


class ProcessTasksCommandOutputTests(SimpleTestCase):
    """Verify the command's concise and verbose output modes."""

    def setUp(self) -> None:
        self.output = StringIO()
        self.command = Command(stdout=self.output)
        self.site = SimpleNamespace(domain="example.com")

    def _run_empty_command(self, *, verbose: bool = False, verbosity: int = 1) -> None:
        empty_queryset = MagicMock()
        empty_queryset.__bool__.return_value = False
        empty_queryset.select_related.return_value.order_by.return_value = (
            empty_queryset
        )

        with (
            patch.object(self.command, "_get_site", return_value=self.site),
            patch.object(self.command, "_check_running_tasks", return_value=0),
            patch.object(self.command, "_delete_old_completed_tasks", return_value=0),
            patch(
                "pod.video_encode_transcript.management.commands.process_tasks.refresh_pending_task_ranks"
            ),
            patch(
                "pod.video_encode_transcript.management.commands.process_tasks.Task"
            ) as task_model,
        ):
            task_model.objects.filter.return_value = empty_queryset
            self.command.handle(
                max_tasks=20,
                site=None,
                verbose=verbose,
                verbosity=verbosity,
            )

    def test_default_empty_run_writes_one_timestamped_summary(self) -> None:
        self._run_empty_command()

        lines = self.output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertRegex(
            lines[0],
            re.compile(
                r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] INFO "
                r"process_tasks completed for site example\.com:"
            ),
        )
        self.assertIn("pending 0; submitted 0", lines[0])

    def test_verbose_empty_run_writes_timestamped_details(self) -> None:
        self._run_empty_command(verbose=True)

        lines = self.output.getvalue().splitlines()
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(re.match(r"^\[\d{4}-\d{2}-\d{2} ", line) for line in lines))
        self.assertTrue(any("1. Checking running tasks" in line for line in lines))
        self.assertTrue(any("pending 0; submitted 0" in line for line in lines))


class ProcessTasksCommandDelegationTests(SimpleTestCase):
    """Verify process_tasks delegates submissions to the public runner API."""

    def setUp(self) -> None:
        self.command = Command()
        self.site = SimpleNamespace(domain="example.com")
        self.runner_managers = [SimpleNamespace(name="runner-a")]

    @patch(
        "pod.video_encode_transcript.management.commands.process_tasks.submit_encoding_task",
        return_value=True,
    )
    def test_submit_encoding_task_uses_public_runner_api(
        self, mock_submit_encoding_task
    ) -> None:
        """Encoding submissions should not import private runner helpers."""
        video = SimpleNamespace(id=17)

        result = self.command._submit_encoding_task(
            video, self.site, self.runner_managers
        )

        self.assertTrue(result)
        mock_submit_encoding_task.assert_called_once_with(
            video=video,
            site=self.site,
            runner_managers=self.runner_managers,
        )

    @patch(
        "pod.video_encode_transcript.management.commands.process_tasks.submit_transcription_task",
        return_value=True,
    )
    def test_submit_transcription_task_uses_public_runner_api(
        self, mock_submit_transcription_task
    ) -> None:
        """Transcription submissions should not import private runner helpers."""
        video = SimpleNamespace(id=23)

        result = self.command._submit_transcription_task(
            video, self.site, self.runner_managers
        )

        self.assertTrue(result)
        mock_submit_transcription_task.assert_called_once_with(
            video=video,
            site=self.site,
            runner_managers=self.runner_managers,
        )

    @patch(
        "pod.video_encode_transcript.management.commands.process_tasks.submit_studio_task",
        return_value=True,
    )
    def test_submit_studio_task_uses_public_runner_api(
        self, mock_submit_studio_task
    ) -> None:
        """Studio submissions should not import private runner helpers."""
        recording = SimpleNamespace(id=31)

        result = self.command._submit_studio_task(
            recording, self.site, self.runner_managers
        )

        self.assertTrue(result)
        mock_submit_studio_task.assert_called_once_with(
            recording=recording,
            site=self.site,
            runner_managers=self.runner_managers,
        )
