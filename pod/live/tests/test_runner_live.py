"""Esup-Pod tests for automatic Live discovery, configuration and playback access."""

from unittest.mock import Mock, patch

import requests
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import (
    RequestFactory,
    SimpleTestCase,
    TestCase,
    TransactionTestCase,
    override_settings,
)
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from pod.live.admin import BroadcasterAdmin
from pod.authentication.models import AccessGroup
from pod.live.forms import BroadcasterAdminForm
from pod.live.models import Broadcaster, Building, Event
from pod.live.rest_views import BroadcasterSerializer
from pod.live.runner_live import get_stream_info, log_playback_context
from pod.video.models import Type
from pod.video_encode_transcript.models import RunnerManager

HLS_URL = "https://media.example.com/runner-2/hls/session/master.m3u8?signature=exact"


def response(payload, status=200):
    """Build a mocked HTTP response containing the supplied Live JSON."""
    return Mock(status_code=status, json=Mock(return_value=payload))


def session(live_id="session-1", state="running", ready=True, url=HLS_URL):
    """Build manager session information with the requested playback state."""
    return {
        "live_id": live_id,
        "source_id": "source-A",
        "state": state,
        "hls_ready": ready,
        "hls_url": url,
    }


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class RunnerLiveResolverTests(SimpleTestCase):
    """Check Live discovery, strict HLS readiness and short cache behavior."""

    def setUp(self):
        """Isolate the cache and prepare an explicit manager and Live source."""
        cache.clear()
        self.manager = RunnerManager(
            id=12,
            url="https://manager.example.com/prefix/",
            token="private-token",
            supports_live=True,
        )
        self.broadcaster = Broadcaster(
            id=3,
            name="Pod name",
            slug="pod-slug",
            stream_mode=Broadcaster.StreamMode.ESUP_RUNNER,
            runner_manager=self.manager,
            source_id="source-A",
            url="https://obsolete.example.com/fixed.m3u8",
            status=False,
        )
        self.get_patch = patch("pod.live.runner_live.requests.get")
        self.get = self.get_patch.start()
        self.addCleanup(self.get_patch.stop)

    def discover(self, refreshed=None, snapshot=None):
        """Mock source discovery followed by the refreshed session response."""
        self.get.side_effect = [
            response({"live": snapshot or session()}),
            response(refreshed or session()),
        ]

    def test_refreshes_snapshot_and_uses_exact_hls_despite_false_callback_status(self):
        """Refresh the snapshot and use the exact HLS URL independently of status."""
        self.discover()
        result = get_stream_info(self.broadcaster)
        self.assertEqual(result["hls_url"], HLS_URL)
        self.assertTrue(result["hls_ready"])
        self.assertEqual(
            [call.args[0] for call in self.get.call_args_list],
            [
                "https://manager.example.com/prefix/live/sources/source-A",
                "https://manager.example.com/prefix/live/session-1",
            ],
        )
        for call in self.get.call_args_list:
            self.assertEqual(
                call.kwargs["headers"]["Authorization"], "Bearer private-token"
            )
            self.assertEqual(call.kwargs["timeout"], (2, 4))
            self.assertFalse(call.kwargs["allow_redirects"])
        self.assertNotIn("private-token", str(result))

    def test_static_url_is_unchanged_without_manager_calls(self):
        """Preserve fixed URL playback without contacting a runner manager."""
        self.broadcaster.stream_mode = Broadcaster.StreamMode.STATIC
        self.assertEqual(self.broadcaster.get_stream_url(), self.broadcaster.url)
        self.get.assert_not_called()

    def test_null_session_waits_without_using_fixed_url(self):
        """Wait for a session instead of falling back to an obsolete fixed URL."""
        self.get.return_value = response({"live": None})
        result = get_stream_info(self.broadcaster)
        self.assertIsNone(result["hls_url"])
        self.assertEqual(result["state"], "waiting_source")
        self.get.assert_called_once()

    def test_every_non_ready_state_removes_snapshot_url(self):
        """Hide the HLS URL in every lifecycle state that cannot be played."""
        for state in (
            "pending",
            "waiting_source",
            "starting",
            "stopping",
            "completed",
            "failed",
        ):
            with self.subTest(state=state):
                cache.clear()
                self.discover(session(state=state))
                result = get_stream_info(self.broadcaster)
                self.assertIsNone(result["hls_url"])
                self.assertFalse(result["hls_ready"])

    def test_requires_boolean_readiness_and_valid_http_url(self):
        """Require strict HLS readiness and a valid HTTP or HTTPS playback URL."""
        for ready, url in (
            (False, HLS_URL),
            ("true", HLS_URL),
            (1, HLS_URL),
            (True, None),
            (True, "file:///private"),
            (True, 7),
        ):
            with self.subTest(ready=ready, url=url):
                cache.clear()
                self.discover(session(ready=ready, url=url))
                self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])

    def test_snapshot_is_never_played_when_refresh_is_not_ready(self):
        """Ignore a playable snapshot when refreshed HLS is not ready."""
        self.discover(session(state="starting", ready=False))
        self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])

    def test_short_cache_is_shared_and_expires_into_new_source_discovery(self):
        """Reuse short cache results and discover a new session after expiration."""
        self.discover()
        with patch("pod.live.runner_live.cache.set", wraps=cache.set) as save:
            first = get_stream_info(self.broadcaster)
            self.assertEqual(get_stream_info(self.broadcaster), first)
            self.assertEqual(self.get.call_count, 2)
            result_saves = [
                call
                for call in save.call_args_list
                if call.args[1] == first and not call.args[0].endswith(":last-ready")
            ]
            self.assertEqual(len(result_saves), 1)
            self.assertEqual(result_saves[0].kwargs["timeout"], 20)
        cache.clear()
        replacement = session(
            live_id="session-2", url=HLS_URL.replace("session/", "session-2/")
        )
        self.discover(replacement, replacement)
        self.assertEqual(get_stream_info(self.broadcaster)["live_id"], "session-2")
        self.assertEqual(self.get.call_count, 4)
        self.assertTrue(
            self.get.call_args_list[2].args[0].endswith("/sources/source-A")
        )

    def test_stop_then_republish_discovers_replacement_instead_of_pinning_old_id(self):
        """Discover a replacement session after stopping and republishing RTMP."""
        for expected in (
            session(),
            session(state="completed"),
            session(live_id="session-2"),
        ):
            cache.clear()
            self.discover(expected, expected)
            result = get_stream_info(self.broadcaster)
            self.assertEqual(result["live_id"], expected["live_id"])
            self.assertEqual(bool(result["hls_url"]), expected["state"] == "running")

    def test_changed_connection_settings_invalidate_the_cache(self):
        """Invalidate cached playback information when manager credentials change."""
        self.discover()
        get_stream_info(self.broadcaster)
        self.manager.token = "rotated-token"
        self.discover(session(state="completed"))
        self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
        self.assertEqual(self.get.call_count, 4)

    def test_errors_are_cached_without_exposing_details_or_reusing_old_url(self):
        """Cache unavailable playback without retaining old URLs or error secrets."""
        self.discover()
        get_stream_info(self.broadcaster)
        cache.clear()
        self.get.side_effect = requests.Timeout("private-token and response secrets")
        with self.assertLogs("pod.live", level="WARNING") as logs:
            result = get_stream_info(self.broadcaster)
        self.assertIsNone(result["hls_url"])
        self.assertNotIn("private-token", str(logs.output) + str(result))
        self.assertEqual(get_stream_info(self.broadcaster), result)
        self.assertEqual(self.get.call_count, 3)

    def test_http_errors_identify_manager_stage_and_status_without_response_body(self):
        """Identify the failing HTTP step without logging remote response secrets."""
        for stage, status in (("source", 404), ("session", 403)):
            with self.subTest(stage=stage, status=status):
                cache.clear()
                failed = response({"detail": "private-token"}, status=status)
                failed.text = "response secrets"
                self.get.side_effect = (
                    [failed]
                    if stage == "source"
                    else [response({"live": session()}), failed]
                )
                with self.assertLogs("pod.live", level="WARNING") as logs:
                    result = get_stream_info(self.broadcaster)
                message = logs.output[0]
                self.assertIn("broadcaster 3", message)
                self.assertIn("manager_id=12", message)
                self.assertIn(f"stage={stage}", message)
                self.assertIn("reason=http_error", message)
                self.assertIn(f"http_status={status}", message)
                self.assertNotIn("private-token", message)
                self.assertNotIn("response secrets", message)
                failed.json.assert_not_called()
                self.assertEqual(result["state"], "unavailable")

    def test_network_errors_have_safe_and_distinct_diagnostics(self):
        """Distinguish timeout, TLS and connection failures without exception text."""
        for error_type, reason in (
            (requests.Timeout, "timeout"),
            (requests.exceptions.SSLError, "tls_error"),
            (requests.ConnectionError, "connection_error"),
            (requests.RequestException, "request_error"),
        ):
            with self.subTest(reason=reason):
                cache.clear()
                self.get.side_effect = error_type("private-token and response secrets")
                with self.assertLogs("pod.live", level="WARNING") as logs:
                    get_stream_info(self.broadcaster)
                message = logs.output[0]
                self.assertIn("stage=source", message)
                self.assertIn(f"reason={reason}", message)
                self.assertNotIn("private-token", message)
                self.assertNotIn("response secrets", message)

    def test_contract_errors_report_safe_categories_for_source_and_session(self):
        """Describe malformed source and session responses using controlled codes."""
        cases = (
            (
                [Mock(status_code=200, json=Mock(side_effect=ValueError("secret")))],
                "source",
                "invalid_json",
            ),
            ([response([])], "source", "invalid_payload"),
            ([response({})], "source", "missing_live"),
            ([response({"live": []})], "source", "invalid_live_session"),
            ([response({"live": {"live_id": ""}})], "source", "missing_live_id"),
            (
                [response({"live": session()}), response(session(live_id="wrong"))],
                "session",
                "session_mismatch",
            ),
            (
                [response({"live": session()}), response(session(state="secret"))],
                "session",
                "invalid_state",
            ),
            (
                [
                    response({"live": session()}),
                    response(session(url="file:///secret")),
                ],
                "session",
                "invalid_hls_url",
            ),
        )
        for replies, stage, reason in cases:
            with self.subTest(reason=reason):
                cache.clear()
                self.get.side_effect = replies
                with self.assertLogs("pod.live", level="WARNING") as logs:
                    result = get_stream_info(self.broadcaster)
                message = logs.output[0]
                self.assertIn(f"stage={stage}", message)
                self.assertIn(f"reason={reason}", message)
                self.assertNotIn("secret", message)
                self.assertNotIn("private-token", message)
                self.assertIsNone(result["hls_url"])

    def test_http_json_and_contract_errors_fail_closed(self):
        """Remove playback URLs on HTTP, JSON or Live contract errors."""
        bad_responses = [
            response({}, status=401),
            response({}, status=403),
            response({}, status=404),
            response({}, status=503),
            response({}, status=302),
            response([]),
            response({}),
            Mock(status_code=200, json=Mock(side_effect=ValueError("private-token"))),
            response({"live": []}),
            response({"live": {"live_id": ""}}),
        ]
        for bad in bad_responses:
            with self.subTest(bad=bad):
                cache.clear()
                self.get.side_effect = None
                self.get.return_value = bad
                self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
        for bad in (
            session(live_id="wrong"),
            dict(session(), source_id="another-source"),
            dict(session(), state="unknown"),
            {},
        ):
            cache.clear()
            self.get.side_effect = [response({"live": session()}), response(bad)]
            self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])

    def test_missing_or_disabled_manager_never_uses_fallback_or_other_managers(self):
        """Keep playback unavailable when its explicit manager cannot be used."""
        self.manager.is_active = False
        self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
        self.broadcaster.runner_manager = None
        self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
        self.get.assert_not_called()

    def test_disabling_live_support_invalidates_previously_ready_playback(self):
        """Discard cached HLS when the manager no longer supports Live."""
        self.discover()
        self.assertEqual(get_stream_info(self.broadcaster)["hls_url"], HLS_URL)
        self.manager.supports_live = False
        self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
        self.assertEqual(self.get.call_count, 2)
        self.manager.supports_live = True
        self.discover(session(state="completed"))
        self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
        self.assertEqual(self.get.call_count, 4)

    @override_settings(
        ESUP_RUNNER_LIVE_CACHE_TIMEOUT=0, ESUP_RUNNER_LIVE_READY_CACHE_TIMEOUT=0
    )
    def test_availability_logs_changes_without_urls_or_repeating_unchanged_state(self):
        """Report lifecycle changes while keeping stable polling quiet and private."""
        self.manager.url = "http://manager.example.com/"
        with patch("pod.live.runner_live.logger") as logs:
            self.discover()
            get_stream_info(self.broadcaster)
            self.discover()
            get_stream_info(self.broadcaster)
            self.assertEqual(logs.info.call_count, 1)
            self.discover(session(state="completed"))
            get_stream_info(self.broadcaster)
            self.assertEqual(logs.info.call_count, 2)
            self.discover(
                session(live_id="new-session"), session(live_id="new-session")
            )
            get_stream_info(self.broadcaster)
            self.assertEqual(logs.info.call_count, 3)
            self.discover(
                session(live_id="replacement"), session(live_id="replacement")
            )
            get_stream_info(self.broadcaster)
            self.assertEqual(logs.info.call_count, 4)
        self.assertEqual(
            logs.info.call_args_list[0].args[3:], ("running", True, True, "https")
        )
        self.assertEqual(
            logs.info.call_args_list[1].args[3:], ("completed", True, False, None)
        )
        self.assertNotIn("private-token", str(logs.mock_calls))
        self.assertNotIn(HLS_URL, str(logs.mock_calls))

    def test_secure_playback_warns_about_http_hls_without_rewriting_or_leaking_url(
        self,
    ):
        """Explain mixed content once per minute without disclosing the media URL."""
        insecure_url = "http://media.example.com/live.m3u8?secret=private-token"
        self.discover(session(url=insecure_url))
        stream = get_stream_info(self.broadcaster)
        request = RequestFactory().get("/live/direct/pod-slug/", secure=True)
        with patch("pod.live.runner_live.logger") as logs:
            log_playback_context(self.broadcaster, stream, request)
            log_playback_context(self.broadcaster, stream, request)
        self.assertEqual(logs.warning.call_count, 1)
        self.assertIn("reason=mixed_content", logs.warning.call_args.args[0])
        self.assertNotIn("private-token", str(logs.mock_calls))
        self.assertEqual(stream["hls_url"], insecure_url)

    def test_http_manager_with_https_hls_is_compatible_with_secure_playback(self):
        """Keep server-side HTTP discovery separate from browser media security."""
        self.manager.url = "http://manager.example.com/"
        self.discover()
        stream = get_stream_info(self.broadcaster)
        request = RequestFactory().get("/live/direct/pod-slug/", secure=True)
        with patch("pod.live.runner_live.logger") as logs:
            log_playback_context(self.broadcaster, stream, request)
        logs.warning.assert_not_called()
        self.assertEqual(stream["hls_url"], HLS_URL)

    def test_http_playback_with_http_hls_has_no_mixed_content_warning(self):
        """Allow HTTP media on an HTTP page without a misleading security warning."""
        self.discover(session(url="http://media.example.com/live.m3u8"))
        stream = get_stream_info(self.broadcaster)
        request = RequestFactory().get("/live/direct/pod-slug/")
        with patch("pod.live.runner_live.logger") as logs:
            log_playback_context(self.broadcaster, stream, request)
        logs.warning.assert_not_called()


