"""Keep long video uploads authenticated without extending inactive sessions."""

import json
import tempfile
import time
from unittest.mock import Mock, patch

from chunked_upload.models import ChunkedUpload
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.backends.cache import SessionStore
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.utils import timezone

from pod.video.views import PodChunkedUploadView


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "video-upload-session-tests",
        }
    },
    SESSION_ENGINE="django.contrib.sessions.backends.cache",
    SESSION_COOKIE_AGE=4 * 60 * 60,
    SESSION_EXPIRE_AT_BROWSER_CLOSE=True,
    SESSION_SAVE_EVERY_REQUEST=False,
)
class UploadSessionTests(SimpleTestCase):
    """Exercise actual chunk writes and session middleware without a database."""

    def setUp(self):
        """Isolate session storage, upload files and the passage of time."""
        self.now = time.time()
        clock = patch("time.time", side_effect=lambda: self.now)
        clock.start()
        self.addCleanup(clock.stop)
        cache.clear()
        self.addCleanup(cache.clear)

        self.factory = RequestFactory()
        self.user = User(pk=1, username="uploader")
        self.session = SessionStore()
        self.session[SESSION_KEY] = str(self.user.pk)
        self.session.save()
        self.session_key = self.session.session_key
        self.middleware = SessionMiddleware(self.respond)

        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        storage = patch.object(
            ChunkedUpload._meta.get_field("file"),
            "storage",
            FileSystemStorage(location=directory.name),
        )
        storage.start()
        self.addCleanup(storage.stop)
        self.upload = ChunkedUpload(
            pk=1, filename="video.mp4", created_on=timezone.now(), user=self.user
        )
        self.upload.file.save("video.part", ContentFile(b""), save=False)

        for replacement in (
            patch("chunked_upload.views.get_object_or_404", return_value=self.upload),
            patch.object(ChunkedUpload, "save"),
            patch("pod.video.views.RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY", False),
        ):
            replacement.start()
            self.addCleanup(replacement.stop)

    def respond(self, request):
        """Resolve the test user only while its stored session remains valid."""
        request.user = (
            self.user if request.session.get(SESSION_KEY) else AnonymousUser()
        )
        return PodChunkedUploadView.as_view()(request)

    def send_chunk(self, content=b"video", start=None):
        """Send a real multipart chunk through the view and session middleware."""
        if start is None:
            start = self.upload.offset
        self.request = self.factory.post(
            "/video/api/chunked_upload/",
            {
                "upload_id": self.upload.upload_id,
                "the_file": SimpleUploadedFile("video.mp4", content),
            },
            HTTP_CONTENT_RANGE=f"bytes {start}-{start + len(content) - 1}/1000",
            HTTP_COOKIE=f"{settings.SESSION_COOKIE_NAME}={self.session_key}",
        )
        return self.middleware(self.request)

    def assert_session_active(self):
        """Reload the persisted session rather than using an in-memory copy."""
        self.assertEqual(SessionStore(self.session_key).get(SESSION_KEY), "1")

    def test_successful_chunk_preserves_response_file_and_session_cookie(self):
        """Renew the session while retaining the existing upload protocol."""
        self.now += 3 * 60 * 60
        response = self.send_chunk()

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload["upload_id"], self.upload.upload_id)
        self.assertEqual(payload["offset"], 5)
        self.assertEqual(set(payload), {"upload_id", "offset", "expires"})
        with open(self.upload.file.path, "rb") as uploaded:
            self.assertEqual(uploaded.read(), b"video")
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertEqual(cookie.value, self.session_key)
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["max-age"], "")

        self.now += 3 * 60 * 60
        self.assert_session_active()

    def test_upload_can_continue_for_nine_hours_then_expire_when_idle(self):
        """Each accepted chunk restarts the four hours without an extra request."""
        for _ in range(3):
            self.now += 3 * 60 * 60
            response = self.send_chunk()
            self.assertEqual(response.status_code, 200)
            self.assertTrue(self.request.user.is_authenticated)
            self.assert_session_active()

        self.assertEqual(self.upload.offset, 15)
        self.now += settings.SESSION_COOKIE_AGE - 1
        self.assert_session_active()
        self.now += 2
        self.assertIsNone(SessionStore(self.session_key).get(SESSION_KEY))

    def test_rejected_chunk_does_not_extend_session_or_write_file(self):
        """An offset error keeps the original session deadline and upload data."""
        self.now += 3 * 60 * 60
        response = self.send_chunk(start=20)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.request.session.modified)
        self.assertNotIn(settings.SESSION_COOKIE_NAME, response.cookies)
        self.assertEqual(self.upload.offset, 0)
        self.now += 60 * 60 + 1
        self.assertIsNone(SessionStore(self.session_key).get(SESSION_KEY))

    def test_custom_session_lifetime_is_preserved(self):
        """Renew using the session's configured lifetime rather than forcing four hours."""
        self.session.set_expiry(600)
        self.session.save()
        self.now += 300
        self.assertEqual(self.send_chunk().status_code, 200)
        self.now += 599
        self.assert_session_active()
        self.now += 2
        self.assertIsNone(SessionStore(self.session_key).get(SESSION_KEY))

    def test_anonymous_callback_does_not_create_a_session(self):
        """The renewal hook never creates an authenticated or anonymous session."""
        request = self.factory.post("/")
        self.middleware.process_request(request)
        request.user = AnonymousUser()

        PodChunkedUploadView().get_response_data(self.upload, request)

        self.assertFalse(request.session.modified)
        self.assertIsNone(request.session.session_key)

    def test_account_excluded_by_staff_restriction_is_not_refreshed(self):
        """Respect the existing upload access restriction when renewing sessions."""
        request = self.factory.post("/")
        self.middleware.process_request(request)
        request.user = self.user
        with patch("pod.video.views.RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY", True):
            PodChunkedUploadView().get_response_data(self.upload, request)

        self.assertFalse(request.session.modified)

    @override_settings(SESSION_ENGINE="redis_sessions.session")
    def test_redis_backend_resets_the_ttl_using_the_existing_session(self):
        """Verify the installed Redis backend saves the same session with a fresh TTL."""
        from redis_sessions.session import SessionStore as RedisSessionStore

        server = Mock()
        with patch("redis_sessions.session.RedisServer.get", return_value=server):
            stored_session = RedisSessionStore(self.session_key)
            server.get.return_value = stored_session.encode({SESSION_KEY: "1"})
            self.middleware = SessionMiddleware(self.respond)

            response = self.send_chunk()

        self.assertEqual(response.status_code, 200)
        server.setex.assert_called_once()
        key, lifetime, encoded = server.setex.call_args.args
        self.assertEqual(key, stored_session.get_real_stored_key(self.session_key))
        self.assertEqual(lifetime, settings.SESSION_COOKIE_AGE)
        self.assertEqual(stored_session.decode(encoded)[SESSION_KEY], "1")
