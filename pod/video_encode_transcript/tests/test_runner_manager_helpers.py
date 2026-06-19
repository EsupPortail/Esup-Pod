"""Focused unit tests for Esup-Pod to maximize coverage of runner_manager helpers."""

import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from django.conf import settings
from django.test import SimpleTestCase
from pod.cut.models import CutVideo
from pod.recorder.models import Recording
from pod.video_encode_transcript import runner_manager
from pod.video_encode_transcript.runner_manager import (
    _attach_cut_info,
    _attach_dressing_info,
    _attach_video_metadata,
    _build_rendition_parameters,
    _edit_task,
    _execute_url,
    _get_runner_managers,
    _headers,
    _ids_for,
    _parse_runner_response,
    _prepare_encoding_parameters,
    _prepare_task_data,
    _prepare_transcription_parameters,
    _prestore_encoding_if_needed,
    _rotate_same_priority_runner_managers,
    _send_task_to_runner_manager,
    _submit_to_runner_manager,
    _try_send_to_rm,
    _update_task_from_response,
    _update_task_pending,
    encode_studio_recording,
    encode_video,
    submit_encoding_task,
    submit_studio_task,
    submit_transcription_task,
    transcript_video,
)


class RunnerManagerImportCoverageTests(SimpleTestCase):
    """Cover module-level import paths that are otherwise hard to reach."""

    def test_module_executes_main_import_path(self) -> None:
        """Execute the file as __main__ to cover the standalone import branch."""
        module_path = Path(runner_manager.__file__)
        source = module_path.read_text(encoding="utf-8")
        encoding_utils = types.ModuleType("encoding_utils")

        def fake_get_list_rendition():
            return {"360": {"resolution": "640x360", "encode_mp4": True}}

        encoding_utils.get_list_rendition = fake_get_list_rendition
        globals_dict = {
            "__name__": "__main__",
            "__package__": "pod.video_encode_transcript",
            "__file__": str(module_path),
        }

        with patch.dict(sys.modules, {"encoding_utils": encoding_utils}):
            exec(compile(source, str(module_path), "exec"), globals_dict)

        self.assertIs(globals_dict["get_list_rendition"], fake_get_list_rendition)

    def test_module_executes_package_import_path_with_default_titles(self) -> None:
        """Execute the package import branch and default title fallbacks."""
        module_path = Path(runner_manager.__file__)
        source = module_path.read_text(encoding="utf-8")
        globals_dict = {
            "__name__": "pod.video_encode_transcript.runner_manager_exec",
            "__package__": "pod.video_encode_transcript",
            "__file__": str(module_path),
        }

        with patch.object(
            settings,
            "TEMPLATE_VISIBLE_SETTINGS",
            {"TITLE_SITE": "", "TITLE_ETB": ""},
            create=True,
        ):
            exec(compile(source, str(module_path), "exec"), globals_dict)

        self.assertEqual(globals_dict["__TITLE_SITE__"], "Pod")
        self.assertEqual(globals_dict["__TITLE_ETB__"], "University name")


