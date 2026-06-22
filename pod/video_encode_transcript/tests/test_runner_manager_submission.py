"""Runner manager submission tests.

Run with `python manage.py test pod.video_encode_transcript.tests.test_runner_manager_submission`
"""

from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from pod.video_encode_transcript.runner_manager import _submit_to_runner_manager


class RunnerManagerSubmissionTests(SimpleTestCase):
    """Validate submission guardrails for runner manager responses."""

    @patch("pod.video_encode_transcript.runner_manager._prestore_encoding_if_needed")
    @patch("pod.video_encode_transcript.runner_manager._update_task_from_response")
    @patch("pod.video_encode_transcript.runner_manager._try_send_to_rm")
    def test_submit_rejects_http_200_with_invalid_body(
        self,
        mocked_try_send_to_rm,
        mocked_update_task_from_response,
        mocked_prestore,
    ) -> None:
        """Skip a runner returning HTTP 200 with a non-JSON body (proxy error page)."""
        response = Mock()
        response.status_code = 200
        response.content = b"<html>HAProxy error</html>"
        response.headers = {"Content-Type": "text/html"}
        response.json.side_effect = ValueError("No JSON object could be decoded")
        mocked_try_send_to_rm.return_value = response

        rm = Mock()
        rm.name = "rm-haproxy"

        payload = {
            "etab_name": "Etab / Site",
            "app_name": "Esup-Pod",
            "app_version": "4.X",
            "task_type": "encoding",
            "source_url": "https://example.com/media/video.mp4",
            "notify_url": "https://example.com/runner/notify_task_end/",
            "parameters": {},
        }

        result = _submit_to_runner_manager(
            rm=rm,
            data=payload,
            task_type="encoding",
            source_type="video",
            video_id=123,
            recording_id=None,
        )

        self.assertFalse(result)
        mocked_update_task_from_response.assert_not_called()
        mocked_prestore.assert_not_called()

    @patch("pod.video_encode_transcript.runner_manager._prestore_encoding_if_needed")
    @patch("pod.video_encode_transcript.runner_manager._update_task_from_response")
    @patch("pod.video_encode_transcript.runner_manager._try_send_to_rm")
    def test_submit_rejects_http_200_with_invalid_json_type(
        self,
        mocked_try_send_to_rm,
        mocked_update_task_from_response,
        mocked_prestore,
    ) -> None:
        """Skip a runner returning HTTP 200 with JSON payload of unexpected type."""
        response = Mock()
        response.status_code = 200
        response.content = b'["proxy", "error"]'
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = ["proxy", "error"]
        mocked_try_send_to_rm.return_value = response

        rm = Mock()
        rm.name = "rm-invalid-json-type"

        payload = {
            "etab_name": "Etab / Site",
            "app_name": "Esup-Pod",
            "app_version": "4.X",
            "task_type": "encoding",
            "source_url": "https://example.com/media/video.mp4",
            "notify_url": "https://example.com/runner/notify_task_end/",
            "parameters": {},
        }

        result = _submit_to_runner_manager(
            rm=rm,
            data=payload,
            task_type="encoding",
            source_type="video",
            video_id=124,
            recording_id=None,
        )

        self.assertFalse(result)
        mocked_update_task_from_response.assert_not_called()
        mocked_prestore.assert_not_called()
