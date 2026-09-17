"""Security regression tests for live views."""

import json
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.test import SimpleTestCase

from pod.live.views import create_video, event


class LiveErrorResponseSecurityTests(SimpleTestCase):
    """Check that internal errors are not disclosed by live endpoints."""

    def test_create_video_does_not_expose_exception_details(self) -> None:
        """Return a stable public error while logging the internal exception."""
        event = SimpleNamespace(
            owner=SimpleNamespace(owner=SimpleNamespace(hashkey="owner-hash"))
        )
        with patch("pod.live.views.Event.objects.get", return_value=event), patch(
            "pod.live.views.os.makedirs"
        ), patch(
            "pod.live.views.check_dir_exists",
            side_effect=RuntimeError("private filesystem details"),
        ):
            response = create_video(1, "test_event_video.mp4", "")

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.content)
        self.assertNotIn("private filesystem details", response_data["error"])

    def test_event_login_redirect_encodes_full_return_url(self) -> None:
        """A return URL query string cannot alter the login redirect target."""
        request = RequestFactory().get(
            "/live/event/1-event/?is_iframe=true&next=//evil.example"
        )
        request.user = AnonymousUser()
        request.resolver_match = SimpleNamespace(namespace="live")
        live_event = SimpleNamespace(is_restricted=True)

        with patch("pod.live.views.get_object_or_404", return_value=live_event):
            response = event(request, "1-event")

        location = urlsplit(response.url)
        query = parse_qs(location.query)
        self.assertEqual(location.netloc, "")
        self.assertEqual(query["is_iframe"], ["true"])
        self.assertEqual(query["referrer"], [request.get_full_path()])
