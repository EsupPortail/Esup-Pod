"""
Unit tests for Esup-Pod video encoding utilities.

Run with `python manage.py test pod.video_encode_transcript.tests.test_utils`
"""

import unittest
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from ..encoding_utils import get_dressing_position_value, sec_to_timestamp
from ..utils import send_email_item


class EncodingUtilitiesTests(unittest.TestCase):
    """TestCase for Esup-Pod encoding utilities."""

    def test_dressing_position_value(self) -> None:
        """Return the expected ffmpeg overlay expression for each watermark corner."""
        result = get_dressing_position_value("top_right", "720")
        self.assertEqual(result, "overlay=main_w-overlay_w-36.0:36.0")

        result = get_dressing_position_value("top_left", "720")
        self.assertEqual(result, "overlay=36.0:36.0")

        result = get_dressing_position_value("bottom_right", "720")
        self.assertEqual(result, "overlay=main_w-overlay_w-36.0:main_h-overlay_h-36.0")

        result = get_dressing_position_value("bottom_left", "720")
        self.assertEqual(result, "overlay=36.0:main_h-overlay_h-36.0")

        print(" ---> get_dressing_position_value: OK! --- EncodginUtilsTest")

    def test_sec_to_timestamp(self) -> None:
        """Convert seconds to a normalized HH:MM:SS.mmm timestamp string."""
        self.assertEqual(sec_to_timestamp(-1), "00:00:00.000")
        self.assertEqual(sec_to_timestamp(60.000), "00:01:00.000")
        print(" ---> sec_to_timestamp: OK! --- EncodginUtilsTest")


class SendEmailItemTests(SimpleTestCase):
    """Test admin alert email guards."""

    @override_settings(
        EMAIL_HOST="smtp.univ.fr",
        ADMINS=(("Name", "adminmail@univ.fr"),),
    )
    @patch("pod.video_encode_transcript.utils.mail_admins")
    def test_send_email_item_skips_placeholder_smtp_settings(
        self, mock_mail_admins
    ) -> None:
        """Do not attempt an SMTP send when project placeholder settings are unchanged."""
        send_email_item("Task 42 failed", "Task", "task-42")
        mock_mail_admins.assert_not_called()

    @override_settings(
        EMAIL_HOST="smtp.example.org",
        ADMINS=(("Ops", "ops@example.org"),),
    )
    @patch("pod.video_encode_transcript.utils.mail_admins")
    def test_send_email_item_uses_configured_smtp_settings(
        self, mock_mail_admins
    ) -> None:
        """Keep sending admin alert emails when SMTP settings are explicitly configured."""
        send_email_item("Task 42 failed", "Task", "task-42")
        mock_mail_admins.assert_called_once()

    @override_settings(EMAIL_HOST="smtp.example.org", ADMINS=())
    @patch("pod.video_encode_transcript.utils.mail_admins")
    def test_send_email_item_skips_when_admins_are_empty(self, mock_mail_admins) -> None:
        """Do not attempt an SMTP send when no admin recipients are configured."""
        send_email_item("Task 42 failed", "Task", "task-42")
        mock_mail_admins.assert_not_called()

    @override_settings(EMAIL_HOST="", ADMINS=(("Ops", "ops@example.org"),))
    @patch("pod.video_encode_transcript.utils.mail_admins")
    def test_send_email_item_skips_when_email_host_is_empty(
        self, mock_mail_admins
    ) -> None:
        """Do not attempt an SMTP send when the SMTP host is not configured."""
        send_email_item("Task 42 failed", "Task", "task-42")
        mock_mail_admins.assert_not_called()
