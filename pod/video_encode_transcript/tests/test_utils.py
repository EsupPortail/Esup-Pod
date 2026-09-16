"""
Unit tests for Esup-Pod video encoding utilities.

Run with `python manage.py test pod.video_encode_transcript.tests.test_utils`
"""

import unittest
from unittest.mock import MagicMock, patch

from django.core import mail
from django.test import SimpleTestCase, override_settings
from django.utils.translation import override

from .. import utils
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


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_SUBJECT_PREFIX="[UniCApod] ",
    MANAGERS=(("Manager", "manager@example.org"),),
    LANGUAGE_CODE="en",
)
class CompletionEmailTests(SimpleTestCase):
    """Check completion messages as received by owners and managers."""

    def setUp(self) -> None:
        """Prepare a video without database access or external email delivery."""
        self.video = MagicMock(id=42, title="example.mp4", slug="0042-example")
        self.video.owner.email = "owner@example.org"
        self.video.owner.__str__.return_value = "Alice"
        self.video.owner.owner.establishment = "university"
        self.video.date_added = "2026-09-16"
        self.video.get_full_url.return_value = "//example.org/video/0042-example/"
        patcher = patch.multiple(
            utils,
            DEBUG=False,
            __TITLE_SITE__="UniCApod",
            USE_ESTABLISHMENT_FIELD=False,
            MANAGERS=(),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_subject_prefix_for_owner_and_managers(self) -> None:
        """Use the configured prefix once, with the site name as an empty fallback."""
        for prefix in ("[UniCApod] ", "[Custom] ", ""):
            with self.subTest(prefix=prefix), override_settings(
                EMAIL_SUBJECT_PREFIX=prefix
            ):
                mail.outbox.clear()
                utils.send_email_encoding(self.video)

                self.assertEqual(len(mail.outbox), 2)
                self.assertEqual(mail.outbox[0].to, ["manager@example.org"])
                self.assertEqual(mail.outbox[1].to, ["owner@example.org"])
                for message in mail.outbox:
                    self.assertEqual(
                        message.subject,
                        (prefix or "[UniCApod] ") + "Encoding #42 completed",
                    )

    def test_subject_prefix_for_establishment_managers(self) -> None:
        """Apply the same prefix to messages sent with establishment managers in BCC."""
        with patch.multiple(
            utils,
            USE_ESTABLISHMENT_FIELD=True,
            MANAGERS=(("university", "establishment@example.org"),),
        ):
            for prefix in ("[UniCApod] ", "[Custom] ", ""):
                with self.subTest(prefix=prefix), override_settings(
                    EMAIL_SUBJECT_PREFIX=prefix
                ):
                    mail.outbox.clear()
                    utils.send_email_encoding(self.video)

                    self.assertEqual(len(mail.outbox), 1)
                    self.assertEqual(mail.outbox[0].to, ["owner@example.org"])
                    self.assertEqual(mail.outbox[0].bcc, ["establishment@example.org"])
                    self.assertEqual(
                        mail.outbox[0].subject,
                        (prefix or "[UniCApod] ") + "Encoding #42 completed",
                    )

    def test_french_encoding_email(self) -> None:
        """Render correct French agreements and spaces in both email formats."""
        with override("fr"):
            utils.send_email_encoding(self.video)

        self.assertEqual(len(mail.outbox), 2)
        for message in mail.outbox:
            self.assertEqual(message.subject, "[UniCApod] Encodage du #42 est terminé")
            for body in (message.body, message.alternatives[0][0]):
                self.assertIn("a été encodée aux formats Web", body)
        for body in (mail.outbox[0].body, mail.outbox[0].alternatives[0][0]):
            self.assertIn("Posté par\u00a0: Alice", body)
            self.assertIn("le\u00a0: 2026-09-16", body)

    def test_french_transcription_email(self) -> None:
        """Preserve feminine agreement for transcription and masculine for content."""
        with override("fr"):
            utils.send_email_transcript(self.video)

        self.assertEqual(len(mail.outbox), 2)
        for message in mail.outbox:
            self.assertEqual(
                message.subject,
                "[UniCApod] La transcription du contenu du #42 est terminée",
            )
            self.assertIn("a été automatiquement transcrit", message.body)

    @patch("pod.video_encode_transcript.utils.notify_user")
    def test_french_encoding_push_notification(self, mock_notify_user) -> None:
        """Keep the site name and encoding agreement in push notifications."""
        with override("fr"):
            utils.send_notification_encoding(self.video)

        mock_notify_user.assert_called_once()
        self.assertEqual(
            mock_notify_user.call_args.args[1],
            "[UniCApod] Encodage du #42 est terminé",
        )
