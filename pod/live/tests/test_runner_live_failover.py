"""Esup-Pod regression tests for primary priority, RTMP absence and Live failover."""

from copy import copy
from unittest.mock import patch

import requests
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from pod.live.admin import BroadcasterAdmin
from pod.live.forms import BroadcasterAdminForm
from pod.live.models import Broadcaster, Event
from pod.live.rest_views import BroadcasterSerializer
from pod.live.runner_live import _stream_key, get_stream_info
from pod.live.tests.test_runner_live import (
    HLS_URL,
    RunnerLiveDatabaseTestCase,
    response,
    session,
)
from pod.video_encode_transcript.models import RunnerManager
from pod.video.models import Type

SECONDARY_HLS = "https://secondary-media.example.com/live/master.m3u8"
SHARED_REDIS_CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis.example.invalid:6379/3",
    }
}


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    ESUP_RUNNER_LIVE_CACHE_TIMEOUT=0,
    ESUP_RUNNER_LIVE_READY_CACHE_TIMEOUT=0,
)
class RunnerLiveFailoverTests(SimpleTestCase):
    """Exercise real resolver decisions with a shared, deterministic clock/cache."""

    def setUp(self):
        """Prepare two independent managers serving the same source identifier."""
        self.clock = self.enterContext(patch("pod.live.runner_live.time.time"))
        self.clock.return_value = 1000
        cache.clear()
        self.primary = RunnerManager(
            pk=12,
            url="https://primary.example.com",
            token="primary-secret",
            supports_live=True,
        )
        self.secondary = RunnerManager(
            pk=13,
            url="https://secondary.example.com",
            token="secondary-secret",
            supports_live=True,
        )
        self.broadcaster = Broadcaster(
            pk=3,
            stream_mode=Broadcaster.StreamMode.ESUP_RUNNER,
            runner_manager=self.primary,
            secondary_runner_manager=self.secondary,
            source_id="source-A",
        )
        self.primary_error = requests.Timeout("private primary details")
        self.session_error = None
        self.primary_session = session()
        self.secondary_session = session(url=SECONDARY_HLS)
        self.primary_source_ready = True
        self.secondary_source_ready = True
        self.secondary_error = None
        self.health = response({}, status=200)
        self.get = self.enterContext(
            patch("pod.live.runner_live.requests.get", side_effect=self.http)
        )
        self.probe = self.enterContext(
            patch("pod.live.runner_live.probe_hls", return_value="unavailable")
        )

    def http(self, url, **kwargs):
        """Route mocked HTTP by manager and discovery step, including health."""
        if url.endswith(("/api/health", "/manager/health")):
            if isinstance(self.health, Exception):
                raise self.health
            return self.health
        primary = url.startswith(self.primary.url)
        error = self.primary_error if primary else self.secondary_error
        if isinstance(error, Exception):
            raise error
        if error is not None:
            return error
        payload = self.primary_session if primary else self.secondary_session
        if "/sources/" in url:
            return response(
                {
                    "live": payload,
                    "source_ready": (
                        self.primary_source_ready
                        if primary
                        else self.secondary_source_ready
                    ),
                }
            )
        if primary and self.session_error is not None:
            raise self.session_error
        return response(payload)

    def resolve(self, elapsed=0, broadcaster=None):
        """Observe a fresh discovery at a precise offset from the first failure."""
        self.clock.return_value = 1000 + elapsed
        return get_stream_info(broadcaster or self.broadcaster)

    def secondary_calls(self):
        """Inspect calls to the secondary without confusing them with HLS probes."""
        return [
            c for c in self.get.call_args_list if c.args[0].startswith(self.secondary.url)
        ]

    def test_only_contacts_secondary_after_thirty_seconds_of_real_failures(self):
        """The threshold is elapsed downtime, independent of viewer/request count."""
        self.resolve()
        for _ in range(10):
            self.resolve(29)
        self.assertEqual(self.secondary_calls(), [])
        result = self.resolve(30)
        self.assertEqual(result["hls_url"], SECONDARY_HLS)
        self.assertTrue(result["retryable"])
        self.assertEqual(len(self.secondary_calls()), 2)
        for call in self.secondary_calls():
            self.assertEqual(
                call.kwargs["headers"]["Authorization"], "Bearer secondary-secret"
            )
        self.assertTrue(self.secondary_calls()[0].args[0].endswith("/sources/source-A"))
        self.assertNotIn("secret", str(result))

    def test_published_primary_starts_without_consulting_secondary(self):
        """A primary publication retains priority before any secondary is selected."""
        self.primary_error = None
        for state in (
            None,
            "pending",
            "waiting_source",
            "starting",
            "running",
            "stopping",
            "completed",
            "failed",
        ):
            with self.subTest(state=state):
                cache.clear()
                self.primary_session = (
                    None if state is None else session(state=state, ready=False)
                )
                for elapsed in (0, 30, 40):
                    result = self.resolve(elapsed)
                    self.assertIsNone(result["hls_url"])
                self.assertEqual(self.secondary_calls(), [])

    def test_recovery_keeps_secondary_until_primary_hls_is_ready(self):
        """A recovering primary must provide playable HLS before replacing secondary."""
        for payload in (
            None,
            session(),
            session(state="starting", ready=False),
            session(state="completed"),
        ):
            with self.subTest(payload=payload):
                cache.clear()
                self.primary_error = requests.Timeout()
                self.resolve()
                self.assertEqual(self.resolve(30)["hls_url"], SECONDARY_HLS)
                self.get.reset_mock()
                self.primary_error = None
                self.primary_session = payload
                result = self.resolve(40)
                ready = bool(payload and payload["state"] == "running")
                expected = HLS_URL if ready else SECONDARY_HLS
                self.assertEqual(result["hls_url"], expected)
                if ready:
                    self.assertNotIn("retryable", result)
                    self.assertEqual(self.secondary_calls(), [])
                else:
                    self.assertTrue(result["retryable"])
                    self.primary_session = session()
                    self.get.reset_mock()
                    self.assertEqual(self.resolve(41)["hls_url"], HLS_URL)
                    self.assertEqual(self.secondary_calls(), [])

    def test_absent_primary_publication_selects_secondary_without_grace_period(self):
        """A healthy primary without RTMP can use the secondary immediately."""
        self.primary_error = None
        self.primary_source_ready = False
        for payload in (None, session(state="completed"), session()):
            with self.subTest(payload=payload):
                cache.clear()
                self.primary_session = payload
                self.assertEqual(self.resolve()["hls_url"], SECONDARY_HLS)
        self.assertTrue(
            all(
                c.args[0].endswith(("/sources/source-A", "/live/session-1"))
                for c in self.secondary_calls()
            )
        )

    def test_primary_ready_hls_wins_when_both_managers_are_publishing(self):
        """Simultaneous publications never replace ready primary HLS with secondary."""
        self.primary_error = None
        self.assertEqual(self.resolve()["hls_url"], HLS_URL)
        self.assertEqual(self.secondary_calls(), [])

    def test_absence_without_publication_metrics_also_uses_secondary(self):
        """Managers without source readiness still expose an explicit absent session."""
        self.primary_error = None
        self.primary_source_ready = None
        self.primary_session = None
        self.assertEqual(self.resolve()["hls_url"], SECONDARY_HLS)

    def test_absent_primary_publication_does_not_refresh_its_historical_session(self):
        """An old session's broken endpoint cannot hide confirmed RTMP absence."""
        self.primary_error = None
        self.primary_source_ready = False
        self.session_error = requests.Timeout()
        self.assertEqual(self.resolve()["hls_url"], SECONDARY_HLS)
        primary_calls = [
            c for c in self.get.call_args_list if c.args[0].startswith(self.primary.url)
        ]
        self.assertEqual(len(primary_calls), 1)

    def test_secondary_without_rtmp_does_not_offer_a_stale_ready_session(self):
        """A stopped secondary publication cannot advertise its old HLS URL."""
        self.primary_error = None
        self.primary_source_ready = False
        self.secondary_source_ready = False
        self.assertIsNone(self.resolve()["hls_url"])

    def test_primary_outage_does_not_interrupt_already_selected_secondary(self):
        """Keep secondary playback if the primary goes down during its recovery."""
        self.primary_error = None
        self.primary_source_ready = False
        self.assertEqual(self.resolve()["hls_url"], SECONDARY_HLS)
        self.primary_error = requests.Timeout()
        self.assertEqual(self.resolve(1)["hls_url"], SECONDARY_HLS)

    def test_recovery_restarts_the_full_grace_period(self):
        """Distinct transient outages cannot accumulate into a failover."""
        self.resolve()
        self.resolve(20)
        self.primary_error = None
        self.primary_session = None
        self.resolve(21)
        self.primary_error = requests.Timeout()
        self.resolve(29)
        self.resolve(58)
        self.assertEqual(self.secondary_calls(), [])
        self.assertEqual(self.resolve(59)["hls_url"], SECONDARY_HLS)

    def test_configuration_and_contract_errors_never_trigger_failover(self):
        """A responding but misconfigured manager is not considered down."""
        failures = [response({}, status=s) for s in (302, 401, 403, 404, 429)]
        failures += [
            response([]),
            response({}),
            requests.exceptions.SSLError(),
            requests.RequestException(),
        ]
        for failure in failures:
            with self.subTest(failure=failure):
                cache.clear()
                self.primary_error = failure
                self.resolve()
                self.resolve(30)
                self.assertEqual(self.secondary_calls(), [])

    def test_responding_health_prevents_failover_on_live_endpoint_errors(self):
        """A failing Live endpoint does not prove that the manager has crashed."""
        for status in (500, 502, 503, 504):
            with self.subTest(status=status):
                cache.clear()
                self.primary_error = response({}, status=status)
                self.resolve()
                self.resolve(30)
                self.assertEqual(self.secondary_calls(), [])

    def test_mediamtx_outage_allows_failover_despite_healthy_manager_api(self):
        """A stopped MediaMTX is a Live outage even when generic health returns 200."""
        self.primary_error = response(
            {"detail": "MediaMTX control unavailable"}, status=503
        )
        self.assertTrue(self.resolve()["retryable"])
        self.resolve(29)
        self.assertEqual(self.secondary_calls(), [])
        self.assertEqual(self.resolve(30)["hls_url"], SECONDARY_HLS)
        self.assertFalse(
            any(c.args[0].endswith("/health") for c in self.get.call_args_list)
        )
        self.primary_error = None
        self.primary_session = None
        self.get.reset_mock()
        result = self.resolve(40)
        self.assertEqual(result["hls_url"], SECONDARY_HLS)
        self.primary_session = session()
        self.get.reset_mock()
        self.assertEqual(self.resolve(50)["hls_url"], HLS_URL)
        self.assertEqual(self.secondary_calls(), [])

    def test_unrecognized_503_bodies_do_not_bypass_manager_health(self):
        """Only Runner's known MediaMTX diagnostic confirms the dependency outage."""
        failures = [
            response({"detail": "MediaMTX control unavailable"}, status=403),
            response({"detail": "private primary details"}, status=503),
            response({"detail": {"error": "MediaMTX control unavailable"}}, status=503),
            response(["MediaMTX control unavailable"], status=503),
            response("MediaMTX control unavailable", status=503),
        ]
        failures.append(response({}, status=503))
        failures[-1].json.side_effect = ValueError("private primary details")
        for failure in failures:
            with self.subTest(failure=failure):
                cache.clear()
                self.primary_error = failure
                with self.assertLogs("pod.live", level="WARNING") as logs:
                    self.resolve()
                    self.resolve(30)
                self.assertEqual(self.secondary_calls(), [])
                self.assertNotIn("private primary details", str(logs.output))

    def test_mediamtx_failure_preserves_primary_hls_before_secondary_is_ready(self):
        """Keep active HLS through the grace period and a media-control-only outage."""
        self.primary_error = None
        self.resolve()
        self.primary_error = response(
            {"detail": "MediaMTX control unavailable"}, status=503
        )
        self.probe.return_value = "active"
        self.assertEqual(self.resolve(1)["hls_url"], HLS_URL)
        self.assertEqual(self.resolve(31)["hls_url"], SECONDARY_HLS)

    def test_session_timeout_with_working_health_does_not_trigger_failover(self):
        """Source lookup succeeded; confirm manager health after a session timeout."""
        self.primary_error = None
        self.session_error = requests.Timeout()
        self.resolve()
        self.resolve(30)
        self.assertEqual(self.secondary_calls(), [])

    def test_secondary_continues_while_primary_session_refresh_fails(self):
        """A healthy manager alone is insufficient to replace secondary playback."""
        self.resolve()
        self.resolve(30)
        self.primary_error = None
        self.session_error = requests.Timeout()
        self.get.reset_mock()
        result = self.resolve(40)
        self.assertEqual(result["hls_url"], SECONDARY_HLS)
        self.assertTrue(result["retryable"])
        self.assertEqual(len(self.secondary_calls()), 2)

    def test_persistently_unhealthy_manager_allows_failover(self):
        """Both failed discovery and failed health establish an outage."""
        for health in (response({}, status=503), requests.ConnectionError()):
            with self.subTest(health=health):
                cache.clear()
                self.primary_error = response({}, status=503)
                self.health = health
                self.resolve()
                self.assertEqual(self.resolve(30)["hls_url"], SECONDARY_HLS)

    def test_legacy_health_endpoint_is_checked_without_following_redirects(self):
        """Older managers remain healthy when only the legacy endpoint exists."""
        original = self.http

        def legacy(url, **kwargs):
            """Simulate a manager exposing only its legacy health endpoint."""
            if url.endswith("/api/health"):
                return response({}, status=404)
            return original(url, **kwargs)

        self.get.side_effect = legacy
        self.primary_error = response({}, status=503)
        self.resolve()
        self.resolve(30)
        self.assertEqual(self.secondary_calls(), [])
        health_calls = [
            c for c in self.get.call_args_list if c.args[0].endswith("/health")
        ]
        self.assertEqual(len(health_calls), 4)
        for call in health_calls:
            self.assertFalse(call.kwargs["allow_redirects"])
            self.assertEqual(call.kwargs["timeout"], (2, 4))

    def test_absent_or_disabled_secondary_never_gets_contacted(self):
        """Only the explicitly configured, usable secondary may serve as backup."""
        for change in ("absent", "inactive", "unsupported", "no_token"):
            with self.subTest(change=change):
                cache.clear()
                if change == "absent":
                    self.broadcaster.secondary_runner_manager = None
                else:
                    self.broadcaster.secondary_runner_manager = self.secondary
                    self.secondary.is_active = change != "inactive"
                    self.secondary.supports_live = change != "unsupported"
                    self.secondary.token = (
                        "" if change == "no_token" else "secondary-secret"
                    )
                self.resolve()
                self.resolve(30)
                self.assertEqual(self.secondary_calls(), [])

    def test_inactive_primary_uses_secondary_immediately(self):
        """Use only the active secondary without waiting for a primary outage."""
        self.primary.is_active = False
        self.primary_error = None
        self.assertEqual(self.resolve()["hls_url"], SECONDARY_HLS)
        self.assertEqual(self.get.call_count, 2)
        self.assertEqual(len(self.secondary_calls()), 2)

    def test_inactive_primary_without_usable_secondary_stays_unavailable(self):
        """An inactive primary never permits an unconfigured or disabled backup."""
        self.primary.is_active = False
        for change in ("absent", "inactive", "unsupported", "no_token", "same"):
            with self.subTest(change=change):
                cache.clear()
                self.secondary.is_active = change != "inactive"
                self.secondary.supports_live = change != "unsupported"
                self.secondary.token = "" if change == "no_token" else "secondary-secret"
                if change == "absent":
                    self.broadcaster.secondary_runner_manager = None
                elif change == "same":
                    self.broadcaster.secondary_runner_manager = self.primary
                else:
                    self.broadcaster.secondary_runner_manager = self.secondary
                self.assertIsNone(self.resolve()["hls_url"])
                self.get.assert_not_called()

    @override_settings(ESUP_RUNNER_LIVE_READY_CACHE_TIMEOUT=20)
    def test_deactivating_cached_primary_switches_to_secondary_immediately(self):
        """A cached primary stream cannot hide administrative deactivation."""
        self.primary_error = None
        self.assertEqual(self.resolve()["hls_url"], HLS_URL)
        self.primary.is_active = False
        self.get.reset_mock()
        self.assertEqual(self.resolve(1)["hls_url"], SECONDARY_HLS)
        self.assertEqual(self.get.call_count, len(self.secondary_calls()))

    def test_inactive_primary_never_preserves_its_hls_when_secondary_is_unavailable(self):
        """A secondary failure must not restore the disabled primary's cached stream."""
        self.primary_error = None
        self.assertEqual(self.resolve()["hls_url"], HLS_URL)
        self.primary.is_active = False
        self.secondary_error = requests.Timeout()
        self.probe.return_value = "active"
        self.assertIsNone(self.resolve(1)["hls_url"])
        self.probe.assert_not_called()

    @override_settings(ESUP_RUNNER_LIVE_CACHE_TIMEOUT=10)
    def test_inactive_primary_preserves_cached_secondary_until_it_is_disabled(self):
        """Reuse valid secondary playback and revoke it if that manager is disabled."""
        self.primary.is_active = False
        self.assertEqual(self.resolve()["hls_url"], SECONDARY_HLS)
        calls = self.get.call_count
        self.assertEqual(self.resolve(1)["hls_url"], SECONDARY_HLS)
        self.assertEqual(self.get.call_count, calls)
        self.secondary.is_active = False
        self.assertIsNone(self.resolve(2)["hls_url"])
        self.assertEqual(self.get.call_count, calls)

    def test_inactive_primary_preserves_secondary_hls_during_secondary_outage(self):
        """Keep independently active secondary HLS without using the disabled primary."""
        self.primary.is_active = False
        self.assertEqual(self.resolve()["hls_url"], SECONDARY_HLS)
        self.secondary_error = requests.Timeout()
        self.probe.return_value = "active"
        self.assertEqual(self.resolve(1)["hls_url"], SECONDARY_HLS)
        self.assertEqual(self.get.call_count, len(self.secondary_calls()))
        self.probe.assert_called_once()

    @override_settings(ESUP_RUNNER_LIVE_CACHE_TIMEOUT=10)
    def test_reactivated_primary_recovers_priority_after_secondary_cache_expires(self):
        """A reactivated primary takes playback back when its HLS is ready."""
        self.primary.is_active = False
        self.assertEqual(self.resolve()["hls_url"], SECONDARY_HLS)
        self.primary.is_active = True
        self.primary_error = None
        self.get.reset_mock()
        self.assertEqual(self.resolve(11)["hls_url"], HLS_URL)
        self.assertEqual(self.secondary_calls(), [])

    def test_secondary_stop_does_not_reuse_its_old_hls(self):
        """Stop confirmed secondary sessions even while the primary stays down."""
        self.resolve()
        self.assertEqual(self.resolve(30)["hls_url"], SECONDARY_HLS)
        self.secondary_session = session(state="completed", ready=False)
        result = self.resolve(40)
        self.assertEqual(result["state"], "completed")
        self.assertIsNone(result["hls_url"])
        self.secondary_error = requests.Timeout()
        self.resolve(50)
        self.probe.assert_not_called()

    def test_secondary_failure_preserves_confirmed_primary_hls(self):
        """Retain independently active HLS when neither manager can discover media."""
        self.primary_error = None
        self.resolve()
        self.primary_error = requests.Timeout()
        self.secondary_error = requests.Timeout()
        self.probe.return_value = "active"
        self.assertEqual(self.resolve(1)["hls_url"], HLS_URL)
        self.assertEqual(self.resolve(31)["hls_url"], HLS_URL)

    def test_primary_hls_continuity_does_not_prevent_delayed_failover(self):
        """Primary media readiness cannot hide the underlying manager outage."""
        self.primary_error = None
        self.resolve()
        self.primary_error = requests.Timeout()
        self.probe.return_value = "active"
        self.assertEqual(self.resolve(1)["hls_url"], HLS_URL)
        self.assertEqual(self.resolve(31)["hls_url"], SECONDARY_HLS)

    def test_each_manager_uses_its_own_last_confirmed_hls(self):
        """A later secondary outage may only reuse that manager's confirmed URL."""
        self.resolve()
        self.resolve(30)
        self.secondary_error = requests.Timeout()
        self.probe.return_value = "active"
        self.assertEqual(self.resolve(40)["hls_url"], SECONDARY_HLS)
        self.assertEqual(self.probe.call_args.args[0], SECONDARY_HLS)

    def test_configuration_edits_and_different_secondaries_isolate_outage_history(self):
        """Do not share failover decisions across different manager pairs/tokens."""
        self.resolve()
        other = copy(self.broadcaster)
        other.secondary_runner_manager = RunnerManager(
            pk=14,
            url="https://other.example.com",
            token="other-token",
            supports_live=True,
        )
        self.resolve(30, other)
        self.assertEqual(self.secondary_calls(), [])
        self.primary.token = "rotated-primary"
        self.resolve(30)
        self.assertEqual(self.secondary_calls(), [])
        self.secondary.token = "rotated-secondary"
        self.resolve(60)
        self.assertEqual(self.secondary_calls(), [])

    def test_long_idle_period_requires_a_fresh_outage(self):
        """An old failure is insufficient evidence after playback polling stops."""
        self.resolve()
        self.resolve(120)
        self.assertEqual(self.secondary_calls(), [])
        self.assertEqual(self.resolve(150)["hls_url"], SECONDARY_HLS)

    @override_settings(ESUP_RUNNER_LIVE_CACHE_TIMEOUT=10)
    def test_cached_failures_and_concurrent_refreshes_do_not_count_as_observations(self):
        """Only fresh HTTP failures start or advance the shared outage timer."""
        key = _stream_key(self.broadcaster)
        cache.add(f"{key}:refresh-lock", True, timeout=60)
        self.resolve()
        self.resolve(30)
        self.get.assert_not_called()
        cache.delete(f"{key}:refresh-lock")
        self.resolve(30)
        self.resolve(35)
        self.assertEqual(self.get.call_count, 1)
        self.assertEqual(self.secondary_calls(), [])
        self.assertEqual(self.resolve(60)["hls_url"], SECONDARY_HLS)

    @override_settings(ESUP_RUNNER_LIVE_CACHE_TIMEOUT=10)
    def test_disabling_cached_secondary_revokes_its_playback(self):
        """Administrative changes override a cached secondary selection immediately."""
        self.resolve()
        self.resolve(30)
        self.secondary.is_active = False
        result = self.resolve(31)
        self.assertIsNone(result["hls_url"])
        self.assertFalse(result["retryable"])
        self.secondary.is_active = True
        self.assertIsNone(self.resolve(41)["hls_url"])


