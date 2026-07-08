"""
Tests for the process_tasks management command runner delegation for Esup-Pod.

Run with `python manage.py test pod.video_encode_transcript.tests.test_process_tasks`
"""

from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from pod.video_encode_transcript.management.commands.process_tasks import Command


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
