"""
Esup-Pod - Live app tests.

Test suite for Buildings, Broadcasters, Events, Heartbeats and permissions.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status

from src.apps.live.models import Building, Broadcaster, Event, HeartBeat
from src.apps.video.models import Type

User = get_user_model()


def _make_building(name="Campus A"):
    """Test helper: create a building."""
    site = Site.objects.get_current()
    b = Building.objects.create(name=name)
    b.sites.add(site)
    return b


def _make_broadcaster(building, name="Broadcaster 1", public=True):
    """Test helper: create a broadcaster."""
    return Broadcaster.objects.create(
        name=name,
        building=building,
        url=f"rtmp://stream.example.com/{name.replace(' ', '_').lower()}",
        public=public,
        status=True,
    )


def _make_event(broadcaster, owner, title="Test Event", is_draft=False):
    """Test helper: create a event."""
    video_type, _ = Type.objects.get_or_create(title="Course", slug="course")
    return Event.objects.create(
        title=title,
        broadcaster=broadcaster,
        owner=owner,
        type=video_type,
        start_date=timezone.now() + timezone.timedelta(hours=1),
        end_date=timezone.now() + timezone.timedelta(hours=2),
        is_draft=is_draft,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class BuildingModelTest(TestCase):
    """Test suite for BuildingModelTest."""

    def test_str(self):
        """Test str."""
        b = Building(name="Library")
        self.assertEqual(str(b), "Library")

    def test_default_site_assigned_on_creation(self):
        """Test default site assigned on creation."""
        b = _make_building("Admin Building")
        self.assertIn(Site.objects.get_current(), b.sites.all())


class BroadcasterModelTest(TestCase):
    """Test suite for BroadcasterModelTest."""

    def setUp(self):
        """Set up test fixtures."""
        self.building = _make_building()

    def test_slug_auto_generated(self):
        """Test slug auto generated."""
        br = _make_broadcaster(self.building, name="Main Hall Camera")
        self.assertEqual(br.slug, "main-hall-camera")

    def test_str(self):
        """Test str."""
        br = _make_broadcaster(self.building, "Cam 1")
        self.assertIn("Cam 1", str(br))

    def test_is_recording_returns_false_without_piloting(self):
        """Test is recording returns false without piloting."""
        br = _make_broadcaster(self.building)
        self.assertFalse(br.is_recording())


class EventModelTest(TestCase):
    """Test suite for EventModelTest."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user("owner", password="pass")
        self.building = _make_building()
        self.broadcaster = _make_broadcaster(self.building)

    def test_str_contains_title(self):
        """Test str contains title."""
        evt = _make_event(self.broadcaster, self.user, "My Lecture")
        self.assertIn("My Lecture", str(evt))

    def test_is_coming_future_event(self):
        """Test is coming future event."""
        evt = _make_event(self.broadcaster, self.user)
        self.assertTrue(evt.is_coming())
        self.assertFalse(evt.is_current())
        self.assertFalse(evt.is_past())

    def test_is_current_live_event(self):
        """Test is current live event."""
        video_type, _ = Type.objects.get_or_create(title="Course", slug="course")
        evt = Event.objects.create(
            title="Live Now",
            broadcaster=self.broadcaster,
            owner=self.user,
            type=video_type,
            start_date=timezone.now() - timezone.timedelta(minutes=5),
            end_date=timezone.now() + timezone.timedelta(minutes=55),
        )
        self.assertTrue(evt.is_current())

    def test_hashkey_is_deterministic(self):
        """Test hashkey is deterministic."""
        evt = _make_event(self.broadcaster, self.user)
        self.assertEqual(evt.get_hashkey(), evt.get_hashkey())

    def test_event_date_validation_in_serializer(self):
        """Test event date validation in serializer."""
        from src.apps.live.serializers import EventSerializer

        video_type, _ = Type.objects.get_or_create(title="Course", slug="course")
        data = {
            "title": "Bad Event",
            "broadcaster": self.broadcaster.id,
            "type": video_type.id,
            "start_date": timezone.now() + timezone.timedelta(hours=2),
            "end_date": timezone.now() + timezone.timedelta(hours=1),
        }
        serializer = EventSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("end_date", serializer.errors)