class RunnerLiveSecondaryConfigurationTests(RunnerLiveDatabaseTestCase):
    """Validate secondary configuration through models, admin and REST."""

    def setUp(self):
        """Add a Live-capable secondary on the same site."""
        super().setUp()
        self.secondary = RunnerManager.objects.create(
            name="Secondary Live manager",
            url="https://secondary.example.com",
            token="secondary-secret",
            supports_live=True,
            site=self.site,
        )

    @override_settings(CACHES=SHARED_REDIS_CACHES)
    def test_optional_secondary_is_accepted_and_protected_from_deletion(self):
        """Existing broadcasters work unchanged and configured backups are protected."""
        self.broadcaster.clean()
        self.broadcaster.secondary_runner_manager = self.secondary
        self.broadcaster.clean()
        self.broadcaster.save()
        with self.assertRaises(ProtectedError):
            self.secondary.delete()

    def test_same_manager_is_rejected_by_model_and_partial_rest_update(self):
        """Enforce distinct managers even on partial configuration changes."""
        self.broadcaster.secondary_runner_manager = self.manager
        with self.assertRaises(ValidationError) as error:
            self.broadcaster.clean()
        self.assertIn("secondary_runner_manager", error.exception.message_dict)
        self.broadcaster.secondary_runner_manager = self.secondary
        serializer = BroadcasterSerializer(
            self.broadcaster, data={"runner_manager": self.secondary.pk}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("secondary_runner_manager", serializer.errors)

    def test_secondary_must_support_live_and_belong_to_a_building_site(self):
        """Apply the same model and REST restrictions to both managers."""
        self.broadcaster.secondary_runner_manager = self.secondary
        self.secondary.supports_live = False
        self.secondary.save()
        with self.assertRaises(ValidationError) as error:
            self.broadcaster.clean()
        self.assertIn("secondary_runner_manager", error.exception.message_dict)
        serializer = BroadcasterSerializer(
            self.broadcaster,
            data={"secondary_runner_manager": self.secondary.pk},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.secondary.supports_live = True
        self.secondary.site = Site.objects.create(
            domain="other.example.com", name="Other"
        )
        self.secondary.save()
        with self.assertRaises(ValidationError) as error:
            self.broadcaster.clean()
        self.assertIn("secondary_runner_manager", error.exception.message_dict)

    @override_settings(CACHES=SHARED_REDIS_CACHES)
    def test_rest_partial_updates_preserve_or_clear_secondary(self):
        """Accept optional backups and preserve them across status callbacks."""
        serializer = BroadcasterSerializer(
            self.broadcaster,
            data={"secondary_runner_manager": self.secondary.pk},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        broadcaster = serializer.save()
        serializer = BroadcasterSerializer(
            broadcaster, data={"status": True}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.save().secondary_runner_manager, self.secondary)
        serializer = BroadcasterSerializer(
            broadcaster, data={"secondary_runner_manager": None}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIsNone(serializer.save().secondary_runner_manager)

    def test_admin_secondary_is_optional_and_live_filtered(self):
        """Present both managers while retaining the optional secondary field."""
        form = BroadcasterAdminForm()
        self.assertFalse(form.fields["secondary_runner_manager"].required)
        self.assertIn(self.secondary, form.fields["secondary_runner_manager"].queryset)
        self.secondary.supports_live = False
        self.secondary.save()
        form = BroadcasterAdminForm()
        self.assertNotIn(self.secondary, form.fields["secondary_runner_manager"].queryset)
        self.assertIn("secondary_runner_manager", BroadcasterAdmin.list_display)

    def test_secondary_autocomplete_filters_live_support_and_keeps_tokens_private(self):
        """The secondary autocomplete follows the same Live restrictions as primary."""
        user = User.objects.create_superuser(username="secondary-admin")
        self.client.force_login(user)
        result = self.client.get(
            reverse("admin:autocomplete"),
            {
                "app_label": "live",
                "model_name": "broadcaster",
                "field_name": "secondary_runner_manager",
                "term": "Secondary",
            },
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(
            [item["id"] for item in result.json()["results"]], [str(self.secondary.pk)]
        )
        self.assertNotContains(result, self.secondary.token)

    @override_settings(
        ESUP_RUNNER_LIVE_CACHE_TIMEOUT=0, ESUP_RUNNER_LIVE_READY_CACHE_TIMEOUT=0
    )
    def test_event_iframe_direct_and_rest_share_failover_and_primary_recovery(self):
        """Expose the same selected stream through every existing playback entry."""
        user = User.objects.create_superuser(username="secondary-viewer")
        self.client.force_login(user)
        api = APIClient()
        api.force_authenticate(user=user)
        self.broadcaster.secondary_runner_manager = self.secondary
        self.broadcaster.save()
        event = Event.objects.create(
            title="Redundant live",
            owner=user,
            broadcaster=self.broadcaster,
            type=Type.objects.create(title="Redundant Live type"),
            is_draft=False,
            start_date=timezone.now() - timezone.timedelta(minutes=5),
            end_date=timezone.now() + timezone.timedelta(minutes=20),
        )
        paths = [
            (event.get_absolute_url(), {"stream": "1"}),
            (event.get_absolute_url(), {"stream": "1", "is_iframe": "true"}),
            (self.broadcaster.get_absolute_url(), {"stream": "1"}),
        ]
        primary_down = True
        primary_ready = False

        def discovery(url, **kwargs):
            """Serve secondary playback while the primary recovers its publication and HLS."""
            if url.startswith(self.manager.url):
                if primary_down:
                    raise requests.ConnectionError()
                if not primary_ready:
                    return response({"source_ready": False, "live": None})
                payload = session()
                return response(
                    {"source_ready": True, "live": payload}
                    if "/sources/" in url
                    else payload
                )
            payload = session(url=SECONDARY_HLS)
            return response({"live": payload} if "/sources/" in url else payload)

        with (
            patch("pod.live.runner_live.time.time", return_value=1000) as clock,
            patch("pod.live.runner_live.requests.get", side_effect=discovery) as get,
        ):
            first = self.client.get(*paths[0])
            self.assertIsNone(first.json()["hls_url"])
            clock.return_value = 1030
            for path, params in paths:
                result = self.client.get(path, params)
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.json()["hls_url"], SECONDARY_HLS)
                self.assertNotContains(result, self.secondary.token)
                self.assertIn("no-store", result["Cache-Control"])
            rest_url = reverse("broadcaster-detail", args=[self.broadcaster.slug])
            self.assertEqual(api.get(rest_url).data["broadcaster_url"], SECONDARY_HLS)
            primary_down = False
            get.reset_mock()
            for path, params in paths:
                result = self.client.get(path, params)
                self.assertEqual(result.json()["hls_url"], SECONDARY_HLS)
            self.assertEqual(api.get(rest_url).data["broadcaster_url"], SECONDARY_HLS)
            primary_ready = True
            get.reset_mock()
            for path, params in paths:
                self.assertEqual(self.client.get(path, params).json()["hls_url"], HLS_URL)
            self.assertEqual(api.get(rest_url).data["broadcaster_url"], HLS_URL)
            self.assertTrue(
                all(c.args[0].startswith(self.manager.url) for c in get.call_args_list)
            )
