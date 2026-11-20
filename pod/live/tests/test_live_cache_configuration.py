"""Esup-Pod tests for secondary Live configuration with incompatible caches."""

from html import unescape
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse

from pod.live.cache_config import (
    INCOMPATIBLE_LIVE_CACHE_WARNING,
    SHARED_LIVE_CACHE_HELP,
)
from pod.live.forms import BroadcasterAdminForm
from pod.live.models import Broadcaster
from pod.live.rest_views import BroadcasterSerializer
from pod.live.tests.test_runner_live import RunnerLiveDatabaseTestCase
from pod.video_encode_transcript.models import RunnerManager

INCOMPATIBLE_BACKENDS = (
    "django.core.cache.backends.locmem.LocMemCache",
    "django.core.cache.backends.dummy.DummyCache",
)
REDIS_BACKENDS = (
    "django_redis.cache.RedisCache",
    "django.core.cache.backends.redis.RedisCache",
)


def cache_settings(backend):
    """Use different default/select2 backends to verify only default is inspected."""
    return {
        "default": {
            "BACKEND": backend,
            "LOCATION": "redis://redis.example.invalid:6379/3",
        },
        "select2": {
            "BACKEND": (
                REDIS_BACKENDS[0]
                if backend in INCOMPATIBLE_BACKENDS
                else INCOMPATIBLE_BACKENDS[0]
            ),
            "LOCATION": "redis://redis.example.invalid:6379/2",
        },
    }


