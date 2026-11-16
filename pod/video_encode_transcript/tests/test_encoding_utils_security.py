"""Esup-Pod security tests for encoding path helpers."""

import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pod.settings")


def _get_encoding_utils_module():
    """Import encoding_utils lazily after test settings environment is set."""
    from pod.video_encode_transcript import encoding_utils

    return encoding_utils


class EncodingUtilsSecurityTests(unittest.TestCase):
    """Validate path-security helpers used by encoding workflows."""

    def test_is_safe_file_path_allows_media_root_path(self) -> None:
        """Allow paths that resolve inside ``MEDIA_ROOT``."""
        encoding_utils = _get_encoding_utils_module()
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as media_root:
            candidate = os.path.join(media_root, "video.mp4")
            with patch.object(encoding_utils, "MEDIA_ROOT", media_root), patch.object(
                encoding_utils, "DEFAULT_RECORDER_PATH", ""
            ):
                self.assertTrue(encoding_utils._is_safe_file_path(candidate))

    def test_is_safe_file_path_rejects_outside_allowed_roots(self) -> None:
        """Reject paths that resolve outside authorized roots."""
        encoding_utils = _get_encoding_utils_module()
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as media_root:
            with patch.object(encoding_utils, "MEDIA_ROOT", media_root), patch.object(
                encoding_utils, "DEFAULT_RECORDER_PATH", ""
            ):
                self.assertFalse(encoding_utils._is_safe_file_path("/etc/passwd"))
                self.assertFalse(encoding_utils._is_safe_file_path(""))

    def test_check_file_requires_existing_non_empty_file(self) -> None:
        """Accept only existing non-empty files in allowed roots."""
        encoding_utils = _get_encoding_utils_module()
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as media_root:
            with patch.object(encoding_utils, "MEDIA_ROOT", media_root), patch.object(
                encoding_utils, "DEFAULT_RECORDER_PATH", ""
            ):
                non_empty = os.path.join(media_root, "ok.txt")
                empty = os.path.join(media_root, "empty.txt")
                missing = os.path.join(media_root, "missing.txt")
                with open(non_empty, "w", encoding="utf-8") as file_handler:
                    file_handler.write("data")
                with open(empty, "w", encoding="utf-8"):
                    pass

                self.assertTrue(encoding_utils.check_file(non_empty))
                self.assertFalse(encoding_utils.check_file(empty))
                self.assertFalse(encoding_utils.check_file(missing))
                self.assertFalse(encoding_utils.check_file("/etc/passwd"))
