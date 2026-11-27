"""Esup-Pod event playback tests with rendered JavaScript and controlled timing."""

import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest import skipUnless

from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.utils import timezone


@skipUnless(shutil.which("node"), "Node.js is required to exercise event playback")
class EventPlaybackTests(SimpleTestCase):
    """Cover startup, waiting video transitions and recovery without a real stream."""

    def playback(
        self, actions, *, sources=None, runner=False, iframe=False, coming=False
    ):
        """Render the production template, then dispatch browser/media events in Node."""
        waiting = SimpleNamespace(is_video=True, get_video_mp4_json=sources)
        event = SimpleNamespace(
            id=1,
            is_current=not coming,
            is_coming=coming,
            is_past=False,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(hours=1),
            video_on_hold=waiting if sources is not None else None,
            broadcaster=SimpleNamespace(
                is_runner_live=runner,
                get_stream_url="https://media.example.com/live.m3u8",
                enable_viewer_count=True,
            ),
        )
        html = render_to_string(
            "live/event-script.html",
            {
                "event": event,
                "request": SimpleNamespace(GET={"is_iframe": "true"} if iframe else {}),
                "LOGO_PLAYER": "logo.png",
            },
        )
        inline_scripts = BeautifulSoup(html, "html.parser").select("script:not([src])")
        self.assertEqual(len(inline_scripts), 1, "Expected one inline playback script")
        script = inline_scripts[0].get_text()
        result = subprocess.run(
            [
                shutil.which("node"),
                str(Path(__file__).with_name("event_playback_harness.cjs")),
            ],
            input=json.dumps({"script": script, "actions": actions}),
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_missing_or_unencoded_waiting_video_does_not_raise_a_media_error(self):
        """Keep an empty waiting player as a poster instead of assigning src(null)."""
        for sources in (None, []):
            with self.subTest(sources=sources):
                state = self.playback(["dom"], sources=sources)[0]
                self.assertEqual(state["waitingSources"], [])
                self.assertEqual(state["errors"], [])
                self.assertEqual(state["openWaitingModals"], 1)
                self.assertFalse(state["liveLoop"])

    def test_metadata_does_not_hide_waiting_before_a_frame_is_ready(self):
        """Switch on media data, and tolerate repeated metadata after a reconnect."""
        for iframe in (False, True):
            with self.subTest(iframe=iframe):
                states = self.playback(
                    ["dom", "loadedmetadata", "loadedmetadata", "loadeddata", "playing"],
                    iframe=iframe,
                )
                self.assertEqual(states[2]["waitingDisplay"], "block")
                self.assertEqual(states[2]["openWaitingModals"], 1)
                self.assertEqual(states[3]["liveDisplay"], "block")
                self.assertEqual(states[3]["waitingDisplay"], "none")
                self.assertEqual(states[3]["openWaitingModals"], 0)
                self.assertEqual(states[4]["viewerCounts"], 1)

    def test_fast_stream_is_not_hidden_by_a_late_dom_content_loaded(self):
        """A cached/fast HLS startup must win over initial waiting UI setup."""
        states = self.playback(["loadedmetadata", "loadeddata", "dom"])
        self.assertEqual(states[-1]["liveDisplay"], "block")
        self.assertEqual(states[-1]["waitingDisplay"], "none")
        self.assertEqual(states[-1]["openWaitingModals"], 0)

    def test_successive_errors_retry_the_configured_hls_only_once(self):
        """Recover even when currentSrc/currentType are empty after source failure."""
        states = self.playback(["dom", "error", "error", "retry"])
        configured = {
            "src": "https://media.example.com/live.m3u8",
            "type": "application/x-mpegURL",
        }
        self.assertEqual(states[0]["liveSources"], [configured])
        self.assertEqual(states[2]["liveSources"], [configured])
        self.assertEqual(states[2]["pendingRetries"], 1)
        self.assertEqual(states[3]["liveSources"], [configured, configured])

    def test_recovery_cancels_retry_and_keeps_waiting_player_reusable(self):
        """A pending retry must not reset a recovered stream or remove waiting DOM."""
        sources = [{"src": "/media/waiting.mp4", "type": "video/mp4"}]
        states = self.playback(
            ["dom", "loadeddata", "error", "error", "loadedmetadata", "playing", "error"],
            sources=sources,
        )
        self.assertEqual(states[3]["pendingRetries"], 1)
        self.assertEqual(states[5]["pendingRetries"], 0)
        self.assertEqual(len(states[5]["liveSources"]), 1)
        self.assertEqual(states[5]["waitingDisplay"], "none")
        self.assertEqual(states[6]["waitingDisplay"], "block")
        self.assertEqual(states[6]["waitingSources"], [sources])
        self.assertEqual(states[6]["openWaitingModals"], 1)
        self.assertEqual(states[6]["waitingPlays"], 3)

    def test_player_disposal_cancels_pending_retry(self):
        """Do not reload a source after leaving or replacing the live player."""
        states = self.playback(["error", "dispose"])
        self.assertEqual(states[-1]["pendingRetries"], 0)

    def test_runner_waiting_player_survives_availability_changes(self):
        """Share waiting-player cleanup without adding fixed-URL retries to Runner."""
        sources = [{"src": "/media/waiting.mp4", "type": "video/mp4"}]
        states = self.playback(
            [
                "dom",
                "runner-unavailable",
                "loadedmetadata",
                "runner-available",
                "loadeddata",
                "playing",
                "runner-unavailable",
                "runner-available",
                "playing",
            ],
            sources=sources,
            runner=True,
        )
        self.assertEqual(states[2]["waitingDisplay"], "block")
        self.assertEqual(states[3]["waitingDisplay"], "none")
        self.assertEqual(states[6]["waitingDisplay"], "block")
        self.assertEqual(states[6]["waitingPlays"], 2)
        self.assertEqual(states[5]["liveDisplay"], "block")
        self.assertEqual(states[5]["waitingDisplay"], "none")
        self.assertEqual(states[8]["waitingDisplay"], "none")
        self.assertEqual(states[8]["liveSources"], [])

    def test_future_event_can_play_its_waiting_video_without_a_live_player(self):
        """Preserve waiting playback before the scheduled event starts."""
        sources = [{"src": "/media/waiting.mp4", "type": "video/mp4"}]
        state = self.playback(["dom"], coming=True, sources=sources)[0]
        self.assertEqual(state["waitingDisplay"], "block")
        self.assertEqual(state["waitingSources"], [sources])
        self.assertEqual(state["openWaitingModals"], 0)
