"""Esup-Pod regression tests for warnings from successful Runner tasks.

Run with `python manage.py test pod.video_encode_transcript.tests.test_task_warnings`.
"""

import json
from contextlib import ExitStack
from datetime import timedelta
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override

from pod.recorder.models import Recorder, Recording
from pod.video import views as video_views
from pod.video.models import Type, Video
from pod.video_encode_transcript import views
from pod.video_encode_transcript.management.commands.process_tasks import Command
from pod.video_encode_transcript.models import (
    EncodingLog,
    EncodingStep,
    RunnerManager,
    Task,
)
from pod.video_encode_transcript.runner_warnings import format_runner_warnings
from pod.video_encode_transcript.utils import change_encoding_step


class TaskWarningsTests(TestCase):
    """Cover callbacks, periodic recovery and the alerts on both video pages."""

    fixtures = ["initial_data.json"]
    warning = "Encoding incomplete: output duration is 60s instead of 120s."
    heading = "This video was processed with warnings. Please check the result."
    incomplete_message = (
        "Part of the video is missing: the resulting video is shorter than expected. "
        "Please check the source file and re-upload a valid, complete video file."
    )

    def setUp(self) -> None:
        """Stub artifact downloads while exercising the real import and callback flow."""
        contexts = ExitStack()
        self.addCleanup(contexts.close)
        media_root = contexts.enter_context(TemporaryDirectory())
        contexts.enter_context(self.settings(MEDIA_ROOT=media_root))
        contexts.enter_context(patch.object(video_views, "USE_RUNNER_MANAGER", True))
        self.owner = User.objects.create(username="warnings-owner", is_staff=True)
        self.runner = RunnerManager.objects.create(
            name="warnings-runner",
            url="https://runner.example.com/",
            token="warnings-token",
            site=Site.objects.get(pk=1),
        )
        self.video = Video.objects.create(
            title="Video with warnings",
            owner=self.owner,
            video="warnings.mp4",
            type=Type.objects.get(pk=1),
            encoding_in_progress=True,
        )
        self.task = Task.objects.create(
            task_id="warnings-task",
            runner_manager=self.runner,
            video=self.video,
            status="running",
            date_added=timezone.now() - timedelta(hours=3),
        )
        change_encoding_step(self.video.pk, 3, "process manager remote encode")
        contexts.enter_context(
            patch.object(views, "_get_task_result_manifest", return_value={"files": []})
        )
        contexts.enter_context(
            patch.object(views, "_save_manifest_files", return_value=(media_root, ""))
        )
        self.import_artifacts = contexts.enter_context(
            patch.object(
                views,
                "store_after_remote_encoding_video",
                side_effect=self._finish_video,
            )
        )

    def _finish_video(self, video_id: int) -> None:
        """Represent the video state left by a successful artifact import.

        Args:
            video_id: Video whose encoding step and progress flag must be updated.
        """
        change_encoding_step(video_id, 0, "done")
        Video.objects.filter(pk=video_id).update(encoding_in_progress=False)

    def _notify(self, **payload):
        """Send an authenticated completion callback using the Runner schema.

        Args:
            **payload: Additional callback fields, including optional warnings.

        Returns:
            The JSON response returned by the notification view.
        """
        return views.notify_task_end(
            RequestFactory().post(
                "/runner/notify_task_end/",
                data=json.dumps(
                    {"task_id": self.task.task_id, "status": "completed", **payload}
                ),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {self.runner.token}",
            )
        )

    def _render_warning(self, use_runner_manager: bool = True) -> str:
        """Render the shared alert using fresh video state.

        Args:
            use_runner_manager: Whether Runner Manager is enabled for the page.

        Returns:
            Rendered HTML for the warning block.
        """
        return render_to_string(
            "videos/video_processing_warnings.html",
            {
                "video": Video.objects.get(pk=self.video.pk),
                "USE_RUNNER_MANAGER": use_runner_manager,
            },
        )

    def test_completed_callback_persists_warnings_and_keeps_video_playable(
        self,
    ) -> None:
        """Retain diagnostics after successful import without creating an error step."""
        with patch.object(views, "send_email_item") as alert_email:
            response = self._notify(warnings=[self.warning], script_output="Runner log")

        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.video.refresh_from_db()
        self.assertEqual(self.task.status, "completed")
        self.assertEqual(self.task.warnings, [self.warning])
        self.assertIn("Runner log", self.task.script_output)
        self.assertFalse(self.video.encoding_in_progress)
        self.assertEqual(self.video.encodingstep.num_step, 0)
        self.assertEqual(self.video.encodinglog.warnings, [self.warning])
        alert_email.assert_not_called()

    def test_video_and_edit_pages_display_warning_alert(self) -> None:
        """Show the same translated warning on the video page and its edit form."""
        self._notify(warnings=[self.warning])
        self.client.force_login(self.owner)
        for view in ("video:video", "video:video_edit"):
            with self.subTest(view=view):
                response = self.client.get(
                    reverse(view, kwargs={"slug": self.video.slug})
                )
                self.assertContains(response, self.heading)
                self.assertContains(response, self.incomplete_message)
                self.assertContains(response, 'class="alert alert-warning" role="alert"')
                self.assertNotContains(
                    response, "Our administrators have already been notified."
                )

    def test_video_and_edit_pages_deduplicate_incomplete_warnings(self) -> None:
        """Show one explanation for distinct audio and video duration diagnostics."""
        warnings = [
            "Encoding incomplete: video output duration is 60s instead of 120s.",
            "Encoding incomplete: audio output duration is 80s instead of 120s.",
        ]
        self._notify(warnings=warnings)
        self.client.force_login(self.owner)
        for view in ("video:video", "video:video_edit"):
            with self.subTest(view=view):
                response = self.client.get(
                    reverse(view, kwargs={"slug": self.video.slug})
                )
                self.assertContains(response, self.incomplete_message, count=1)

        self.task.refresh_from_db()
        self.assertEqual(self.task.warnings, warnings)
        self.assertEqual(EncodingLog.objects.get(video=self.video).warnings, warnings)

    def test_displayed_warning_messages_are_deduplicated(self) -> None:
        """Deduplicate displayed English text while retaining other warning messages."""
        other_warning = "Check the subtitle track <French>."
        self._notify(
            warnings=[
                self.warning,
                other_warning,
                "Encoding incomplete: audio is truncated.",
            ]
        )
        with override("en"):
            rendered = self._render_warning()

        self.assertEqual(rendered.count(self.incomplete_message), 1)
        self.assertEqual(rendered.count("Check the subtitle track &lt;French&gt;."), 1)
        self.assertEqual(rendered.count("<li>"), 2)

    def test_periodic_recovery_imports_completed_task_with_warnings(self) -> None:
        """Keep status endpoint warnings when the completion callback was missed."""
        command = Command()
        command._configure_output_logger(verbose=False, quiet=True)
        response = Mock(status_code=200)
        response.json.return_value = {"status": "completed", "warnings": [self.warning]}
        with patch.object(views.requests, "get", return_value=response):
            self.assertEqual(command._check_running_tasks(self.runner.site), 1)

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")
        self.assertEqual(self.task.warnings, [self.warning])
        self.assertIn(self.incomplete_message, self._render_warning())

    def test_video_and_edit_pages_hide_warning_when_runner_manager_disabled(
        self,
    ) -> None:
        """Hide stored Runner diagnostics when Pod switches to another encoding mode."""
        self._notify(warnings=[self.warning])
        self.client.force_login(self.owner)
        with patch.object(video_views, "USE_RUNNER_MANAGER", False):
            for view in ("video:video", "video:video_edit"):
                with self.subTest(view=view):
                    response = self.client.get(
                        reverse(view, kwargs={"slug": self.video.slug})
                    )
                    self.assertEqual(response.context["USE_RUNNER_MANAGER"], False)
                    self.assertNotContains(response, self.heading)
                    self.assertNotContains(response, self.incomplete_message)
        self.assertNotIn(self.heading, self._render_warning(use_runner_manager=False))

    def test_ordinary_encoding_logs_do_not_generate_runner_warning(self) -> None:
        """Keep ordinary encoder log messages outside the Runner warning display."""
        self._finish_video(self.video.pk)
        EncodingLog.objects.create(
            video=self.video, log=f"FFmpeg warnings:\nWARNING: {self.warning}"
        )
        self.assertNotIn(self.heading, self._render_warning())

    def test_warnings_are_retained_during_retryable_import_failure(self) -> None:
        """Do not display a successful-processing warning before import succeeds."""
        self.import_artifacts.side_effect = RuntimeError("Temporary import failure")
        self._notify(warnings=[self.warning])
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "running")
        self.assertEqual(self.task.warnings, [self.warning])
        self.assertNotIn(self.heading, self._render_warning())

        self.import_artifacts.side_effect = self._finish_video
        views.download_and_import_task_result(self.task)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")
        self.assertIn(self.heading, self._render_warning())

    def test_absent_empty_or_malformed_warnings_do_not_break_completion(self) -> None:
        """Support older Runners and ignore values outside the list-of-strings schema."""
        for payload in ({}, {"warnings": []}, {"warnings": None}, {"warnings": "text"}):
            with self.subTest(payload=payload):
                Task.objects.filter(pk=self.task.pk).update(status="running")
                self.assertEqual(self._notify(**payload).status_code, 200)
                self.task.refresh_from_db()
                self.assertEqual(self.task.status, "completed")
                self.assertEqual(self.task.warnings, [])
                self.assertNotIn(self.heading, self._render_warning())

    def test_warning_messages_are_normalized_and_html_is_escaped(self) -> None:
        """Ignore empty/non-string entries and render unrecognized diagnostics safely."""
        warning = '<script>alert("warning")</script>'
        self._notify(warnings=[None, " ", 1, warning, f" {warning} "])
        self.task.refresh_from_db()
        self.assertEqual(self.task.warnings, [warning])
        rendered = self._render_warning()
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)

    def test_repeated_callback_without_warnings_preserves_diagnostics(self) -> None:
        """Keep the original warning when a completion callback is replayed."""
        self._notify(warnings=[self.warning])
        self._notify()
        self.assertEqual(self.import_artifacts.call_count, 1)
        self.task.refresh_from_db()
        self.assertEqual(self.task.warnings, [self.warning])
        self.assertIn(self.incomplete_message, self._render_warning())

    def test_callback_during_import_preserves_warning_and_script_output(self) -> None:
        """Keep metadata received while another worker already holds the import lock."""

        def finish_with_callback(video_id):
            """Deliver a late notification before completing the video import."""
            self._notify(warnings=[self.warning], script_output="Late Runner log")
            self._finish_video(video_id)

        self.import_artifacts.side_effect = finish_with_callback
        self._notify()
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")
        self.assertEqual(self.task.warnings, [self.warning])
        self.assertIn("Late Runner log", self.task.script_output)
        self.assertEqual(self.import_artifacts.call_count, 1)
        self.assertIn(self.incomplete_message, self._render_warning())

    def test_warning_survives_completed_task_cleanup(self) -> None:
        """Persist video warnings independently of the task retention policy."""
        self._notify(warnings=[self.warning])
        self.task.delete()
        self.assertIn(self.incomplete_message, self._render_warning())

    def test_new_encoding_clears_previous_warning(self) -> None:
        """Remove obsolete diagnostics when the source is encoded again."""
        self._notify(warnings=[self.warning])
        change_encoding_step(self.video.pk, 0, "start")
        self.assertEqual(EncodingLog.objects.get(video=self.video).warnings, [])
        self.assertNotIn(self.heading, self._render_warning())

    def test_clean_import_clears_previous_warning(self) -> None:
        """Replace old video warnings when a subsequent encoding succeeds cleanly."""
        EncodingLog.objects.create(
            video=self.video, log=format_runner_warnings([self.warning])
        )
        self._notify(warnings=[])
        self.assertNotIn(self.heading, self._render_warning())

    def test_transcription_preserves_existing_encoding_warnings(self) -> None:
        """An unrelated successful transcription must not hide incomplete encoding."""
        EncodingLog.objects.create(
            video=self.video, log=format_runner_warnings([self.warning])
        )
        Task.objects.filter(pk=self.task.pk).update(type="transcription")
        with patch.object(
            views,
            "_import_transcription_result",
            side_effect=lambda *args: self._finish_video(self.video.pk),
        ):
            self._notify()
        self.assertIn(self.incomplete_message, self._render_warning())

    def test_studio_warnings_are_attached_to_the_created_video(self) -> None:
        """Handle Studio tasks whose video only exists after the import starts."""
        recorder = Recorder.objects.create(
            name="warnings-recorder", address_ip="192.0.2.1", type=self.video.type
        )
        recording = Recording.objects.create(
            title="Studio recording",
            user=self.owner,
            recorder=recorder,
            source_file="/nonexistent/studio-warning.mp4",
        )
        Task.objects.filter(pk=self.task.pk).update(
            type="studio", video=None, recording=recording
        )
        with (
            patch.object(
                views, "_create_video_from_studio_task", return_value=self.video.pk
            ),
            patch.object(views, "store_remote_encoding_log_recording"),
        ):
            self._notify(warnings=[self.warning])
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")
        self.assertIn(self.incomplete_message, self._render_warning())

    def test_warning_alert_is_displayed_in_english(self) -> None:
        """Use the same English incomplete-video explanation as failed task errors."""
        self._notify(warnings=[self.warning])
        with override("en"):
            rendered = self._render_warning()
        self.assertIn(self.heading, rendered)
        self.assertIn(self.incomplete_message, rendered)

    def test_warning_support_does_not_add_database_fields(self) -> None:
        """Keep warnings in existing logs without extending any model's schema."""
        for model in (Task, EncodingLog, EncodingStep):
            with self.subTest(model=model.__name__):
                self.assertNotIn("warnings", {field.name for field in model._meta.fields})

    def test_full_multiline_warnings_and_existing_logs_are_preserved(self) -> None:
        """Store full diagnostics without the encoding description's 255-character limit."""
        warning = "Warning details " * 40 + "\nSecond line"
        Task.objects.filter(pk=self.task.pk).update(script_output="Existing Runner log")
        EncodingLog.objects.create(video=self.video, log="Existing encoding log")
        self._notify(warnings=[warning], script_output="New Runner log")

        self.task.refresh_from_db()
        encoding_log = EncodingLog.objects.get(video=self.video)
        self.assertEqual(self.task.warnings, [warning])
        self.assertEqual(encoding_log.warnings, [warning])
        self.assertIn("Existing Runner log", self.task.script_output)
        self.assertIn("New Runner log", self.task.script_output)
        self.assertIn("Existing encoding log", encoding_log.log)