class LiveCacheConfigurationTests(RunnerLiveDatabaseTestCase):
    """Cover admin restrictions and model/REST validation without a Redis server."""

    def setUp(self):
        """Prepare a broadcaster and two eligible secondary managers."""
        super().setUp()
        self.secondary = RunnerManager.objects.create(
            name="Secondary manager",
            url="https://secondary.example.com",
            token="secondary-token",
            supports_live=True,
            site=self.site,
        )
        self.replacement = RunnerManager.objects.create(
            name="Replacement manager",
            url="https://replacement.example.com",
            token="replacement-token",
            supports_live=True,
            site=self.site,
        )

    def form_data(self, **overrides):
        """Build a valid admin update with optional secondary changes."""
        return {
            "name": self.broadcaster.name,
            "building": self.building.pk,
            "main_lang": "en",
            "stream_mode": Broadcaster.StreamMode.ESUP_RUNNER,
            "runner_manager": self.manager.pk,
            "source_id": self.broadcaster.source_id,
            **overrides,
        }

    def assign_existing_secondary(self):
        """Represent a secondary saved before the cache configuration changed."""
        self.broadcaster.secondary_runner_manager = self.secondary
        self.broadcaster.save()

    def test_admin_add_and_change_warn_and_disable_secondary(self):
        """Warn on both admin pages even when select2 already uses Redis."""
        user = User.objects.create_superuser(username="live-cache-admin")
        self.client.force_login(user)
        self.assign_existing_secondary()
        paths = (
            reverse("admin:live_broadcaster_add"),
            reverse("admin:live_broadcaster_change", args=[self.broadcaster.pk]),
        )
        for backend in INCOMPATIBLE_BACKENDS:
            with (
                self.subTest(backend=backend),
                override_settings(CACHES=cache_settings(backend)),
            ):
                for path in paths:
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(
                        str(INCOMPATIBLE_LIVE_CACHE_WARNING),
                        unescape(response.content.decode()),
                    )
                    self.assertIn(
                        str(SHARED_LIVE_CACHE_HELP), unescape(response.content.decode())
                    )
                    form = response.context["adminform"].form
                    self.assertTrue(form.fields["secondary_runner_manager"].disabled)
                    self.assertIn("disabled", str(form["secondary_runner_manager"]))
                    if form.instance.pk:
                        self.assertEqual(
                            form.initial["secondary_runner_manager"], self.secondary.pk
                        )

    def test_posted_secondary_cannot_override_disabled_admin_field(self):
        """Ignore forged secondary values on new and existing assignments."""
        for backend in INCOMPATIBLE_BACKENDS:
            with (
                self.subTest(backend=backend),
                override_settings(CACHES=cache_settings(backend)),
            ):
                for previous in (None, self.secondary):
                    self.broadcaster.secondary_runner_manager = previous
                    self.broadcaster.save()
                    form = BroadcasterAdminForm(
                        self.form_data(secondary_runner_manager=self.replacement.pk),
                        instance=self.broadcaster,
                    )
                    self.assertTrue(form.is_valid(), form.errors)
                    form.save()
                    self.broadcaster.refresh_from_db()
                    self.assertEqual(self.broadcaster.secondary_runner_manager, previous)

    def test_model_rejects_new_secondary_on_local_or_dummy_cache(self):
        """Reject new assignments on both unsaved and existing broadcasters."""
        for backend in INCOMPATIBLE_BACKENDS:
            with (
                self.subTest(backend=backend),
                override_settings(CACHES=cache_settings(backend)),
            ):
                for pk in (None, self.broadcaster.pk):
                    candidate = Broadcaster(
                        pk=pk,
                        building=self.building,
                        stream_mode=Broadcaster.StreamMode.ESUP_RUNNER,
                        runner_manager=self.manager,
                        secondary_runner_manager=self.secondary,
                        source_id="source-A",
                    )
                    with self.assertRaises(ValidationError) as error:
                        candidate.clean()
                    self.assertIn(
                        "secondary_runner_manager", error.exception.message_dict
                    )

    def test_rest_rejects_secondary_on_creation_and_partial_update(self):
        """Apply the same restriction when clients bypass the admin form."""
        for backend in INCOMPATIBLE_BACKENDS:
            with (
                self.subTest(backend=backend),
                override_settings(CACHES=cache_settings(backend)),
            ):
                serializers = (
                    BroadcasterSerializer(
                        data={
                            "name": "New Live broadcaster",
                            "building": reverse(
                                "building-detail", args=[self.building.pk]
                            ),
                            "stream_mode": Broadcaster.StreamMode.ESUP_RUNNER,
                            "runner_manager": self.manager.pk,
                            "secondary_runner_manager": self.secondary.pk,
                            "source_id": "source-B",
                        }
                    ),
                    BroadcasterSerializer(
                        self.broadcaster,
                        data={"secondary_runner_manager": self.secondary.pk},
                        partial=True,
                    ),
                )
                for serializer in serializers:
                    self.assertFalse(serializer.is_valid())
                    self.assertIn("secondary_runner_manager", serializer.errors)

    def test_existing_secondary_can_be_preserved_or_cleared(self):
        """Keep existing configurations editable after a switch to a local cache."""
        self.assign_existing_secondary()
        for backend in INCOMPATIBLE_BACKENDS:
            with (
                self.subTest(backend=backend),
                override_settings(CACHES=cache_settings(backend)),
            ):
                self.assign_existing_secondary()
                self.broadcaster.clean()
                for data in (
                    {"status": True},
                    {"secondary_runner_manager": self.secondary.pk},
                    {"secondary_runner_manager": None},
                ):
                    serializer = BroadcasterSerializer(
                        self.broadcaster, data=data, partial=True
                    )
                    self.assertTrue(serializer.is_valid(), serializer.errors)
                    serializer.save()
                    self.broadcaster.refresh_from_db()
                    expected = (
                        None
                        if data.get("secondary_runner_manager", True) is None
                        else self.secondary
                    )
                    self.assertEqual(self.broadcaster.secondary_runner_manager, expected)

    def test_existing_secondary_cannot_be_replaced(self):
        """Preserving a saved manager must not allow assigning another one."""
        self.assign_existing_secondary()
        for backend in INCOMPATIBLE_BACKENDS:
            with (
                self.subTest(backend=backend),
                override_settings(CACHES=cache_settings(backend)),
            ):
                serializer = BroadcasterSerializer(
                    self.broadcaster,
                    data={"secondary_runner_manager": self.replacement.pk},
                    partial=True,
                )
                self.assertFalse(serializer.is_valid())
                self.assertIn("secondary_runner_manager", serializer.errors)
                self.broadcaster.secondary_runner_manager = self.replacement
                with self.assertRaises(ValidationError) as error:
                    self.broadcaster.clean()
                self.assertIn("secondary_runner_manager", error.exception.message_dict)
                self.broadcaster.refresh_from_db()

    def test_redis_backends_enable_secondary_without_a_network_probe(self):
        """Accept Redis configuration without mistaking it for verified sharing."""
        for backend in REDIS_BACKENDS:
            with (
                self.subTest(backend=backend),
                override_settings(CACHES=cache_settings(backend)),
                patch("redis.connection.Connection.connect") as connect,
            ):
                form = BroadcasterAdminForm(
                    self.form_data(secondary_runner_manager=self.secondary.pk),
                    instance=self.broadcaster,
                )
                self.assertFalse(form.fields["secondary_runner_manager"].disabled)
                self.assertTrue(form.is_valid(), form.errors)
                serializer = BroadcasterSerializer(
                    self.broadcaster,
                    data={"secondary_runner_manager": self.secondary.pk},
                    partial=True,
                )
                self.assertTrue(serializer.is_valid(), serializer.errors)
                connect.assert_not_called()
