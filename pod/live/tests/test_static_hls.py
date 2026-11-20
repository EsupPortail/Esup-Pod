"""Regression coverage for fixed HLS broadcasters after Runner Live support."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape, escapejs
from rest_framework.test import APIClient

from pod.live.forms import BroadcasterAdminForm
from pod.live.models import Broadcaster, Building, Event
from pod.video.models import Type
from pod.video_encode_transcript.models import RunnerManager

STATIC_URL = "https://media.example.com/live.m3u8?token=a%2Fb&expires=2000000000"


class StaticHLSResolverTests(SimpleTestCase):
    """Keep static playback independent of Runner, cache and callback readiness."""

    def test_static_url_is_exact_without_database_network_or_cache_access(self):
        """Ignore Runner settings and preserve signed URLs even with status false."""
        manager = RunnerManager(id=12, is_active=False, supports_live=False)
        for status in (False, True):
            for configured in (False, True):
                with (
                    self.subTest(status=status, configured=configured),
                    patch("pod.live.runner_live.requests.get") as manager_get,
                    patch("pod.live.runner_live.probe_hls") as probe,
                    patch("pod.live.runner_live.cache") as live_cache,
                ):
                    broadcaster = Broadcaster(url=STATIC_URL, status=status)
                    if configured:
                        broadcaster.runner_manager = manager
                        broadcaster.secondary_runner_manager = manager
                        broadcaster.source_id = "unused-source"
                    self.assertEqual(
                        broadcaster.get_stream_info(),
                        {
                            "live_id": None,
                            "state": "running" if status else "stopped",
                            "hls_ready": True,
                            "hls_url": STATIC_URL,
                        },
                    )
                    self.assertEqual(broadcaster.get_stream_url(), STATIC_URL)
                    manager_get.assert_not_called()
                    probe.assert_not_called()
                    self.assertEqual(live_cache.mock_calls, [])


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class StaticHLSCompatibilityTests(TestCase):
    """Exercise existing configuration, pages and REST clients without a manager."""

    def setUp(self):
        """Create a legacy broadcaster using only the fields available before Live."""
        Site.objects.clear_cache()
        self.addCleanup(Site.objects.clear_cache)
        self.building = Building.objects.create(name="Static HLS building")
        self.admin = User.objects.create_superuser(username="static-hls-admin")
        self.broadcaster = Broadcaster.objects.create(
            name="Legacy HLS broadcaster",
            building=self.building,
            url=STATIC_URL,
        )
        self.event = Event.objects.create(
            title="Static HLS event",
            owner=self.admin,
            broadcaster=self.broadcaster,
            type=Type.objects.create(title="Static HLS type"),
            is_draft=False,
            start_date=timezone.now() - timezone.timedelta(minutes=5),
            end_date=timezone.now() + timezone.timedelta(minutes=20),
        )
        self.api = APIClient()
        self.api.force_authenticate(user=self.admin)
        self.detail_url = reverse("broadcaster-detail", args=[self.broadcaster.slug])
        manager_patch = patch("pod.live.runner_live.requests.get")
        self.manager_get = manager_patch.start()
        self.addCleanup(manager_patch.stop)
        self.addCleanup(self.manager_get.assert_not_called)

    def test_default_static_configuration_needs_no_manager_or_source(self):
        """Continue validating broadcasters created with the legacy model fields."""
        self.broadcaster.refresh_from_db()
        self.broadcaster.full_clean(exclude=["piloting_implementation"])
        self.assertEqual(self.broadcaster.stream_mode, Broadcaster.StreamMode.STATIC)
        self.assertFalse(self.broadcaster.is_runner_live)
        self.assertIsNone(self.broadcaster.runner_manager_id)
        self.assertIsNone(self.broadcaster.secondary_runner_manager_id)
        self.assertEqual(self.broadcaster.source_id, "")
        self.assertEqual(self.broadcaster.get_stream_url(), STATIC_URL)

    def test_admin_create_and_edit_require_url_without_runner_fields(self):
        """Keep the fixed-URL admin form usable with a local cache and no manager."""
        data = {
            "name": "Another static broadcaster",
            "building": self.building.pk,
            "main_lang": "en",
            "stream_mode": Broadcaster.StreamMode.STATIC,
            "url": "https://media.example.com/another.m3u8",
        }
        form = BroadcasterAdminForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        created = form.save()
        self.assertEqual(created.stream_mode, Broadcaster.StreamMode.STATIC)
        self.client.force_login(self.admin)
        page = self.client.get(
            reverse("admin:live_broadcaster_change", args=[self.broadcaster.pk])
        )
        self.assertEqual(page.status_code, 200)
        edit_form = page.context["adminform"].form
        self.assertTrue(edit_form.fields["url"].required)
        self.assertFalse(edit_form.fields["runner_manager"].required)
        self.assertFalse(edit_form.fields["source_id"].required)
        form = BroadcasterAdminForm(
            {**data, "name": self.broadcaster.name, "url": STATIC_URL},
            instance=self.broadcaster,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().url, STATIC_URL)

    def test_legacy_rest_creation_and_put_omit_all_runner_fields(self):
        """Accept the original API payload and keep broadcaster_url as the HLS URL."""
        data = {
            "name": "Legacy REST broadcaster",
            "building": reverse("building-detail", args=[self.building.pk]),
            "broadcaster_url": "https://media.example.com/legacy.m3u8?key=a%2Fb&v=1",
            "status": True,
        }
        created = self.api.post(reverse("broadcaster-list"), data, format="json")
        self.assertEqual(created.status_code, 201, created.data)
        self.assertEqual(created.data["stream_mode"], Broadcaster.StreamMode.STATIC)
        self.assertEqual(created.data["broadcaster_url"], data["broadcaster_url"])
        detail_url = reverse("broadcaster-detail", args=[created.data["slug"]])
        updated = self.api.put(detail_url, {**data, "status": False}, format="json")
        self.assertEqual(updated.status_code, 200, updated.data)
        self.assertEqual(updated.data["broadcaster_url"], data["broadcaster_url"])
        self.assertFalse(updated.data["status"])
        self.assertIsNone(updated.data["runner_manager"])
        self.assertIsNone(updated.data["secondary_runner_manager"])

    def test_status_callbacks_preserve_static_url_and_configuration(self):
        """Accept existing on/off PATCH callbacks without changing playback mode."""
        for status in (True, False):
            with self.subTest(status=status):
                result = self.api.patch(
                    self.detail_url, {"status": status}, format="json"
                )
                self.assertEqual(result.status_code, 200, result.data)
                self.assertEqual(result.data["broadcaster_url"], STATIC_URL)
                self.broadcaster.refresh_from_db()
                self.assertEqual(self.broadcaster.status, status)
                self.assertEqual(self.broadcaster.url, STATIC_URL)
                self.assertFalse(self.broadcaster.is_runner_live)
                self.assertIsNone(self.broadcaster.runner_manager_id)
                self.assertIsNone(self.broadcaster.secondary_runner_manager_id)
                self.assertEqual(self.broadcaster.source_id, "")

    def test_transcription_callback_keeps_receiving_the_static_url(self):
        """Preserve transcription startup/shutdown arguments for static streams."""
        self.event.enable_transcription = True
        self.event.save()
        with (
            patch("pod.live.rest_views.USE_LIVE_TRANSCRIPTION", True),
            patch("pod.live.rest_views.transcribe_live", create=True) as transcribe,
        ):
            for status in (True, False):
                with self.subTest(status=status):
                    result = self.api.patch(
                        self.detail_url, {"status": status}, format="json"
                    )
                    self.assertEqual(result.status_code, 200, result.data)
                    transcribe.assert_called_with(
                        STATIC_URL,
                        self.broadcaster.slug,
                        status,
                        self.broadcaster.main_lang,
                        self.broadcaster.transcription_file.path,
                    )

    def test_direct_event_and_iframe_keep_static_sources_without_runner_polling(self):
        """Render signed HLS URLs correctly regardless of the status callback value."""
        self.client.force_login(self.admin)
        for status in (False, True):
            self.broadcaster.status = status
            self.broadcaster.save()
            for path in (
                self.broadcaster.get_absolute_url(),
                self.event.get_absolute_url(),
                self.event.get_absolute_url() + "?is_iframe=true",
            ):
                with self.subTest(status=status, path=path):
                    page = self.client.get(path)
                    self.assertContains(page, f'<source src="{escape(STATIC_URL)}"')
                    self.assertContains(page, str(escapejs(STATIC_URL)))
                    self.assertNotContains(page, "js/runner_live.js")
                    self.assertNotContains(page, "PodRunnerLive.start")
                    self.assertNotContains(page, 'id="runner-live-status"')

    def test_public_event_and_iframe_remain_accessible_anonymously(self):
        """Preserve public event access while the direct page still requires login."""
        for suffix in ("", "?is_iframe=true"):
            page = self.client.get(self.event.get_absolute_url() + suffix)
            self.assertContains(page, f'<source src="{escape(STATIC_URL)}"')
        direct = self.client.get(self.broadcaster.get_absolute_url())
        self.assertEqual(direct.status_code, 302)

    def test_password_protection_still_guards_static_pages_and_playback(self):
        """Require the event password before exposing its HLS URL or player."""
        self.event.password = "static-event-password"
        self.event.save()
        event_url = self.event.get_absolute_url()
        for suffix in ("", "?is_iframe=true"):
            page = self.client.get(event_url + suffix)
            self.assertEqual(page.status_code, 200)
            self.assertNotContains(page, f'<source src="{escape(STATIC_URL)}"')
            self.assertNotContains(page, 'videojs("podvideoplayer"')
        denied = self.client.get(event_url, {"stream": "1"})
        self.assertEqual(denied.status_code, 403)
        unlocked = self.client.post(event_url, {"password": self.event.password})
        self.assertContains(unlocked, f'<source src="{escape(STATIC_URL)}"')
        playback = self.client.get(event_url, {"stream": "1"})
        self.assertEqual(playback.status_code, 200)
        self.assertEqual(playback.json()["hls_url"], STATIC_URL)