class RunnerLiveDatabaseTestCase(TestCase):
    """Share explicit Live configuration across database regression tests."""

    def setUp(self):
        """Create the site, building, manager and broadcaster shared by DB tests."""
        cache.clear()
        Site.objects.clear_cache()
        self.addCleanup(Site.objects.clear_cache)
        self.site = Site.objects.get_current()
        self.building = Building.objects.create(name="Live building")
        self.manager = RunnerManager.objects.create(
            name="Live manager",
            url="https://manager.example.com/",
            token="private-token",
            site=self.site,
            supports_live=True,
        )
        self.broadcaster = Broadcaster.objects.create(
            name="Live broadcaster",
            building=self.building,
            stream_mode=Broadcaster.StreamMode.ESUP_RUNNER,
            runner_manager=self.manager,
            source_id="source-A",
        )


class RunnerLiveConfigurationTests(RunnerLiveDatabaseTestCase):
    """Check Live model, admin form and REST configuration validation."""

    def test_manager_live_support_is_disabled_by_default(self):
        """Require explicit opt-in before a manager can be used for Live."""
        manager = RunnerManager.objects.create(
            name="Task manager",
            url="https://tasks.example.com/",
            token="task-token",
            site=self.site,
        )
        manager.refresh_from_db()
        self.assertFalse(manager.supports_live)

    def test_manager_without_live_support_is_rejected_by_model_form_and_rest(self):
        """Reject managers without Live support, including partial API updates."""
        self.manager.supports_live = False
        self.manager.save(update_fields=["supports_live"])
        with self.assertRaises(ValidationError) as error:
            self.broadcaster.clean()
        self.assertIn("runner_manager", error.exception.message_dict)
        form = BroadcasterAdminForm(self.form_data())
        self.assertNotIn(self.manager, form.fields["runner_manager"].queryset)
        self.assertFalse(form.is_valid())
        self.assertIn("runner_manager", form.errors)
        for data in ({"runner_manager": self.manager.pk}, {"status": True}):
            with self.subTest(data=data):
                serializer = BroadcasterSerializer(
                    self.broadcaster, data=data, partial=True
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn("runner_manager", serializer.errors)

    def test_multiple_live_broadcasters_can_omit_url_and_manager_is_protected(self):
        """Allow empty Live URLs and protect the referenced manager from deletion."""
        self.broadcaster.full_clean(exclude=["piloting_implementation"])
        second = Broadcaster.objects.create(
            name="Second Live broadcaster",
            building=self.building,
            stream_mode=Broadcaster.StreamMode.ESUP_RUNNER,
            runner_manager=self.manager,
            source_id="source-B",
            url="",
        )
        second.full_clean(exclude=["piloting_implementation"])
        self.assertIsNone(second.url)
        with self.assertRaises(ProtectedError):
            self.manager.delete()

    def test_live_requires_explicit_manager_and_source_without_using_slug(self):
        """Require explicit Live configuration independently of the Pod slug."""
        self.broadcaster.runner_manager = None
        self.broadcaster.source_id = ""
        with self.assertRaises(ValidationError) as error:
            self.broadcaster.full_clean(exclude=["piloting_implementation"])
        self.assertIn("runner_manager", error.exception.message_dict)
        self.assertIn("source_id", error.exception.message_dict)

    def test_static_requires_url_and_preserves_uniqueness(self):
        """Require a unique stream URL for fixed URL playback."""
        self.broadcaster.stream_mode = Broadcaster.StreamMode.STATIC
        with self.assertRaises(ValidationError) as error:
            self.broadcaster.full_clean(exclude=["piloting_implementation"])
        self.assertIn("url", error.exception.message_dict)
        self.broadcaster.url = "https://fixed.example.com/live.m3u8"
        self.broadcaster.full_clean(exclude=["piloting_implementation"])
        self.broadcaster.save()
        duplicate = Broadcaster(
            name="Duplicate", building=self.building, url=self.broadcaster.url
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean(exclude=["piloting_implementation"])

    def test_source_identifier_validation_and_manager_site(self):
        """Reject invalid source identifiers and managers from unrelated sites."""
        for source in ("has/slash", "_starts_with_underscore", "x" * 101):
            with self.subTest(source=source):
                self.broadcaster.source_id = source
                with self.assertRaises(ValidationError):
                    self.broadcaster.full_clean(exclude=["piloting_implementation"])
        self.broadcaster.source_id = "source-A"
        self.manager.site = Site.objects.create(
            domain="other.example.com", name="Other"
        )
        self.manager.save()
        with self.assertRaises(ValidationError) as error:
            self.broadcaster.full_clean(exclude=["piloting_implementation"])
        self.assertIn("runner_manager", error.exception.message_dict)

    def form_data(self, **overrides):
        """Build valid Live admin form data with optional field overrides."""
        return dict(
            name="New broadcaster",
            building=self.building.pk,
            main_lang="en",
            stream_mode=Broadcaster.StreamMode.ESUP_RUNNER,
            runner_manager=self.manager.pk,
            source_id="source-B",
            **overrides,
        )

    def test_admin_form_accepts_live_without_url_and_exposes_configuration(self):
        """Expose Live configuration in the admin and accept an empty fixed URL."""
        form = BroadcasterAdminForm(self.form_data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.fields["url"].required)
        self.assertTrue(form.fields["runner_manager"].required)
        self.assertTrue(form.fields["source_id"].required)
        for field in ("stream_mode", "runner_manager", "source_id"):
            self.assertIn(field, BroadcasterAdmin.list_display)

    def test_form_switch_to_static_requires_url(self):
        """Require a fixed URL when the form switches away from Live mode."""
        data = self.form_data()
        data["stream_mode"] = Broadcaster.StreamMode.STATIC
        form = BroadcasterAdminForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("url", form.errors)

    def test_admin_manager_autocomplete_searches_without_exposing_token(self):
        """Search Live-capable managers without disclosing their bearer token."""
        RunnerManager.objects.create(
            name="Live manager without support",
            url="https://tasks.example.com/",
            token="task-token",
            site=self.site,
        )
        user = User.objects.create_superuser(
            username="live-config-admin", email="admin@example.com"
        )
        self.client.force_login(user)
        for term in (self.manager.name, self.site.domain):
            with self.subTest(term=term):
                result = self.client.get(
                    reverse("admin:autocomplete"),
                    {
                        "app_label": "live",
                        "model_name": "broadcaster",
                        "field_name": "runner_manager",
                        "term": term,
                    },
                )
                self.assertEqual(result.status_code, 200)
                self.assertEqual(
                    [item["id"] for item in result.json()["results"]],
                    [str(self.manager.pk)],
                )
                self.assertNotContains(result, self.manager.token)

    def test_rest_creation_and_partial_status_validate_effective_configuration(self):
        """Validate Live creation and preserve configuration on status updates."""
        data = {
            "name": "REST Live",
            "building": reverse("building-detail", args=[self.building.pk]),
            "stream_mode": "esup_runner",
            "runner_manager": self.manager.pk,
            "source_id": "source-B",
        }
        serializer = BroadcasterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        broadcaster = serializer.save()
        self.assertIsNone(broadcaster.url)
        serializer = BroadcasterSerializer(
            broadcaster, data={"status": True}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer = BroadcasterSerializer(
            broadcaster, data={"stream_mode": "static"}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("broadcaster_url", serializer.errors)


class RunnerLivePlaybackTests(RunnerLiveDatabaseTestCase):
    """Exercise real page access and REST callbacks with a mocked manager."""

    def setUp(self):
        """Create a current public event and mock its manager playback responses."""
        super().setUp()
        self.owner = User.objects.create_user(username="live-owner")
        self.admin = User.objects.create_superuser(
            username="live-admin", email="admin@example.com"
        )
        self.event = Event.objects.create(
            title="Live event",
            owner=self.owner,
            broadcaster=self.broadcaster,
            type=Type.objects.create(title="Live type"),
            is_draft=False,
            start_date=timezone.now() - timezone.timedelta(minutes=5),
            end_date=timezone.now() + timezone.timedelta(minutes=20),
        )
        self.direct_url = self.broadcaster.get_absolute_url()
        self.event_url = self.event.get_absolute_url()
        self.get_patch = patch("pod.live.runner_live.requests.get")
        self.get = self.get_patch.start()
        self.addCleanup(self.get_patch.stop)
        self.get.return_value = response({"live": None})

    def test_status_only_patch_does_not_claim_hls_is_ready_or_overwrite_configuration(
        self,
    ):
        """Keep status callbacks independent of HLS readiness and configuration."""
        client = APIClient()
        client.force_authenticate(user=self.admin)
        url = reverse("broadcaster-detail", args=[self.broadcaster.slug])
        result = client.patch(url, {"status": True}, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.data["broadcaster_url"])
        self.assertNotIn("private-token", str(result.data))
        self.broadcaster.refresh_from_db()
        self.assertTrue(self.broadcaster.status)
        self.assertEqual(self.broadcaster.source_id, "source-A")
        self.assertEqual(self.broadcaster.runner_manager, self.manager)
        cache.clear()
        self.get.side_effect = [response({"live": session()}), response(session())]
        self.client.force_login(self.admin)
        playback = self.client.get(self.direct_url, {"stream": "1"})
        self.assertEqual(playback.json()["hls_url"], HLS_URL)

    def test_direct_poll_requires_login_permission_and_building_site(self):
        """Apply login, live permissions and building site checks to polling."""
        result = self.client.get(self.direct_url, {"stream": "1"})
        self.assertEqual(result.status_code, 302)
        self.client.force_login(self.owner)
        self.assertEqual(
            self.client.get(self.direct_url, {"stream": "1"}).status_code, 403
        )
        self.client.force_login(self.admin)
        other = Site.objects.create(domain="other.example.com", name="Other")
        self.building.sites.set([other])
        self.assertEqual(
            self.client.get(self.direct_url, {"stream": "1"}).status_code, 404
        )
        self.get.assert_not_called()

    def test_public_event_poll_is_uncached_and_whitelists_response(self):
        """Return uncached public playback data without private manager fields."""
        self.get.side_effect = [
            response({"live": session()}),
            response(dict(session(), token="private-token")),
        ]
        result = self.client.get(self.event_url, {"stream": "1"})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["hls_url"], HLS_URL)
        self.assertIn("no-store", result["Cache-Control"])
        self.assertNotContains(result, "private-token")

    def test_secure_pages_log_http_hls_after_access_checks_without_changing_contract(
        self,
    ):
        """Diagnose mixed content for direct, event and iframe playback polling."""
        self.client.force_login(self.admin)
        insecure_url = "http://media.example.com/live/master.m3u8?secret=signature"
        for path in (
            self.direct_url,
            self.event_url,
            self.event_url + "?is_iframe=true",
        ):
            with self.subTest(path=path):
                cache.clear()
                self.get.side_effect = [
                    response({"live": session()}),
                    response(session(url=insecure_url)),
                ]
                with self.assertLogs("pod.live", level="WARNING") as logs:
                    result = self.client.get(path, {"stream": "1"}, secure=True)
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.json()["hls_url"], insecure_url)
                self.assertEqual(
                    set(result.json()), {"live_id", "state", "hls_ready", "hls_url"}
                )
                self.assertIn("reason=mixed_content", logs.output[0])
                self.assertNotIn("secret=signature", str(logs.output))

    def test_event_poll_respects_login_draft_and_group_restrictions(self):
        """Enforce event authentication and draft visibility before polling."""
        self.event.is_restricted = True
        self.event.save()
        self.assertEqual(
            self.client.get(self.event_url, {"stream": "1"}).status_code, 302
        )
        self.event.is_restricted = False
        self.event.is_draft = True
        self.event.save()
        self.assertEqual(
            self.client.get(self.event_url, {"stream": "1"}).status_code, 403
        )
        self.get.assert_not_called()

    def test_event_poll_respects_access_groups(self):
        """Require membership in the event access groups to poll playback."""
        group = AccessGroup.objects.create(code_name="live-viewers")
        self.event.restrict_access_to_groups.add(group)
        self.client.force_login(self.owner)
        # An unrelated authenticated viewer must still belong to the access group.
        viewer = User.objects.create_user(username="live-viewer")
        self.client.force_login(viewer)
        self.assertEqual(
            self.client.get(self.event_url, {"stream": "1"}).status_code, 403
        )
        self.get.assert_not_called()
        viewer.owner.accessgroup_set.add(group)
        self.assertEqual(
            self.client.get(self.event_url, {"stream": "1"}).status_code, 200
        )

    def test_password_grant_allows_polling_and_password_change_revokes_it(self):
        """Grant polling with a valid password and revoke access when it changes."""
        self.event.password = "event-password"
        self.event.save()
        self.assertEqual(
            self.client.get(self.event_url, {"stream": "1"}).status_code, 403
        )
        page = self.client.post(self.event_url, {"password": "event-password"})
        self.assertEqual(page.status_code, 200)
        self.assertEqual(
            self.client.get(self.event_url, {"stream": "1"}).status_code, 200
        )
        self.event.password = "new-password"
        self.event.save()
        self.assertEqual(
            self.client.get(self.event_url, {"stream": "1"}).status_code, 403
        )

    def test_past_and_future_events_do_not_disclose_current_broadcaster_url(self):
        """Hide current broadcaster playback outside the scheduled event period."""
        for start, end in ((-30, -5), (5, 30)):
            self.event.start_date = timezone.now() + timezone.timedelta(minutes=start)
            self.event.end_date = timezone.now() + timezone.timedelta(minutes=end)
            self.event.save()
            result = self.client.get(self.event_url, {"stream": "1"})
            self.assertIsNone(result.json()["hls_url"])
        self.get.assert_not_called()

    def test_live_pages_include_polling_and_never_embed_obsolete_url_or_token(self):
        """Render polling on Live pages without embedding old URLs or credentials."""
        self.broadcaster.url = "https://obsolete.example.com/stream.m3u8"
        self.broadcaster.save()
        self.client.force_login(self.admin)
        for path in (
            self.direct_url,
            self.event_url,
            self.event_url + "?is_iframe=true",
        ):
            with self.subTest(path=path):
                page = self.client.get(path)
                self.assertContains(page, "js/runner_live.js")
                self.assertContains(page, 'id="runner-live-status"')
                self.assertContains(page, "data-mixed-content-message=")
                self.assertContains(page, "data-ended-message=")
                self.assertNotContains(page, "https://obsolete.example.com/stream.m3u8")
                self.assertNotContains(page, "private-token")
                self.assertNotContains(page, "videojs.Hls.xhr.beforeRequest")
        self.get.assert_not_called()

    def test_private_event_poll_keeps_private_path_and_access_checks(self):
        """Preserve the private event path and its access checks during polling."""
        self.event.is_draft = True
        self.event.save()
        private_url = reverse(
            "live:event_private",
            args=[self.event.slug, self.event.get_hashkey()],
        )
        self.assertEqual(
            self.client.get(self.event_url, {"stream": "1"}).status_code, 403
        )
        page = self.client.get(private_url)
        self.assertContains(page, f'data-stream-url="{private_url}?stream=1"')
        result = self.client.get(private_url, {"stream": "1"})
        self.assertEqual(result.status_code, 200)

    def test_password_page_does_not_load_live_player_before_access_is_granted(self):
        """Keep protected pages free of player initialization before password entry."""
        self.event.password = "event-password"
        self.event.save()
        for path in (self.event_url, self.event_url + "?is_iframe=true"):
            with self.subTest(path=path):
                page = self.client.get(path)
                self.assertEqual(page.status_code, 200)
                self.assertNotContains(page, "PodRunnerLive.start")
                self.assertNotContains(page, 'id="runner-live-status"')
                self.assertNotContains(page, 'videojs("podvideoplayer"')
        self.get.assert_not_called()

    def test_fixed_url_pages_and_rest_preserve_playback_without_live_polling(self):
        """Preserve fixed URL pages and REST playback without automatic polling."""
        fixed_url = "https://fixed.example.com/live/master.m3u8"
        self.broadcaster.stream_mode = Broadcaster.StreamMode.STATIC
        self.broadcaster.url = fixed_url
        self.broadcaster.save()
        self.client.force_login(self.admin)
        for path in (
            self.direct_url,
            self.event_url,
            self.event_url + "?is_iframe=true",
        ):
            with self.subTest(path=path):
                page = self.client.get(path)
                self.assertContains(page, f'<source src="{fixed_url}"')
                self.assertNotContains(page, "js/runner_live.js")
                self.assertNotContains(page, 'id="runner-live-status"')
        client = APIClient()
        client.force_authenticate(user=self.admin)
        result = client.get(reverse("broadcaster-detail", args=[self.broadcaster.slug]))
        self.assertEqual(result.data["broadcaster_url"], fixed_url)
        self.get.assert_not_called()


class RunnerLiveMigrationTests(TransactionTestCase):
    """Check that incremental Live migrations preserve existing broadcasters."""

    def test_existing_broadcaster_keeps_its_url_and_defaults_to_static(self):
        """Preserve legacy broadcaster URLs and select static mode during migration."""
        old_target = [
            ("live", "0002_initial"),
            ("video_encode_transcript", "0014_runnermanager_admin_url"),
        ]
        executor = MigrationExecutor(connection)
        if old_target[0] not in executor.loader.graph.nodes:
            self.skipTest(
                "Upgrade regression requires the existing deployment migration history."
            )
        new_target = executor.loader.graph.leaf_nodes()
        executor.migrate(old_target)
        try:
            old_apps = executor.loader.project_state(old_target).apps
            site = old_apps.get_model("sites", "Site").objects.create(
                domain="legacy.example.com", name="Legacy site"
            )
            manager = old_apps.get_model(
                "video_encode_transcript", "RunnerManager"
            ).objects.create(
                name="Legacy manager",
                url="https://legacy-manager.example.com/",
                token="legacy-token",
                site=site,
            )
            building = old_apps.get_model("live", "Building").objects.create(
                name="Legacy building"
            )
            old = old_apps.get_model("live", "Broadcaster").objects.create(
                name="Legacy broadcaster",
                building=building,
                url="https://legacy.example.com/live.m3u8",
            )
            executor = MigrationExecutor(connection)
            executor.migrate(new_target)
            migrated = (
                executor.loader.project_state(new_target)
                .apps.get_model("live", "Broadcaster")
                .objects.get(pk=old.pk)
            )
            self.assertEqual(migrated.url, "https://legacy.example.com/live.m3u8")
            self.assertEqual(migrated.stream_mode, "static")
            self.assertEqual(migrated.source_id, "")
            self.assertIsNone(migrated.runner_manager_id)
            migrated_manager = (
                executor.loader.project_state(new_target)
                .apps.get_model("video_encode_transcript", "RunnerManager")
                .objects.get(pk=manager.pk)
            )
            self.assertFalse(migrated_manager.supports_live)
        finally:
            MigrationExecutor(connection).migrate(new_target)
