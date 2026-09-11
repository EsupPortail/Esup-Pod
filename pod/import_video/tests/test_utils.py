"""Esup-Pod tests for SSRF and filesystem protections in import_video utils.

test with `python manage.py test pod.import_video.tests.test_utils`
"""

from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from pod.import_video.utils import (
    define_dest_file_and_path,
    download_video_file,
    safe_request,
    validate_remote_import_url,
    verify_video_exists_and_size,
)


class DummyRedirectResponse:
    """Minimal response object for redirect validation tests."""

    def __init__(self, location: str):
        self.headers = {"Location": location}
        self.is_redirect = True
        self.closed = False

    def close(self):
        self.closed = True


class ImportVideoUtilsSecurityTest(SimpleTestCase):
    """Validate SSRF protections around remote imports."""

    def test_validate_remote_import_url_rejects_loopback_ip(self):
        """Local loopback addresses must be rejected."""
        with self.assertRaises(ValueError):
            validate_remote_import_url("http://127.0.0.1/video.mp4")

    @patch("pod.import_video.utils.requests.request")
    def test_verify_video_exists_and_size_rejects_private_url_before_request(
        self, mock_request
    ):
        """Blocked destinations must never trigger an outbound request."""
        with self.assertRaises(ValueError):
            verify_video_exists_and_size("http://127.0.0.1/video.mp4")

        mock_request.assert_not_called()

    def test_download_video_file_rejects_private_url_before_session_request(self):
        """Blocked downloads must fail before using the HTTP session."""
        session = Mock()

        with self.assertRaises(ValueError):
            download_video_file(session, "http://127.0.0.1/video.mp4", "/tmp/test.mp4")

        session.request.assert_not_called()

    def test_download_video_file_rejects_destination_outside_media_root(self):
        """A destination path cannot escape MEDIA_ROOT."""
        session = Mock()

        with TemporaryDirectory() as media_root, patch(
            "pod.import_video.utils.MEDIA_ROOT", media_root
        ):
            with self.assertRaises(ValueError):
                download_video_file(
                    session,
                    "https://example.org/video.mp4",
                    "/tmp/outside-media-root.mp4",
                )

        session.request.assert_not_called()

    def test_define_destination_rejects_owner_path_traversal(self):
        """Even a compromised owner path cannot control the created directory."""
        user = SimpleNamespace(owner=SimpleNamespace(hashkey="../../outside-media-root"))

        with TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root
        ), patch("pod.import_video.utils.MEDIA_ROOT", media_root), patch(
            "pod.import_video.utils.os.makedirs"
        ) as mock_makedirs:
            with self.assertRaises(ValueError):
                define_dest_file_and_path(user, "recording", "mp4")

        mock_makedirs.assert_not_called()

    @patch("pod.import_video.utils.socket.getaddrinfo")
    def test_validate_remote_import_url_accepts_public_host(self, mock_getaddrinfo):
        """Public hosts remain allowed."""
        mock_getaddrinfo.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 0)),
        ]
        url, addresses = validate_remote_import_url("https://example.org/video.mp4")
        self.assertEqual(
            url.geturl(),
            "https://example.org/video.mp4",
        )

    @patch("pod.import_video.utils.socket.getaddrinfo")
    def test_validate_remote_import_url_rejects_private_network(self, mock_getaddrinfo):
        """Private network destinations must be rejected."""
        mock_getaddrinfo.return_value = [
            (2, 1, 6, "", ("10.10.1.24", 0)),
        ]

        with self.assertRaises(ValueError):
            validate_remote_import_url("https://internal.example.org/video.mp4")

    @patch("pod.import_video.utils.requests.request")
    @patch("pod.import_video.utils.socket.getaddrinfo")
    def test_safe_request_blocks_redirect_to_private_host(
        self, mock_getaddrinfo, mock_request
    ):
        """Redirects to private destinations must be rejected."""
        mock_getaddrinfo.return_value = [
            (2, 1, 6, "", ("93.184.216.34", 0)),
        ]
        response = DummyRedirectResponse("http://127.0.0.1/private.mp4")
        mock_request.return_value = response

        with self.assertRaises(ValueError):
            safe_request("get", "https://public.example.org/video.mp4", timeout=2)

        self.assertTrue(response.closed)
        mock_request.assert_called_once()