class RunnerManagerHelperTests(SimpleTestCase):
    """Validate low-level runner manager helper behavior."""

    def test_build_rendition_parameters_serializes_renditions(self) -> None:
        """Serialize rendition data using string keys expected by the runner."""
        with patch(
            "pod.video_encode_transcript.runner_manager.get_list_rendition",
            return_value={
                360: {
                    "resolution": "640x360",
                    "video_bitrate": "750k",
                    "audio_bitrate": "96k",
                    "encode_mp4": True,
                },
                720: {
                    "resolution": "1280x720",
                    "video_bitrate": "2000k",
                    "audio_bitrate": "128k",
                    "encode_mp4": False,
                },
            },
        ):
            params = _build_rendition_parameters()

        self.assertEqual(
            json.loads(params["rendition"]),
            {
                "360": {
                    "resolution": "640x360",
                    "video_bitrate": "750k",
                    "audio_bitrate": "96k",
                    "encode_mp4": True,
                },
                "720": {
                    "resolution": "1280x720",
                    "video_bitrate": "2000k",
                    "audio_bitrate": "128k",
                    "encode_mp4": False,
                },
            },
        )

    def test_build_rendition_parameters_includes_bitrate_fields_for_each_rendition(
        self,
    ) -> None:
        """Ensure each serialized rendition includes both audio and video bitrates."""
        with patch(
            "pod.video_encode_transcript.runner_manager.get_list_rendition",
            return_value={
                360: {
                    "resolution": "640x360",
                    "video_bitrate": "750k",
                    "audio_bitrate": "96k",
                    "encode_mp4": True,
                },
                1080: {
                    "resolution": "1920x1080",
                    "video_bitrate": "3000k",
                    "audio_bitrate": "192k",
                    "encode_mp4": False,
                },
            },
        ):
            params = _build_rendition_parameters()

        rendition_payload = json.loads(params["rendition"])
        for rendition_data in rendition_payload.values():
            self.assertIn("video_bitrate", rendition_data)
            self.assertIn("audio_bitrate", rendition_data)

    def test_attach_cut_info_adds_serialized_cut(self) -> None:
        """Store cut metadata when a CutVideo row exists."""
        params = {}
        cut_video = SimpleNamespace(start="1.25", end="7.5", duration="6.25")

        with patch(
            "pod.video_encode_transcript.runner_manager.CutVideo.objects.get",
            return_value=cut_video,
        ):
            _attach_cut_info(params, video=SimpleNamespace())

        self.assertEqual(
            json.loads(params["cut"]),
            {"start": "1.25", "end": "7.5", "initial_duration": "6.25"},
        )

    def test_attach_cut_info_ignores_missing_cut(self) -> None:
        """Leave params unchanged when no CutVideo exists."""
        params = {}

        with patch(
            "pod.video_encode_transcript.runner_manager.CutVideo.objects.get",
            side_effect=CutVideo.DoesNotExist(),
        ):
            _attach_cut_info(params, video=SimpleNamespace())

        self.assertEqual(params, {})

    def test_attach_dressing_info_adds_all_available_assets(self) -> None:
        """Serialize watermark and credits metadata for the runner."""
        params = {}
        dressing = SimpleNamespace(
            watermark=SimpleNamespace(file=SimpleNamespace(name="dressing/wm.png")),
            position="top-right",
            opacity=0.7,
            opening_credits=SimpleNamespace(
                slug="intro",
                video=SimpleNamespace(name="openers/intro.mp4"),
                duration=5,
            ),
            ending_credits=SimpleNamespace(
                slug="outro",
                video=SimpleNamespace(name="outros/outro.mp4"),
                duration=8,
            ),
        )
        video = SimpleNamespace(id=12)

        with patch("pod.dressing.models.Dressing.objects.filter") as mock_filter, patch(
            "pod.dressing.models.Dressing.objects.get", return_value=dressing
        ), patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=SimpleNamespace(domain="example.com"),
        ), patch(
            "pod.video_encode_transcript.runner_manager.SECURE_SSL_REDIRECT", True
        ):
            mock_filter.return_value.exists.return_value = True
            _attach_dressing_info(params, video)

        self.assertEqual(
            json.loads(params["dressing"]),
            {
                "watermark": "https://example.com/media/dressing/wm.png",
                "watermark_position": "top-right",
                "watermark_opacity": "0.7",
                "opening_credits": "intro",
                "opening_credits_video": "https://example.com/media/openers/intro.mp4",
                "opening_credits_video_duration": "5",
                "ending_credits": "outro",
                "ending_credits_video": "https://example.com/media/outros/outro.mp4",
                "ending_credits_video_duration": "8",
            },
        )

    def test_attach_dressing_info_ignores_videos_without_dressing(self) -> None:
        """Keep params unchanged when no dressing is linked to the video."""
        params = {}

        with patch("pod.dressing.models.Dressing.objects.filter") as mock_filter, patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=SimpleNamespace(domain="example.com"),
        ):
            mock_filter.return_value.exists.return_value = False
            _attach_dressing_info(params, SimpleNamespace(id=99))

        self.assertEqual(params, {})

    def test_attach_dressing_info_logs_errors(self) -> None:
        """Catch unexpected dressing lookup errors without raising."""
        with patch(
            "pod.dressing.models.Dressing.objects.filter",
            side_effect=RuntimeError("boom"),
        ), patch("pod.video_encode_transcript.runner_manager.log.error") as mock_error:
            _attach_dressing_info({}, SimpleNamespace(id=7))

        mock_error.assert_called_once()

    def test_attach_video_metadata_skips_empty_values(self) -> None:
        """Do not inject empty metadata fields into params."""
        params = {}
        _attach_video_metadata(params, SimpleNamespace(id=None, slug="", title=None))
        self.assertEqual(params, {})

    def test_prepare_task_data_builds_runner_payload(self) -> None:
        """Assemble the runner task payload with notify URL."""
        payload = _prepare_task_data(
            source_url="https://example.com/media/video.mp4",
            base_url="https://example.com",
            parameters={"rendition": "{}"},
            task_type="encoding",
        )

        self.assertEqual(payload["app_name"], "Esup-Pod")
        self.assertEqual(payload["source_url"], "https://example.com/media/video.mp4")
        self.assertEqual(
            payload["notify_url"], "https://example.com/runner/notify_task_end/"
        )
        self.assertEqual(payload["parameters"], {"rendition": "{}"})

    @patch(
        "pod.video_encode_transcript.runner_manager.get_list_rendition",
        return_value={
            360: {
                "resolution": "640x360",
                "video_bitrate": "750k",
                "audio_bitrate": "96k",
                "encode_mp4": True,
            }
        },
    )
    @patch("pod.video_encode_transcript.runner_manager.SECURE_SSL_REDIRECT", False)
    @patch("pod.video_encode_transcript.runner_manager._attach_dressing_info")
    @patch("pod.video_encode_transcript.runner_manager._attach_cut_info")
    @patch("pod.video_encode_transcript.runner_manager._submit_to_runner_managers")
    def test_submit_encoding_task_includes_video_metadata(
        self,
        mock_submit_to_runner_managers,
        mock_attach_cut_info,
        mock_attach_dressing_info,
        mock_get_list_rendition,
    ) -> None:
        """Encoding tasks should build a shared payload including video metadata."""
        mock_submit_to_runner_managers.return_value = True
        rm = SimpleNamespace(name="runner-a")
        video = SimpleNamespace(
            id=17,
            slug="sample-video",
            title="Sample video",
            video="videos/sample.mp4",
        )

        result = submit_encoding_task(
            video=video,
            site=SimpleNamespace(domain="example.com"),
            runner_managers=[rm],
        )

        self.assertTrue(result)
        payload = mock_submit_to_runner_managers.call_args.kwargs["data"]
        self.assertEqual(payload["parameters"]["video_id"], 17)
        self.assertEqual(payload["parameters"]["video_slug"], "sample-video")
        self.assertEqual(payload["parameters"]["video_title"], "Sample video")
        self.assertEqual(
            json.loads(payload["parameters"]["rendition"]),
            {
                "360": {
                    "resolution": "640x360",
                    "video_bitrate": "750k",
                    "audio_bitrate": "96k",
                    "encode_mp4": True,
                }
            },
        )
        mock_get_list_rendition.assert_called_once_with()
        mock_attach_cut_info.assert_called_once()
        mock_attach_dressing_info.assert_called_once()
        self.assertEqual(
            payload["source_url"], "http://example.com/media/videos/sample.mp4"
        )
        self.assertEqual(
            payload["notify_url"], "http://example.com/runner/notify_task_end/"
        )
        mock_submit_to_runner_managers.assert_called_once_with(
            runner_managers=[rm],
            data=payload,
            task_type="encoding",
            source_type="video",
            source_id=17,
        )

    @patch("pod.video_encode_transcript.runner_manager.SECURE_SSL_REDIRECT", False)
    @patch("pod.video_encode_transcript.runner_manager._submit_to_runner_managers")
    @patch(
        "pod.video_encode_transcript.transcript.resolve_transcription_language",
        return_value="fr",
    )
    def test_submit_transcription_task_includes_video_metadata(
        self, mock_resolve_transcription_language, mock_submit_to_runner_managers
    ) -> None:
        """Transcription tasks should build a shared payload including metadata."""
        mock_submit_to_runner_managers.return_value = True
        rm = SimpleNamespace(name="runner-a")
        video = Mock(
            id=23,
            slug="transcript-video",
            title="Transcript video",
            transcript="fr",
            duration=12.5,
            video="videos/transcript.mp4",
        )
        video.get_video_mp3.return_value = None

        with patch.object(
            runner_manager.settings, "TRANSCRIPTION_TYPE", "whisper", create=True
        ), patch.object(
            runner_manager.settings, "TRANSCRIPTION_NORMALIZE", True, create=True
        ):
            result = submit_transcription_task(
                video=video,
                site=SimpleNamespace(domain="example.com"),
                runner_managers=[rm],
            )

        self.assertTrue(result)
        payload = mock_submit_to_runner_managers.call_args.kwargs["data"]
        self.assertEqual(payload["parameters"]["language"], "fr")
        self.assertEqual(payload["parameters"]["duration"], 12.5)
        self.assertTrue(payload["parameters"]["normalize"])
        self.assertEqual(payload["parameters"]["model_type"], "whisper")
        self.assertEqual(payload["parameters"]["video_id"], 23)
        self.assertEqual(payload["parameters"]["video_slug"], "transcript-video")
        self.assertEqual(payload["parameters"]["video_title"], "Transcript video")
        self.assertEqual(
            payload["source_url"], "http://example.com/media/videos/transcript.mp4"
        )
        mock_submit_to_runner_managers.assert_called_once_with(
            runner_managers=[rm],
            data=payload,
            task_type="transcription",
            source_type="video",
            source_id=23,
        )
        mock_resolve_transcription_language.assert_called_once_with(video)

    @patch(
        "pod.video_encode_transcript.runner_manager.get_list_rendition",
        return_value={
            720: {
                "resolution": "1280x720",
                "video_bitrate": "2000k",
                "audio_bitrate": "128k",
                "encode_mp4": False,
            }
        },
    )
    @patch("pod.video_encode_transcript.runner_manager.SECURE_SSL_REDIRECT", False)
    @patch("pod.video_encode_transcript.runner_manager._submit_to_runner_managers")
    def test_submit_studio_task_uses_shared_source_url_and_payload(
        self, mock_submit_to_runner_managers, mock_get_list_rendition
    ) -> None:
        """Studio tasks should reuse shared source URL and payload builders."""
        mock_submit_to_runner_managers.return_value = True
        rm = SimpleNamespace(name="runner-a")
        recording = SimpleNamespace(id=31, source_file="/srv/media/studio/source.xml")

        with patch.object(
            runner_manager.settings, "MEDIA_ROOT", "/srv/media", create=True
        ), patch.object(runner_manager.settings, "MEDIA_URL", "/media/", create=True):
            result = submit_studio_task(
                recording=recording,
                site=SimpleNamespace(domain="example.com"),
                runner_managers=[rm],
            )

        self.assertTrue(result)
        payload = mock_submit_to_runner_managers.call_args.kwargs["data"]
        self.assertEqual(
            payload["source_url"], "http://example.com/media/studio/source.xml"
        )
        self.assertEqual(
            json.loads(payload["parameters"]["rendition"]),
            {
                "720": {
                    "resolution": "1280x720",
                    "video_bitrate": "2000k",
                    "audio_bitrate": "128k",
                    "encode_mp4": False,
                }
            },
        )
        self.assertNotIn("video_id", payload["parameters"])
        mock_get_list_rendition.assert_called_once_with()
        mock_submit_to_runner_managers.assert_called_once_with(
            runner_managers=[rm],
            data=payload,
            task_type="studio",
            source_type="recording",
            source_id=31,
        )

    def test_rotate_same_priority_runner_managers_returns_singleton_list(self) -> None:
        """Avoid unnecessary DB lookup work when only one runner is available."""
        runner = SimpleNamespace(id=1)
        self.assertEqual(_rotate_same_priority_runner_managers([runner]), [runner])

    def test_rotate_same_priority_runner_managers_rotates_and_handles_missing_history(
        self,
    ) -> None:
        """Rotate from the last assigned runner and keep order without history."""
        runners = [
            SimpleNamespace(id=1),
            SimpleNamespace(id=2),
            SimpleNamespace(id=3),
        ]
        queryset = Mock()
        queryset.order_by.return_value.values_list.return_value.first.side_effect = [
            2,
            None,
        ]

        with patch(
            "pod.video_encode_transcript.runner_manager.Task.objects.filter",
            return_value=queryset,
        ):
            self.assertEqual(
                _rotate_same_priority_runner_managers(runners),
                [runners[2], runners[0], runners[1]],
            )
            self.assertEqual(_rotate_same_priority_runner_managers(runners), runners)

    def test_get_runner_managers_keeps_singletons_and_rotates_groups(self) -> None:
        """Return one runner as-is and rotate multi-runner priority groups."""
        runner_a = SimpleNamespace(id=1, priority=1)
        runner_b = SimpleNamespace(id=2, priority=1)
        runner_c = SimpleNamespace(id=3, priority=2)

        manager_qs = Mock()
        manager_qs.order_by.return_value = [runner_a]
        with patch(
            "pod.video_encode_transcript.runner_manager.RunnerManager.objects.filter",
            return_value=manager_qs,
        ):
            self.assertEqual(_get_runner_managers(SimpleNamespace()), [runner_a])

        manager_qs.order_by.return_value = [runner_a, runner_b, runner_c]
        with patch(
            "pod.video_encode_transcript.runner_manager.RunnerManager.objects.filter",
            return_value=manager_qs,
        ), patch(
            "pod.video_encode_transcript.runner_manager._rotate_same_priority_runner_managers",
            side_effect=[[runner_b, runner_a], [runner_c]],
        ) as mock_rotate:
            ordered = _get_runner_managers(SimpleNamespace())

        self.assertEqual(ordered, [runner_b, runner_a, runner_c])
        self.assertEqual(mock_rotate.call_count, 2)

    def test_ids_for_supports_video_and_recording_sources(self) -> None:
        """Resolve ids according to the source type."""
        self.assertEqual(_ids_for("video", "12"), (12, None))
        self.assertEqual(_ids_for("recording", 5), (None, 5))

    def test_prepare_encoding_parameters_handles_video_and_studio_modes(self) -> None:
        """Attach metadata only when a video object is provided."""
        video = SimpleNamespace(id=9, slug="sample-video", title="Sample video")

        with patch(
            "pod.video_encode_transcript.runner_manager._build_rendition_parameters",
            side_effect=[{"rendition": "{}"}, {"rendition": "{}"}],
        ), patch(
            "pod.video_encode_transcript.runner_manager._attach_cut_info"
        ) as mock_cut, patch(
            "pod.video_encode_transcript.runner_manager._attach_dressing_info"
        ) as mock_dressing:
            params_with_video = _prepare_encoding_parameters(video=video)
            params_without_video = _prepare_encoding_parameters(video=None)

        self.assertEqual(
            params_with_video,
            {
                "rendition": "{}",
                "video_id": 9,
                "video_slug": "sample-video",
                "video_title": "Sample video",
            },
        )
        self.assertEqual(params_without_video, {"rendition": "{}"})
        mock_cut.assert_called_once_with(params_with_video, video)
        mock_dressing.assert_called_once_with(params_with_video, video)

    def test_prepare_transcription_parameters_covers_normal_and_legacy_modes(
        self,
    ) -> None:
        """Build transcription params with resolved language or legacy fallback."""
        video = SimpleNamespace(
            transcript="fr",
            duration=12.5,
            id=3,
            slug="video-slug",
            title="Video title",
        )

        with patch(
            "pod.video_encode_transcript.transcript.resolve_transcription_language",
            return_value="en",
        ), patch.object(
            runner_manager.settings, "TRANSCRIPTION_TYPE", "whisper", create=True
        ), patch.object(
            runner_manager.settings, "TRANSCRIPTION_NORMALIZE", True, create=True
        ):
            params = _prepare_transcription_parameters(video)

        self.assertEqual(
            params,
            {
                "language": "en",
                "duration": 12.5,
                "normalize": True,
                "video_id": 3,
                "video_slug": "video-slug",
                "video_title": "Video title",
                "model_type": "whisper",
            },
        )

        with patch(
            "pod.video_encode_transcript.transcript.resolve_transcription_language",
            side_effect=RuntimeError("boom"),
        ):
            legacy_params = _prepare_transcription_parameters(video)

        self.assertEqual(
            legacy_params,
            {
                "lang": "fr",
                "video_id": 3,
                "video_slug": "video-slug",
                "video_title": "Video title",
            },
        )

    def test_execute_url_normalizes_trailing_slash(self) -> None:
        """Always target the task execute endpoint."""
        self.assertEqual(
            _execute_url(SimpleNamespace(url="https://runner.example.com")),
            "https://runner.example.com/task/execute",
        )
        self.assertEqual(
            _execute_url(SimpleNamespace(url="https://runner.example.com/")),
            "https://runner.example.com/task/execute",
        )

    def test_headers_include_bearer_token(self) -> None:
        """Build the runner manager authentication headers."""
        self.assertEqual(
            _headers(SimpleNamespace(token="runner-token")),
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": "Bearer runner-token",
            },
        )

    def test_try_send_to_rm_posts_json_payload(self) -> None:
        """POST the serialized payload to the runner execute endpoint."""
        rm = SimpleNamespace(
            url="https://runner.example.com/",
            token="runner-token",
            name="runner-a",
        )
        payload = {"parameters": {"test": True}}
        response = Mock()

        with patch(
            "pod.video_encode_transcript.runner_manager.requests.post",
            return_value=response,
        ) as mock_post:
            result = _try_send_to_rm(rm, payload)

        self.assertIs(result, response)
        mock_post.assert_called_once_with(
            "https://runner.example.com/task/execute",
            data=json.dumps(payload),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": "Bearer runner-token",
            },
            timeout=30,
        )

    def test_try_send_to_rm_returns_none_when_request_fails(self) -> None:
        """Move on to the next runner when the HTTP request fails."""
        rm = SimpleNamespace(
            url="https://runner.example.com/",
            token="runner-token",
            name="runner-a",
        )

        with patch(
            "pod.video_encode_transcript.runner_manager.requests.post",
            side_effect=requests.RequestException("down"),
        ), patch("pod.video_encode_transcript.runner_manager.log.warning") as mock_warn:
            result = _try_send_to_rm(rm, {"parameters": {}})

        self.assertIsNone(result)
        mock_warn.assert_called_once()

    def test_parse_runner_response_handles_empty_and_valid_payloads(self) -> None:
        """Accept empty bodies and valid JSON objects."""
        rm = SimpleNamespace(name="runner-a")
        empty_response = Mock(content=b"", headers={})
        valid_response = Mock(content=b"{}", headers={"Content-Type": "application/json"})
        valid_response.json.return_value = {"task_id": "abc", "status": "running"}

        self.assertEqual(_parse_runner_response(rm, empty_response), {})
        self.assertEqual(
            _parse_runner_response(rm, valid_response),
            {"task_id": "abc", "status": "running"},
        )

    def test_parse_runner_response_rejects_invalid_payloads(self) -> None:
        """Reject HTML bodies and unexpected JSON types."""
        rm = SimpleNamespace(name="runner-a")
        invalid_body = Mock(
            content=b"<html>oops</html>",
            headers={"Content-Type": "text/html"},
        )
        invalid_body.json.side_effect = ValueError("invalid")
        invalid_type = Mock(
            content=b"[]",
            headers={"Content-Type": "application/json"},
        )
        invalid_type.json.return_value = ["oops"]

        with patch("pod.video_encode_transcript.runner_manager.log.warning") as mock_warn:
            self.assertIsNone(_parse_runner_response(rm, invalid_body))
            self.assertIsNone(_parse_runner_response(rm, invalid_type))

        self.assertEqual(mock_warn.call_count, 2)

    def test_prestore_encoding_if_needed_handles_all_source_modes(self) -> None:
        """Dispatch pre-store helpers only for encoding and studio tasks."""
        rm = SimpleNamespace(url="https://runner.example.com/")
        payload = {"task_type": "encoding"}

        with patch(
            "pod.video_encode_transcript.runner_manager.store_before_remote_encoding_video"
        ) as mock_store_video, patch(
            "pod.video_encode_transcript.runner_manager.store_before_remote_encoding_recording"
        ) as mock_store_recording, patch(
            "pod.video_encode_transcript.runner_manager.log.warning"
        ) as mock_warn:
            _prestore_encoding_if_needed(
                task_type="transcription",
                source_type="video",
                video_id=1,
                recording_id=None,
                rm=rm,
                data=payload,
            )
            _prestore_encoding_if_needed(
                task_type="encoding",
                source_type="video",
                video_id=1,
                recording_id=None,
                rm=rm,
                data=payload,
            )
            _prestore_encoding_if_needed(
                task_type="encoding",
                source_type="video",
                video_id=None,
                recording_id=None,
                rm=rm,
                data=payload,
            )
            _prestore_encoding_if_needed(
                task_type="studio",
                source_type="recording",
                video_id=None,
                recording_id=9,
                rm=rm,
                data=payload,
            )
            _prestore_encoding_if_needed(
                task_type="studio",
                source_type="recording",
                video_id=None,
                recording_id=None,
                rm=rm,
                data=payload,
            )

        mock_store_video.assert_called_once_with(
            1, "https://runner.example.com/task/execute", payload
        )
        mock_store_recording.assert_called_once_with(
            9, "https://runner.example.com/task/execute", payload
        )
        self.assertEqual(mock_warn.call_count, 2)

    def test_submit_to_runner_manager_covers_failure_and_success_paths(self) -> None:
        """Handle network failures, HTTP errors, and valid runner responses."""
        rm = SimpleNamespace(name="runner-a", id=4)
        data = {
            "etab_name": "Site",
            "app_name": "Esup-Pod",
            "app_version": "4.X",
            "task_type": "encoding",
            "source_url": "https://example.com/video.mp4",
            "notify_url": "https://example.com/runner/notify_task_end/",
            "parameters": {},
        }
        non_200_response = Mock(status_code=503)
        ok_response = Mock(status_code=200)

        with patch(
            "pod.video_encode_transcript.runner_manager._update_task_from_response"
        ) as mock_update, patch(
            "pod.video_encode_transcript.runner_manager._prestore_encoding_if_needed"
        ) as mock_prestore, patch(
            "pod.video_encode_transcript.runner_manager.log.warning"
        ) as mock_warn, patch(
            "pod.video_encode_transcript.runner_manager._try_send_to_rm",
            side_effect=[None, non_200_response, ok_response],
        ), patch(
            "pod.video_encode_transcript.runner_manager._parse_runner_response",
            return_value={"task_id": "remote-1", "status": "running"},
        ):
            self.assertFalse(
                _submit_to_runner_manager(
                    rm, data, "encoding", "video", video_id=10, recording_id=None
                )
            )
            self.assertFalse(
                _submit_to_runner_manager(
                    rm, data, "encoding", "video", video_id=10, recording_id=None
                )
            )
            self.assertTrue(
                _submit_to_runner_manager(
                    rm, data, "encoding", "video", video_id=10, recording_id=None
                )
            )

        mock_update.assert_called_once_with(
            10, None, "encoding", rm, {"task_id": "remote-1", "status": "running"}
        )
        mock_prestore.assert_called_once()
        mock_warn.assert_called_once()

    def test_submit_to_runner_manager_returns_false_on_invalid_runner_payload(
        self,
    ) -> None:
        """Abort submission when the runner response cannot be parsed."""
        rm = SimpleNamespace(name="runner-a", id=4)
        response = Mock(status_code=200)

        with patch(
            "pod.video_encode_transcript.runner_manager._try_send_to_rm",
            return_value=response,
        ), patch(
            "pod.video_encode_transcript.runner_manager._parse_runner_response",
            return_value=None,
        ), patch(
            "pod.video_encode_transcript.runner_manager._update_task_from_response"
        ) as mock_update, patch(
            "pod.video_encode_transcript.runner_manager._prestore_encoding_if_needed"
        ) as mock_prestore:
            result = _submit_to_runner_manager(
                rm,
                {
                    "etab_name": "Site",
                    "app_name": "Esup-Pod",
                    "app_version": "4.X",
                    "task_type": "encoding",
                    "source_url": "https://example.com/video.mp4",
                    "notify_url": "https://example.com/runner/notify_task_end/",
                    "parameters": {},
                },
                "encoding",
                "video",
                video_id=10,
                recording_id=None,
            )

        self.assertFalse(result)
        mock_update.assert_not_called()
        mock_prestore.assert_not_called()

    def test_update_task_helpers_delegate_to_edit_task(self) -> None:
        """Translate helper inputs into the expected _edit_task calls."""
        rm = SimpleNamespace(id=7)

        with patch("pod.video_encode_transcript.runner_manager._edit_task") as mock_edit:
            self.assertEqual(_update_task_pending("video", "14", "encoding"), (14, None))
            self.assertEqual(_update_task_pending("recording", 6, "studio"), (None, 6))
            _update_task_from_response(
                video_id=14,
                recording_id=None,
                task_type="encoding",
                rm=rm,
                response_json={},
            )

        self.assertEqual(mock_edit.call_count, 3)
        mock_edit.assert_any_call(
            video_id=14,
            recording_id=None,
            type="encoding",
            status="pending",
            runner_manager_id=None,
            task_id=None,
        )
        mock_edit.assert_any_call(
            video_id=None,
            recording_id=6,
            type="studio",
            status="pending",
            runner_manager_id=None,
            task_id=None,
        )
        mock_edit.assert_any_call(
            video_id=14,
            recording_id=None,
            type="encoding",
            status="pending",
            runner_manager_id=7,
            task_id=None,
        )

    def test_send_task_to_runner_manager_covers_all_result_paths(self) -> None:
        """Return appropriate status for success, no runner, all-fail, and exceptions."""
        runner_a = SimpleNamespace(name="runner-a")
        runner_b = SimpleNamespace(name="runner-b")
        site = SimpleNamespace(domain="example.com")

        with patch(
            "pod.video_encode_transcript.runner_manager._update_task_pending",
            return_value=(12, None),
        ), patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=site,
        ), patch(
            "pod.video_encode_transcript.runner_manager._prepare_task_data",
            return_value={"parameters": {}},
        ), patch(
            "pod.video_encode_transcript.runner_manager.log.warning"
        ) as mock_warn, patch(
            "pod.video_encode_transcript.runner_manager.log.error"
        ) as mock_error:
            with patch(
                "pod.video_encode_transcript.runner_manager._get_runner_managers",
                return_value=[],
            ):
                self.assertFalse(
                    _send_task_to_runner_manager(
                        task_type="encoding",
                        source_id=12,
                        source_type="video",
                        source_url="https://example.com/video.mp4",
                        base_url="https://example.com",
                        parameters={"rendition": "{}"},
                    )
                )

            with patch(
                "pod.video_encode_transcript.runner_manager._get_runner_managers",
                return_value=[runner_a, runner_b],
            ), patch(
                "pod.video_encode_transcript.runner_manager._submit_to_runner_manager",
                side_effect=[False, True],
            ) as mock_submit:
                self.assertTrue(
                    _send_task_to_runner_manager(
                        task_type="encoding",
                        source_id=12,
                        source_type="video",
                        source_url="https://example.com/video.mp4",
                        base_url="https://example.com",
                        parameters={"rendition": "{}"},
                    )
                )
                self.assertEqual(mock_submit.call_count, 2)

            with patch(
                "pod.video_encode_transcript.runner_manager._get_runner_managers",
                return_value=[runner_a],
            ), patch(
                "pod.video_encode_transcript.runner_manager._submit_to_runner_manager",
                return_value=False,
            ):
                self.assertFalse(
                    _send_task_to_runner_manager(
                        task_type="encoding",
                        source_id=12,
                        source_type="video",
                        source_url="https://example.com/video.mp4",
                        base_url="https://example.com",
                        parameters={"rendition": "{}"},
                    )
                )

            with patch(
                "pod.video_encode_transcript.runner_manager._update_task_pending",
                side_effect=RuntimeError("boom"),
            ):
                self.assertFalse(
                    _send_task_to_runner_manager(
                        task_type="encoding",
                        source_id=12,
                        source_type="video",
                        source_url="https://example.com/video.mp4",
                        base_url="https://example.com",
                        parameters={"rendition": "{}"},
                    )
                )

        self.assertGreaterEqual(mock_warn.call_count, 2)
        mock_error.assert_called_once()

    @patch("pod.video_encode_transcript.runner_manager.SECURE_SSL_REDIRECT", False)
    def test_encode_video_builds_payload_and_logs_errors(self) -> None:
        """Prepare video encoding submission and handle failures gracefully."""
        site = SimpleNamespace(domain="example.com")
        video = SimpleNamespace(video="videos/sample.mp4")

        with patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=site,
        ), patch(
            "pod.video_encode_transcript.runner_manager.get_object_or_404",
            return_value=video,
        ), patch(
            "pod.video_encode_transcript.runner_manager._prepare_encoding_parameters",
            return_value={"rendition": "{}"},
        ) as mock_prepare, patch(
            "pod.video_encode_transcript.runner_manager._send_task_to_runner_manager"
        ) as mock_send:
            encode_video(9)

        mock_prepare.assert_called_once_with(video=video)
        mock_send.assert_called_once_with(
            task_type="encoding",
            source_id=9,
            source_type="video",
            source_url="http://example.com/media/videos/sample.mp4",
            base_url="http://example.com",
            parameters={"rendition": "{}"},
        )

        with patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=site,
        ), patch(
            "pod.video_encode_transcript.runner_manager.get_object_or_404",
            side_effect=RuntimeError("boom"),
        ), patch(
            "pod.video_encode_transcript.runner_manager.log.error"
        ) as mock_error:
            encode_video(9)

        mock_error.assert_called_once()

    @patch("pod.video_encode_transcript.runner_manager.SECURE_SSL_REDIRECT", False)
    def test_encode_studio_recording_covers_success_and_error_paths(self) -> None:
        """Build studio XML URLs and log lookup/runtime failures."""
        site = SimpleNamespace(domain="example.com")
        recording = SimpleNamespace(source_file="/srv/media/studio/source.xml")

        with patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=site,
        ), patch(
            "pod.video_encode_transcript.runner_manager.Recording.objects.get",
            return_value=recording,
        ), patch(
            "pod.video_encode_transcript.runner_manager.os.path.relpath",
            return_value="studio/source.xml",
        ), patch.object(
            runner_manager.settings, "MEDIA_ROOT", "/srv/media", create=True
        ), patch.object(
            runner_manager.settings, "MEDIA_URL", "/media/", create=True
        ), patch(
            "pod.video_encode_transcript.runner_manager._prepare_encoding_parameters",
            return_value={"rendition": "{}"},
        ), patch(
            "pod.video_encode_transcript.runner_manager._send_task_to_runner_manager"
        ) as mock_send:
            encode_studio_recording(15)

        mock_send.assert_called_once_with(
            task_type="studio",
            source_id=15,
            source_type="recording",
            source_url="http://example.com/media/studio/source.xml",
            base_url="http://example.com",
            parameters={"rendition": "{}"},
        )

        with patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=site,
        ), patch(
            "pod.video_encode_transcript.runner_manager.Recording.objects.get",
            return_value=recording,
        ), patch(
            "pod.video_encode_transcript.runner_manager.os.path.relpath",
            side_effect=ValueError("no relpath"),
        ), patch.object(
            runner_manager.settings, "MEDIA_ROOT", "/srv/media", create=True
        ), patch.object(
            runner_manager.settings, "MEDIA_URL", "/media/", create=True
        ), patch(
            "pod.video_encode_transcript.runner_manager._prepare_encoding_parameters",
            return_value={"rendition": "{}"},
        ), patch(
            "pod.video_encode_transcript.runner_manager._send_task_to_runner_manager"
        ) as mock_send:
            encode_studio_recording(16)

        mock_send.assert_called_once_with(
            task_type="studio",
            source_id=16,
            source_type="recording",
            source_url="http://example.com/media/srv/media/studio/source.xml",
            base_url="http://example.com",
            parameters={"rendition": "{}"},
        )

        with patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=site,
        ), patch(
            "pod.video_encode_transcript.runner_manager.Recording.objects.get",
            side_effect=Recording.DoesNotExist,
        ), patch(
            "pod.video_encode_transcript.runner_manager.log.error"
        ) as mock_error:
            encode_studio_recording(17)
        mock_error.assert_called_once()

        with patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            side_effect=RuntimeError("boom"),
        ), patch("pod.video_encode_transcript.runner_manager.log.error") as mock_error:
            encode_studio_recording(18)
        mock_error.assert_called_once()

    @patch("pod.video_encode_transcript.runner_manager.SECURE_SSL_REDIRECT", False)
    def test_transcript_video_covers_mp3_video_and_error_paths(self) -> None:
        """Prefer the MP3 rendition when available and keep state aligned."""
        site = SimpleNamespace(domain="example.com")
        mp3_wrapper = SimpleNamespace(source_file=SimpleNamespace(url="/media/audio.mp3"))
        video_with_mp3 = Mock(video="videos/sample.mp4")
        video_with_mp3.get_video_mp3.return_value = mp3_wrapper
        video_without_mp3 = Mock(video="videos/sample.mp4")
        video_without_mp3.get_video_mp3.return_value = None
        queryset = Mock()

        with patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=site,
        ), patch(
            "pod.video_encode_transcript.runner_manager.get_object_or_404",
            return_value=video_with_mp3,
        ), patch(
            "pod.video_encode_transcript.runner_manager._prepare_transcription_parameters",
            return_value={"language": "en"},
        ), patch(
            "pod.video_encode_transcript.runner_manager.Video.objects.filter",
            return_value=queryset,
        ), patch(
            "pod.video_encode_transcript.runner_manager.change_encoding_step"
        ) as mock_change_step, patch(
            "pod.video_encode_transcript.runner_manager._send_task_to_runner_manager"
        ) as mock_send:
            transcript_video(21)

        queryset.update.assert_called_once_with(encoding_in_progress=True)
        mock_change_step.assert_called_once_with(21, 5, "transcripting audio")
        mock_send.assert_called_once_with(
            task_type="transcription",
            source_id=21,
            source_type="video",
            source_url="http://example.com/media/audio.mp3",
            base_url="http://example.com",
            parameters={"language": "en"},
        )

        with patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=site,
        ), patch(
            "pod.video_encode_transcript.runner_manager.get_object_or_404",
            return_value=video_without_mp3,
        ), patch(
            "pod.video_encode_transcript.runner_manager._prepare_transcription_parameters",
            return_value={"language": "fr"},
        ), patch(
            "pod.video_encode_transcript.runner_manager.Video.objects.filter",
            return_value=Mock(),
        ), patch(
            "pod.video_encode_transcript.runner_manager.change_encoding_step"
        ), patch(
            "pod.video_encode_transcript.runner_manager._send_task_to_runner_manager"
        ) as mock_send:
            transcript_video(22)

        mock_send.assert_called_once_with(
            task_type="transcription",
            source_id=22,
            source_type="video",
            source_url="http://example.com/media/videos/sample.mp4",
            base_url="http://example.com",
            parameters={"language": "fr"},
        )

        with patch(
            "pod.video_encode_transcript.runner_manager.Site.objects.get_current",
            return_value=site,
        ), patch(
            "pod.video_encode_transcript.runner_manager.get_object_or_404",
            side_effect=RuntimeError("boom"),
        ), patch(
            "pod.video_encode_transcript.runner_manager.log.error"
        ) as mock_error:
            transcript_video(23)

        mock_error.assert_called_once()


