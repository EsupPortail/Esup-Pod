"""
Views helper unit tests for video encoding workflows.

Run with `python manage.py test pod.video_encode_transcript.tests.test_views_helpers`
"""

import os
import shutil
import tempfile
import unittest

from pod.video_encode_transcript.views import (
    _get_user_hashkey_from_recording,
    _merge_or_move_directory,
)


class FakeOwner:
    """Minimal owner-like object exposing a hashkey."""

    def __init__(self, hashkey):
        self.hashkey = hashkey


class FakeUser:
    """Minimal user-like object exposing an owner relation."""

    def __init__(self, owner):
        self.owner = owner


class FakeRecording:
    """Minimal recording-like object exposing a user relation."""

    def __init__(self, user):
        self.user = user


class ViewsHelpersTests(unittest.TestCase):
    """Test utility helpers used by view-side studio ingestion flow."""

    def setUp(self) -> None:
        """Create a dedicated temporary root folder for each test."""
        self.tmp_root = tempfile.mkdtemp(prefix="podv4_test_")

    def tearDown(self) -> None:
        """Clean up temporary files created during the test."""
        try:
            shutil.rmtree(self.tmp_root)
        except Exception:
            pass

    def _touch(self, path: str, content: str = "x") -> None:
        """Create a file with content, creating parent directories as needed."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_merge_or_move_directory_move_when_dest_absent(self):
        """Move source directory as-is when destination does not exist."""
        src_dir = os.path.join(self.tmp_root, "src")
        dest_dir = os.path.join(self.tmp_root, "dest")
        os.makedirs(src_dir, exist_ok=True)
        self._touch(os.path.join(src_dir, "a.txt"), "A")
        os.makedirs(os.path.join(src_dir, "sub"), exist_ok=True)
        self._touch(os.path.join(src_dir, "sub", "b.txt"), "B")

        _merge_or_move_directory(src_dir, dest_dir)

        self.assertFalse(os.path.exists(src_dir))
        self.assertTrue(os.path.isdir(dest_dir))
        with open(os.path.join(dest_dir, "a.txt"), "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "A")
        with open(os.path.join(dest_dir, "sub", "b.txt"), "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "B")

    def test_merge_or_move_directory_merge_when_dest_exists(self):
        """Merge source content into destination and replace collisions with source files."""
        src_dir = os.path.join(self.tmp_root, "src")
        dest_dir = os.path.join(self.tmp_root, "dest")
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(dest_dir, exist_ok=True)

        # Files in src
        self._touch(os.path.join(src_dir, "same.txt"), "SRC")
        self._touch(os.path.join(src_dir, "only_src.txt"), "ONLY_SRC")
        os.makedirs(os.path.join(src_dir, "dirX"), exist_ok=True)
        self._touch(os.path.join(src_dir, "dirX", "in_src.txt"), "IN_SRC")

        # Files in dest
        self._touch(os.path.join(dest_dir, "same.txt"), "DEST")  # should be replaced
        self._touch(
            os.path.join(dest_dir, "only_dest.txt"), "ONLY_DEST"
        )  # should remain
        os.makedirs(os.path.join(dest_dir, "dirX"), exist_ok=True)
        self._touch(
            os.path.join(dest_dir, "dirX", "to_remove.txt"), "TO_REMOVE"
        )  # dir should be replaced

        _merge_or_move_directory(src_dir, dest_dir)

        # src dir removed
        self.assertFalse(os.path.exists(src_dir))
        # dest contains merged content
        with open(os.path.join(dest_dir, "same.txt"), "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "SRC")  # replaced by src
        with open(os.path.join(dest_dir, "only_dest.txt"), "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "ONLY_DEST")  # preserved
        with open(os.path.join(dest_dir, "only_src.txt"), "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "ONLY_SRC")  # added
        # dirX replaced by src version
        self.assertTrue(os.path.isdir(os.path.join(dest_dir, "dirX")))
        self.assertFalse(
            os.path.exists(os.path.join(dest_dir, "dirX", "to_remove.txt"))
        )
        with open(
            os.path.join(dest_dir, "dirX", "in_src.txt"), "r", encoding="utf-8"
        ) as f:
            self.assertEqual(f.read(), "IN_SRC")

    def test_get_user_hashkey_from_recording_success(self):
        """Extract owner hashkey from a well-formed recording-like object."""
        fake = FakeRecording(FakeUser(FakeOwner("abc123")))
        hk = _get_user_hashkey_from_recording(fake)
        self.assertEqual(hk, "abc123")

    def test_get_user_hashkey_from_recording_failure(self):
        """Raise RuntimeError when expected nested attributes are missing."""

        class BadRecording:
            pass

        with self.assertRaises(RuntimeError):
            _get_user_hashkey_from_recording(BadRecording())


if __name__ == "__main__":
    unittest.main()
