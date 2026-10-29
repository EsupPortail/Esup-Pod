"""Esup-Pod tests for HLS playback continuity during Runner manager outages."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from pod.live.hls_probe import MAX_PLAYLIST_BYTES, probe_hls
from pod.live.runner_live import get_stream_info

HLS_URL = "https://media.example.com/live/master.m3u8?signature=private"


def hls_response(data, status=200):
    """Provide streamed HLS data and track that the connection is closed."""
    if isinstance(data, str):
        data = data.encode()
    return Mock(status_code=status, iter_content=Mock(return_value=[data]))


def playlist(sequence=1, ended=False):
    """Build a sliding media playlist with an accessible latest segment."""
    return (
        "#EXTM3U\n#EXT-X-TARGETDURATION:6\n"
        f"#EXT-X-MEDIA-SEQUENCE:{sequence}\n"
        f"#EXTINF:6,\nsegment-{sequence}.ts\n" + ("#EXT-X-ENDLIST\n" if ended else "")
    )


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class HLSProbeTests(SimpleTestCase):
    """Distinguish a progressing live from stale, ended or inaccessible HLS."""

    def setUp(self):
        """Isolate shared observations and control network data and observation time."""
        cache.clear()
        get_patch = patch("pod.live.hls_probe.requests.get")
        clock_patch = patch("pod.live.hls_probe.time.time", return_value=1000)
        self.get = get_patch.start()
        self.clock = clock_patch.start()
        self.addCleanup(get_patch.stop)
        self.addCleanup(clock_patch.stop)

    def observe(self, sequence=1, ended=False):
        """Probe a playlist and its latest segment without waiting in real time."""
        self.get.side_effect = [hls_response(playlist(sequence, ended))]
        if not ended:
            self.get.side_effect = [
                hls_response(playlist(sequence)),
                hls_response(b"media"),
            ]
        return probe_hls(HLS_URL, "probe")

    def test_accessible_playlist_requires_actual_progression(self):
        """A 200 response alone never confirms an active live."""
        self.assertEqual(self.observe(), "checking")
        self.clock.return_value += 10
        self.assertEqual(self.observe(), "checking")
        self.assertEqual(self.observe(2), "active")
        self.clock.return_value += 10
        self.assertEqual(self.observe(2), "active")
        self.clock.return_value += 10
        self.assertEqual(self.observe(2), "active")
        self.clock.return_value += 11
        self.assertEqual(self.observe(2), "stalled")

    def test_progressing_hls_has_no_fixed_outage_cutoff(self):
        """Accessible new segments keep confirming playback beyond 120 seconds."""
        self.assertEqual(self.observe(), "checking")
        for sequence in range(2, 40):
            self.clock.return_value += 10
            self.assertEqual(self.observe(sequence), "active")

    def test_changed_segment_signature_does_not_count_as_new_media(self):
        """Rotating access parameters cannot make a frozen playlist appear active."""
        self.observe()
        self.clock.return_value += 10
        self.get.side_effect = [
            hls_response(playlist().replace("segment-1.ts", "segment-1.ts?token=new")),
            hls_response(b"media"),
        ]
        self.assertEqual(probe_hls(HLS_URL, "probe"), "checking")

    def test_sequence_reset_requires_new_progression(self):
        """A restarted media sequence must advance before it confirms live playback."""
        self.observe(10)
        self.clock.return_value += 10
        self.assertEqual(self.observe(11), "active")
        self.assertEqual(self.observe(1), "checking")
        self.clock.return_value += 10
        self.assertEqual(self.observe(2), "active")

    def test_old_observations_do_not_confirm_an_archive_after_a_long_idle_period(self):
        """A later playlist must prove fresh progression after a long gap between probes."""
        self.observe()
        self.clock.return_value += 3600
        self.assertEqual(self.observe(100), "checking")
        self.clock.return_value += 10
        self.assertEqual(self.observe(100), "checking")
        self.clock.return_value += 10
        self.assertEqual(self.observe(101), "active")

    def test_endlist_confirms_the_end_without_fetching_media(self):
        """An ended playlist is not mistaken for live media because it still exists."""
        self.assertEqual(self.observe(ended=True), "ended")
        self.assertEqual(self.get.call_count, 1)

    def test_master_playlist_and_segment_checks_never_forward_manager_credentials(self):
        """Resolve relative variant/segment URLs and read only initial media bytes."""
        master = hls_response(
            "#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=100000\n720p/index.m3u8?key=signed\n"
        )
        media = hls_response(playlist())
        segment = hls_response(b"media")
        self.get.side_effect = [master, media, segment]
        self.assertEqual(probe_hls(HLS_URL, "probe"), "checking")
        self.assertEqual(
            self.get.call_args_list[1].args[0],
            "https://media.example.com/live/720p/index.m3u8?key=signed",
        )
        self.assertEqual(
            self.get.call_args_list[2].args[0],
            "https://media.example.com/live/720p/segment-1.ts",
        )
        for call in self.get.call_args_list:
            self.assertNotIn("Authorization", call.kwargs["headers"])
            self.assertEqual(call.kwargs["timeout"], (2, 2))
            self.assertFalse(call.kwargs["allow_redirects"])
            self.assertTrue(call.kwargs["stream"])
        self.assertEqual(self.get.call_args.kwargs["headers"]["Range"], "bytes=0-1023")
        for reply in (master, media, segment):
            reply.close.assert_called_once()

    def test_missing_latest_segment_cannot_confirm_progress(self):
        """Playlist changes only count when the latest referenced media is accessible."""
        self.observe()
        self.get.side_effect = [
            hls_response(playlist(2)),
            hls_response(b"error", status=404),
        ]
        self.assertEqual(probe_hls(HLS_URL, "probe"), "unavailable")
        self.assertEqual(self.observe(), "checking")

    def test_invalid_oversized_and_redirected_playlists_are_unavailable(self):
        """Bound parsing and refuse unusable playlist responses."""
        for reply in (
            hls_response("<html>error</html>"),
            hls_response(b"x" * (MAX_PLAYLIST_BYTES + 1)),
            hls_response("redirect", status=302),
            hls_response("#EXTM3U\n#EXT-X-TARGETDURATION:0\nsegment.ts\n"),
        ):
            with self.subTest(reply=reply):
                self.get.side_effect = [reply]
                self.assertEqual(probe_hls(HLS_URL, "probe"), "unavailable")
                reply.close.assert_called_once()

    def test_nested_playlist_requests_are_bounded(self):
        """A cyclic master playlist cannot make the check loop indefinitely."""
        replies = [
            hls_response("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1\nmaster.m3u8\n")
            for _ in range(3)
        ]
        self.get.side_effect = replies
        self.assertEqual(probe_hls(HLS_URL, "probe"), "unavailable")
        self.assertEqual(self.get.call_count, 3)

    def test_segment_read_stops_after_the_first_nonempty_chunk(self):
        """Do not download whole media files when a server ignores Range."""
        segment = hls_response(b"media")

        def chunks():
            yield b"media"
            raise AssertionError("The rest of this segment must not be downloaded")

        segment.iter_content.return_value = chunks()
        self.get.side_effect = [hls_response(playlist()), segment]
        self.assertEqual(probe_hls(HLS_URL, "probe"), "checking")
        segment.close.assert_called_once()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    ESUP_RUNNER_LIVE_CACHE_TIMEOUT=0,
    ESUP_RUNNER_LIVE_READY_CACHE_TIMEOUT=0,
)
class RunnerLiveOutageTests(SimpleTestCase):
    """Exercise complete discovery and HLS fallback, including invalidation."""

    def setUp(self):
        """Use an explicit manager/source and deterministic HTTP responses."""
        cache.clear()
        self.manager = SimpleNamespace(
            pk=12,
            url="https://manager.example.com",
            token="private-token",
            is_active=True,
            supports_live=True,
        )
        self.broadcaster = SimpleNamespace(
            pk=3,
            is_runner_live=True,
            runner_manager_id=12,
            runner_manager=self.manager,
            source_id="source-A",
        )
        get_patch = patch("pod.live.runner_live.requests.get")
        clock_patch = patch("pod.live.hls_probe.time.time", return_value=1000)
        self.get = get_patch.start()
        self.clock = clock_patch.start()
        self.addCleanup(get_patch.stop)
        self.addCleanup(clock_patch.stop)

    def confirm(self, state="running", ready=True):
        """Return the current state as a successful manager discovery."""
        payload = dict(
            live_id="live-1",
            source_id="source-A",
            state=state,
            hls_ready=ready,
            hls_url=HLS_URL,
        )
        self.get.side_effect = [
            Mock(status_code=200, json=Mock(return_value={"live": payload})),
            Mock(status_code=200, json=Mock(return_value=payload)),
        ]
        return get_stream_info(self.broadcaster)

    def outage(self, sequence=1, error=None, ended=False):
        """Make the manager fail while HLS remains independently reachable."""
        self.get.side_effect = [
            error or requests.Timeout("private-token"),
            hls_response(playlist(sequence, ended)),
        ]
        if not ended:
            self.get.side_effect = [
                error or requests.Timeout("private-token"),
                hls_response(playlist(sequence)),
                hls_response(b"media"),
            ]
        return get_stream_info(self.broadcaster)

    def test_outage_reuses_exact_url_only_after_accessible_segments_advance(self):
        """Remember a URL beyond the discovery TTL and confirm its live progression."""
        self.confirm()
        with self.assertLogs("pod.live", level="WARNING") as logs:
            first = self.outage()
        self.assertEqual(first["discovery_status"], "unreachable")
        self.assertTrue(first["retryable"])
        self.assertEqual(first["hls_status"], "checking")
        self.assertIsNone(first["hls_url"])
        self.assertNotIn("private-token", str(logs.output))
        for sequence in range(2, 20):
            self.clock.return_value += 10
            result = self.outage(sequence)
            self.assertEqual(result["state"], "running")
            self.assertEqual(result["hls_url"], HLS_URL)
            self.assertTrue(result["hls_ready"])
            self.assertTrue(result["retryable"])

    def test_responding_but_failing_manager_is_distinct_from_unreachable_manager(self):
        """A 503 means HTTP responded; it still permits HLS-backed continuity."""
        self.confirm()
        error = Mock(status_code=503, json=Mock())
        result = self.outage(error=error)
        self.assertEqual(result["discovery_status"], "error")
        self.assertTrue(result["retryable"])
        self.clock.return_value += 10
        self.assertEqual(self.outage(2, error=error)["hls_url"], HLS_URL)
        error.json.assert_not_called()

    def test_frozen_and_ended_playlists_are_not_offered_to_new_viewers(self):
        """Do not advertise an archive as a live during a manager outage."""
        self.confirm()
        self.outage()
        self.clock.return_value += 10
        self.assertTrue(self.outage(2)["hls_ready"])
        self.clock.return_value += 10
        self.outage(2)
        self.clock.return_value += 11
        result = self.outage(2)
        self.assertEqual(result["hls_status"], "stalled")
        self.assertIsNone(result["hls_url"])
        result = self.outage(2, ended=True)
        self.assertEqual(result["state"], "completed")
        self.get.reset_mock()
        self.get.side_effect = requests.Timeout()
        self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
        self.get.assert_called_once()

    def test_confirmed_absence_and_stop_discard_last_known_url(self):
        """Confirmed lifecycle states cannot later resurrect an old cached URL."""
        for state in ("waiting_source", "starting", "completed", "failed"):
            with self.subTest(state=state):
                cache.clear()
                self.confirm()
                self.confirm(state=state, ready=False)
                self.get.reset_mock()
                self.get.side_effect = requests.Timeout()
                self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
                self.get.assert_called_once()

    def test_access_refusals_and_invalid_payloads_invalidate_fallback(self):
        """Configuration and contract errors are not treated as temporary outages."""
        for reply in (
            Mock(status_code=403),
            Mock(status_code=401),
            Mock(status_code=200, json=Mock(return_value=[])),
        ):
            with self.subTest(reply=reply):
                cache.clear()
                self.confirm()
                self.get.side_effect = [reply]
                result = get_stream_info(self.broadcaster)
                self.assertFalse(result["retryable"])
                self.assertIsNone(result["hls_url"])
                self.get.reset_mock()
                self.get.side_effect = requests.Timeout()
                get_stream_info(self.broadcaster)
                self.get.assert_called_once()

    def test_new_credentials_cannot_reuse_a_previous_configuration_url(self):
        """A changed manager token isolates the previously remembered HLS address."""
        self.confirm()
        self.manager.token = "replacement-token"
        self.get.reset_mock()
        self.get.side_effect = requests.Timeout()
        self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
        self.get.assert_called_once()

    def test_disabling_a_manager_discards_its_remembered_url(self):
        """Re-enabling a manager cannot restore an URL invalidated by disabling it."""
        self.confirm()
        self.manager.is_active = False
        self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
        self.manager.is_active = True
        self.get.reset_mock()
        self.get.side_effect = requests.Timeout()
        self.assertIsNone(get_stream_info(self.broadcaster)["hls_url"])
        self.get.assert_called_once()

    @override_settings(
        ESUP_RUNNER_LIVE_READY_CACHE_TIMEOUT=20, ESUP_RUNNER_LIVE_CACHE_TIMEOUT=10
    )
    def test_positive_negative_and_outage_cache_durations(self):
        """Apply 20 seconds to confirmed playback and 10 seconds to absence/errors."""
        with patch("pod.live.runner_live.cache.set", wraps=cache.set) as save:
            self.confirm()
        self.assertTrue(
            any(call.kwargs.get("timeout") == 20 for call in save.call_args_list)
        )
        self.get.reset_mock()
        get_stream_info(self.broadcaster)
        self.get.assert_not_called()
        cache.clear()
        with patch("pod.live.runner_live.cache.set", wraps=cache.set) as save:
            self.confirm(state="completed", ready=False)
        self.assertTrue(
            any(call.kwargs.get("timeout") == 10 for call in save.call_args_list)
        )
        cache.clear()
        self.get.side_effect = requests.Timeout()
        with patch("pod.live.runner_live.cache.set", wraps=cache.set) as save:
            get_stream_info(self.broadcaster)
        self.assertTrue(
            any(call.kwargs.get("timeout") == 10 for call in save.call_args_list)
        )

    def test_concurrent_discovery_is_shared_without_duplicate_manager_calls(self):
        """A concurrent request waits for the owner of the per-source refresh lock."""
        pending = []
        payload = dict(
            live_id="live-1",
            source_id="source-A",
            state="running",
            hls_ready=True,
            hls_url=HLS_URL,
        )

        def fetch(url, **kwargs):
            if "/sources/" in url:
                pending.append(get_stream_info(self.broadcaster))
                return Mock(status_code=200, json=Mock(return_value={"live": payload}))
            return Mock(status_code=200, json=Mock(return_value=payload))

        self.get.side_effect = fetch
        self.assertEqual(get_stream_info(self.broadcaster)["hls_url"], HLS_URL)
        self.assertEqual(self.get.call_count, 2)
        self.assertEqual(pending[0]["discovery_status"], "refreshing")
        self.assertTrue(pending[0]["retryable"])