class RunnerManagerEditTaskTests(SimpleTestCase):
    """Validate task creation and update behavior without touching the DB."""

    @staticmethod
    def _fake_task_queue_module():
        module = types.ModuleType("pod.video_encode_transcript.task_queue")
        module.refresh_pending_task_ranks = Mock()
        return module

    def test_edit_task_creates_video_and_studio_tasks(self) -> None:
        """Create new task rows for both videos and studio recordings."""
        fake_task_queue = self._fake_task_queue_module()

        with patch.dict(
            sys.modules, {"pod.video_encode_transcript.task_queue": fake_task_queue}
        ), patch("pod.video_encode_transcript.runner_manager.Task") as mock_task:
            created_video_task = Mock()
            created_studio_task = Mock()
            mock_task.objects.filter.side_effect = [[], []]
            mock_task.side_effect = [created_video_task, created_studio_task]

            _edit_task(
                video_id=4,
                recording_id=None,
                type="encoding",
                status="pending",
                runner_manager_id=3,
                task_id="video-task",
            )
            _edit_task(
                video_id=None,
                recording_id=8,
                type="studio",
                status="pending",
                runner_manager_id=5,
                task_id="studio-task",
            )

        self.assertEqual(mock_task.call_count, 2)
        mock_task.assert_any_call(
            video_id=4,
            recording_id=None,
            type="encoding",
            runner_manager_id=3,
            status="pending",
            task_id="video-task",
        )
        mock_task.assert_any_call(
            video_id=None,
            recording_id=8,
            type="studio",
            runner_manager_id=5,
            status="pending",
            task_id="studio-task",
        )
        created_video_task.save.assert_called_once_with()
        created_studio_task.save.assert_called_once_with()
        self.assertEqual(fake_task_queue.refresh_pending_task_ranks.call_count, 2)

    def test_edit_task_updates_existing_pending_task(self) -> None:
        """Update an existing pending task instead of creating a new row."""
        fake_task_queue = self._fake_task_queue_module()
        existing_task = SimpleNamespace(
            status="pending",
            runner_manager_id=None,
            task_id=None,
            save=Mock(),
        )

        with patch.dict(
            sys.modules, {"pod.video_encode_transcript.task_queue": fake_task_queue}
        ), patch("pod.video_encode_transcript.runner_manager.Task") as mock_task:
            mock_task.objects.filter.return_value = [existing_task]

            _edit_task(
                video_id=4,
                recording_id=None,
                type="encoding",
                status="running",
                runner_manager_id=9,
                task_id="remote-9",
            )

        self.assertEqual(existing_task.status, "running")
        self.assertEqual(existing_task.runner_manager_id, 9)
        self.assertEqual(existing_task.task_id, "remote-9")
        existing_task.save.assert_called_once_with()
        fake_task_queue.refresh_pending_task_ranks.assert_called_once_with()

    def test_edit_task_preserves_runner_info_when_no_new_values(self) -> None:
        """Do not overwrite task_id or runner_manager_id when None is provided."""
        fake_task_queue = self._fake_task_queue_module()
        existing_task = SimpleNamespace(
            status="pending",
            runner_manager_id=6,
            task_id="keep-me",
            save=Mock(),
        )

        with patch.dict(
            sys.modules, {"pod.video_encode_transcript.task_queue": fake_task_queue}
        ), patch("pod.video_encode_transcript.runner_manager.Task") as mock_task:
            mock_task.objects.filter.return_value = [existing_task]

            _edit_task(
                video_id=4,
                recording_id=None,
                type="encoding",
                status="completed",
                runner_manager_id=None,
                task_id=None,
            )

        self.assertEqual(existing_task.status, "completed")
        self.assertEqual(existing_task.runner_manager_id, 6)
        self.assertEqual(existing_task.task_id, "keep-me")
        existing_task.save.assert_called_once_with()
        fake_task_queue.refresh_pending_task_ranks.assert_called_once_with()

    def test_edit_task_logs_errors(self) -> None:
        """Catch task edition errors and log them instead of raising."""
        fake_task_queue = self._fake_task_queue_module()

        with patch.dict(
            sys.modules, {"pod.video_encode_transcript.task_queue": fake_task_queue}
        ), patch(
            "pod.video_encode_transcript.runner_manager.Task.objects.filter",
            side_effect=RuntimeError("boom"),
        ), patch(
            "pod.video_encode_transcript.runner_manager.log.error"
        ) as mock_error:
            _edit_task(
                video_id=4,
                recording_id=None,
                type="encoding",
                status="failed",
            )

        mock_error.assert_called_once()
