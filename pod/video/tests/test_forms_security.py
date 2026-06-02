"""Esup-Pod security-focused tests for video forms helpers."""

import os
import tempfile
import unittest

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings

try:
    from pod.video.forms import safe_media_path

    SAFE_MEDIA_PATH_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - environment-dependent import guard
    safe_media_path = None
    SAFE_MEDIA_PATH_IMPORT_ERROR = exc


@unittest.skipIf(
    safe_media_path is None,
    f"safe_media_path import unavailable in this environment: {SAFE_MEDIA_PATH_IMPORT_ERROR}",
)
class VideoFormsSecurityTests(SimpleTestCase):
    """Test path validation helpers used by the video forms."""

    def test_safe_media_path_accepts_path_within_media_root(self) -> None:
        """Resolve a regular relative media path."""
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                expected = os.path.realpath(
                    os.path.join(media_root, "videos", "my-video.mp4")
                )
                self.assertEqual(
                    safe_media_path("videos/my-video.mp4"),
                    expected,
                )

    def test_safe_media_path_rejects_parent_path_traversal(self) -> None:
        """Reject traversal attempts escaping ``MEDIA_ROOT``."""
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                with self.assertRaises(ValidationError):
                    safe_media_path("../../etc/passwd")

    def test_safe_media_path_rejects_absolute_paths(self) -> None:
        """Reject absolute paths that are not relative to ``MEDIA_ROOT``."""
        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                with self.assertRaises(ValidationError):
                    safe_media_path("/etc/passwd")