# ---------------------------------------------------------------------------
# API Tests — Buildings
# ---------------------------------------------------------------------------


class BuildingAPITest(TestCase):
    """Test suite for BuildingAPITest."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.building = _make_building("Science Building")

    def test_list_buildings(self):
        """Test list buildings."""
        response = self.client.get("/api/live/buildings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Science Building")

    def test_retrieve_building(self):
        """Test retrieve building."""
        response = self.client.get(f"/api/live/buildings/{self.building.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# API Tests — Broadcasters
# ---------------------------------------------------------------------------


class BroadcasterAPITest(TestCase):
    """Test suite for BroadcasterAPITest."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.building = _make_building()
        self.broadcaster = _make_broadcaster(self.building, public=True)
        self.private_broadcaster = _make_broadcaster(
            self.building, name="Private Cam", public=False
        )

    def test_list_only_public_broadcasters_for_anonymous(self):
        """Test list only public broadcasters for anonymous."""
        response = self.client.get("/api/live/broadcasters/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [r["name"] for r in response.data["results"]]
        self.assertIn("Broadcaster 1", names)
        self.assertNotIn("Private Cam", names)

    def test_retrieve_public_broadcaster(self):
        """Test retrieve public broadcaster."""
        response = self.client.get(f"/api/live/broadcasters/{self.broadcaster.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_restricted_broadcaster_requires_auth(self):
        """Test retrieve restricted broadcaster requires auth."""
        self.broadcaster.is_restricted = True
        self.broadcaster.save()
        response = self.client.get(f"/api/live/broadcasters/{self.broadcaster.slug}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_start_record_requires_auth(self):
        """Test start record requires auth."""
        response = self.client.post(
            f"/api/live/broadcasters/{self.broadcaster.slug}/start_record/",
            {"event_id": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_start_record_without_piloting_returns_400(self):
        """Test start record without piloting returns 400."""
        user = User.objects.create_superuser("admin", password="pass")
        self.client.force_authenticate(user=user)
        response = self.client.post(
            f"/api/live/broadcasters/{self.broadcaster.slug}/start_record/",
            {"event_id": 1},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# API Tests — Events
# ---------------------------------------------------------------------------


class EventAPITest(TestCase):
    """Test suite for EventAPITest."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.owner = User.objects.create_user("eventowner", password="pass")
        self.other = User.objects.create_user("other", password="pass")
        self.building = _make_building()
        self.broadcaster = _make_broadcaster(self.building)
        self.event = _make_event(self.broadcaster, self.owner, is_draft=False)

    def test_list_returns_upcoming_non_draft(self):
        """Test list returns upcoming non draft."""
        response = self.client.get("/api/live/events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_draft_not_visible_in_list(self):
        """Test draft not visible in list."""
        _make_event(self.broadcaster, self.owner, "Hidden Draft", is_draft=True)
        response = self.client.get("/api/live/events/")
        self.assertEqual(response.data["count"], 1)

    def test_retrieve_public_event(self):
        """Test retrieve public event."""
        response = self.client.get(f"/api/live/events/{self.event.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)

    def test_retrieve_draft_blocked_for_non_owner(self):
        """Test retrieve draft blocked for non owner."""
        draft = _make_event(self.broadcaster, self.owner, "Draft Only", is_draft=True)
        response = self.client.get(f"/api/live/events/{draft.slug}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_draft_accessible_with_hashkey(self):
        """Test retrieve draft accessible with hashkey."""
        draft = _make_event(self.broadcaster, self.owner, "Private", is_draft=True)
        key = draft.get_hashkey()
        response = self.client.get(f"/api/live/events/{draft.slug}/?key={key}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_protected_event_returns_403_for_non_owner(self):
        """Test password protected event returns 403 for non owner."""
        self.event.password = "secret"
        self.event.save()
        response = self.client.get(f"/api/live/events/{self.event.slug}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.data.get("password_required"))

    def test_unlock_correct_password(self):
        """Test unlock correct password."""
        self.event.password = "secret"
        self.event.save()
        response = self.client.post(
            f"/api/live/events/{self.event.slug}/unlock/", {"password": "secret"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unlock_wrong_password(self):
        """Test unlock wrong password."""
        self.event.password = "secret"
        self.event.save()
        response = self.client.post(
            f"/api/live/events/{self.event.slug}/unlock/", {"password": "wrong"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_my_events_requires_auth(self):
        """Test my events requires auth."""
        response = self.client.get("/api/live/events/my-events/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_my_events_returns_owned_events(self):
        """Test my events returns owned events."""
        self.client.force_authenticate(user=self.owner)
        # Include a draft (should appear for owner)
        _make_event(self.broadcaster, self.owner, "My Draft", is_draft=True)
        response = self.client.get("/api/live/events/my-events/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_my_events_does_not_return_others_events(self):
        """Test my events does not return others events."""
        self.client.force_authenticate(user=self.other)
        response = self.client.get("/api/live/events/my-events/")
        self.assertEqual(response.data["count"], 0)

    def test_create_event_requires_auth(self):
        """Test create event requires auth."""
        video_type, _ = Type.objects.get_or_create(title="Course", slug="course")
        response = self.client.post(
            "/api/live/events/",
            {
                "title": "New Event",
                "broadcaster": self.broadcaster.id,
                "type": video_type.id,
                "start_date": timezone.now() + timezone.timedelta(hours=1),
                "end_date": timezone.now() + timezone.timedelta(hours=2),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_event_by_non_owner_forbidden(self):
        """Test delete event by non owner forbidden."""
        self.client.force_authenticate(user=self.other)
        response = self.client.delete(f"/api/live/events/{self.event.slug}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_event_by_owner_allowed(self):
        """Test delete event by owner allowed."""
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(f"/api/live/events/{self.event.slug}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Heartbeat Tests
# ---------------------------------------------------------------------------


class HeartBeatAPITest(TestCase):
    """Test suite for HeartBeatAPITest."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.owner = User.objects.create_user("hbowner", password="pass")
        self.building = _make_building()
        self.broadcaster = _make_broadcaster(self.building)
        self.event = _make_event(self.broadcaster, self.owner, is_draft=False)

    def test_heartbeat_without_viewkey_returns_400(self):
        """Test heartbeat without viewkey returns 400."""
        response = self.client.post(f"/api/live/events/{self.event.slug}/heartbeat/", {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_heartbeat_increments_viewer_count(self):
        """Test heartbeat increments viewer count."""
        response = self.client.post(
            f"/api/live/events/{self.event.slug}/heartbeat/",
            {"viewkey": "abc-unique-key-1"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["viewers"], 1)

    def test_heartbeat_same_viewkey_does_not_duplicate(self):
        """Test heartbeat same viewkey does not duplicate."""
        for _ in range(3):
            self.client.post(
                f"/api/live/events/{self.event.slug}/heartbeat/",
                {"viewkey": "same-key"},
            )
        self.assertEqual(self.event.heartbeats.count(), 1)

    def test_heartbeat_multiple_viewers(self):
        """Test heartbeat multiple viewers."""
        for i in range(5):
            self.client.post(
                f"/api/live/events/{self.event.slug}/heartbeat/",
                {"viewkey": f"viewer-{i}"},
            )
        response = self.client.post(
            f"/api/live/events/{self.event.slug}/heartbeat/",
            {"viewkey": "viewer-5"},
        )
        self.assertEqual(response.data["viewers"], 6)

    def test_cleanup_stale_heartbeats(self):
        """Test cleanup stale heartbeats."""
        hb = HeartBeat.objects.create(
            viewkey="old-viewer",
            event=self.event,
            last_heartbeat=timezone.now() - timezone.timedelta(minutes=5),
        )
        HeartBeat.cleanup_stale(self.event, delay_seconds=45)
        self.assertFalse(HeartBeat.objects.filter(pk=hb.pk).exists())
