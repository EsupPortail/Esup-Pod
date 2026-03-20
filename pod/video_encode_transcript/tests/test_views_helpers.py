"""
Views helper unit tests for Esup-Pod video encoding workflows.

Run with `python manage.py test pod.video_encode_transcript.tests.test_views_helpers`
"""

import os
import shutil
import tempfile
import unittest
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import patch

import requests

from pod.video_encode_transcript.views import (
    _download_and_store_manifest_member,
    _format_video_directory,
    _get_destination_directory,
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
        self._touch(os.path.join(dest_dir, "only_dest.txt"), "ONLY_DEST")  # should remain
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
        self.assertFalse(os.path.exists(os.path.join(dest_dir, "dirX", "to_remove.txt")))
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

    def test_format_video_directory_uses_minimum_four_digits(self):
        """Format short numeric ids with leading zeros."""
        self.assertEqual(_format_video_directory(1), "0001")
        self.assertEqual(_format_video_directory("42"), "0042")
        self.assertEqual(_format_video_directory(12345), "12345")

    def test_get_destination_directory_uses_padded_video_id(self):
        """Build destination path with a zero-padded video id for encoding tasks."""
        task = SimpleNamespace(
            type="encoding",
            video=SimpleNamespace(
                id=1,
                owner=SimpleNamespace(owner=SimpleNamespace(hashkey="hash123")),
            ),
        )
        with patch("pod.video_encode_transcript.views.MEDIA_ROOT", self.tmp_root):
            with patch("pod.video_encode_transcript.views.VIDEOS_DIR", "videos"):
                dest_dir = _get_destination_directory(task)

        expected = os.path.join(self.tmp_root, "videos", "hash123", "0001")
        self.assertEqual(dest_dir, expected)

    def test_get_destination_directory_uses_padded_video_id_for_transcription(self):
        """Build destination path with a zero-padded video id for transcription tasks."""
        task = SimpleNamespace(
            type="transcription",
            video=SimpleNamespace(
                id=9,
                owner=SimpleNamespace(owner=SimpleNamespace(hashkey="hash123")),
            ),
        )
        with patch("pod.video_encode_transcript.views.MEDIA_ROOT", self.tmp_root):
            with patch("pod.video_encode_transcript.views.VIDEOS_DIR", "videos"):
                dest_dir = _get_destination_directory(task)

        expected = os.path.join(self.tmp_root, "videos", "hash123", "0009")
        self.assertEqual(dest_dir, expected)

    def test_download_and_store_manifest_member_retries_chunked_transfer(self):
        """Retry streamed download on chunked transfer break and overwrite partial data."""

        class FakeResponse:
            def __init__(
                self,
                chunks: list[bytes],
                error: Exception | None = None,
            ) -> None:
                self._chunks = chunks
                self._error = error
                self.closed = False

            def iter_content(self, chunk_size: int = 0):
                del chunk_size
                for chunk in self._chunks:
                    yield chunk
                if self._error is not None:
                    raise self._error

            def close(self) -> None:
                self.closed = True

        first = FakeResponse(
            [b"partial"],
            requests.exceptions.ChunkedEncodingError("Connection broken"),
        )
        second = FakeResponse([b"complete"])
        task = SimpleNamespace(id=7)

        with patch(
            "pod.video_encode_transcript.views._download_manifest_member",
            side_effect=[first, second],
        ) as mock_download:
            with patch("pod.video_encode_transcript.views.time.sleep") as mock_sleep:
                with patch(
                    "pod.video_encode_transcript.views._compute_manifest_retry_delay",
                    return_value=0.0,
                ):
                    dest_path = _download_and_store_manifest_member(
                        "https://runner.example/result/file",
                        {"Authorization": "Bearer test"},
                        "folder/video.mp4",
                        task,
                        self.tmp_root,
                        max_attempts=2,
                    )

        self.assertEqual(mock_download.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertTrue(first.closed)
        self.assertTrue(second.closed)
        self.assertIsNotNone(dest_path)
        self.assertTrue(isinstance(dest_path, str))
        with open(str(dest_path), "rb") as f:
            self.assertEqual(f.read(), b"complete")

    def test_download_and_store_manifest_member_removes_partial_file_on_failure(self):
        """Clean up partial file and return None when all retries fail."""

        class FailingResponse:
            def __init__(self) -> None:
                self.closed = False

            def iter_content(self, chunk_size: int = 0):
                del chunk_size
                yield b"incomplete"
                raise requests.exceptions.ChunkedEncodingError("stream interrupted")

            def close(self) -> None:
                self.closed = True

        responses = [FailingResponse(), FailingResponse()]
        task = SimpleNamespace(id=9)

        with patch(
            "pod.video_encode_transcript.views._download_manifest_member",
            side_effect=responses,
        ):
            with patch("pod.video_encode_transcript.views.time.sleep"):
                with patch(
                    "pod.video_encode_transcript.views._compute_manifest_retry_delay",
                    return_value=0.0,
                ):
                    dest_path = _download_and_store_manifest_member(
                        "https://runner.example/result/file",
                        {"Authorization": "Bearer test"},
                        "broken/output.bin",
                        task,
                        self.tmp_root,
                        max_attempts=2,
                    )

        self.assertIsNone(dest_path)
        self.assertFalse(
            os.path.exists(os.path.join(self.tmp_root, "broken", "output.bin"))
        )
        self.assertTrue(all(response.closed for response in responses))

    def test_download_and_store_manifest_member_retries_on_checksum_mismatch(self):
        """Retry when checksum validation fails and keep final valid file."""

        class FakeResponse:
            def __init__(self, chunks: list[bytes]) -> None:
                self._chunks = chunks
                self.closed = False

            def iter_content(self, chunk_size: int = 0):
                del chunk_size
                for chunk in self._chunks:
                    yield chunk

            def close(self) -> None:
                self.closed = True

        expected_hash = sha256(b"good-data").hexdigest()
        first = FakeResponse([b"bad-data"])
        second = FakeResponse([b"good-data"])
        task = SimpleNamespace(id=11)

        with patch(
            "pod.video_encode_transcript.views._download_manifest_member",
            side_effect=[first, second],
        ) as mock_download:
            with patch("pod.video_encode_transcript.views.time.sleep") as mock_sleep:
                with patch(
                    "pod.video_encode_transcript.views._compute_manifest_retry_delay",
                    return_value=0.0,
                ):
                    dest_path = _download_and_store_manifest_member(
                        "https://runner.example/result/file",
                        {"Authorization": "Bearer test"},
                        "checksum/output.bin",
                        task,
                        self.tmp_root,
                        expected_sha256=expected_hash,
                        max_attempts=2,
                    )

        self.assertEqual(mock_download.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertTrue(first.closed)
        self.assertTrue(second.closed)
        self.assertIsNotNone(dest_path)
        self.assertTrue(isinstance(dest_path, str))
        with open(str(dest_path), "rb") as f:
            self.assertEqual(f.read(), b"good-data")

    def test_download_and_store_manifest_member_atomic_write_keeps_existing_file(self):
        """Do not corrupt existing file when checksum validation fails."""

        class FakeResponse:
            def __init__(self, chunks: list[bytes]) -> None:
                self._chunks = chunks
                self.closed = False

            def iter_content(self, chunk_size: int = 0):
                del chunk_size
                for chunk in self._chunks:
                    yield chunk

            def close(self) -> None:
                self.closed = True

        expected_hash = sha256(b"expected").hexdigest()
        task = SimpleNamespace(id=12)
        existing_path = os.path.join(self.tmp_root, "atomic", "artifact.bin")
        os.makedirs(os.path.dirname(existing_path), exist_ok=True)
        with open(existing_path, "wb") as f:
            f.write(b"stable-data")

        failing_response = FakeResponse([b"corrupt-data"])
        with patch(
            "pod.video_encode_transcript.views._download_manifest_member",
            return_value=failing_response,
        ):
            dest_path = _download_and_store_manifest_member(
                "https://runner.example/result/file",
                {"Authorization": "Bearer test"},
                "atomic/artifact.bin",
                task,
                self.tmp_root,
                expected_sha256=expected_hash,
                max_attempts=1,
            )

        self.assertIsNone(dest_path)
        self.assertTrue(failing_response.closed)
        with open(existing_path, "rb") as f:
            self.assertEqual(f.read(), b"stable-data")


if __name__ == "__main__":
    unittest.main()
