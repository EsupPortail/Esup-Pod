"""Test case for Pod live."""

import os
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.safestring import SafeString

from pod.video.models import Type
from pod.video.models import Video
from ..models import (
    Building,
    Broadcaster,
    HeartBeat,
    Event,
    get_available_broadcasters_of_building,
    get_building_having_available_broadcaster,
    get_default_event_type,
    present_or_future_date,
)
from django.utils import timezone

LIVE_TRANSCRIPTIONS_FOLDER = getattr(
    settings, "LIVE_TRANSCRIPTIONS_FOLDER", "live_transcripts"
)
MEDIA_URL = getattr(settings, "MEDIA_URL", None)

if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel


class BuildingTestCase(TestCase):
    def setUp(self):
        Building.objects.create(name="building1")
        print(" --->  SetUp of BuildingTestCase: OK!")

    def test_attributs(self):
        """Test attributs."""
        building = Building.objects.get(id=1)
        self.assertEqual(building.name, "building1")
        building.gmapurl = "b"
        building.save()
        self.assertEqual(building.gmapurl, "b")
        if FILEPICKER:
            user = User.objects.create(username="pod")
            homedir, created = UserFolder.objects.get_or_create(name="Home", owner=user)
            headband = CustomImageModel.objects.create(
                folder=homedir, created_by=user, file="blabla.jpg"
            )
        else:
            headband = CustomImageModel.objects.create(file="blabla.jpg")
        building.headband = headband
        building.save()
        self.assertTrue("blabla" in building.headband.name)
        print("   --->  test_attributs of BuildingTestCase: OK!")

    def test_delete_object(self):
        """Test delete object."""
        Building.objects.get(id=1).delete()
        self.assertEqual(Building.objects.all().count(), 0)

        print("   --->  test_delete_object of BuildingTestCase: OK!")


"""
    test recorder object
"""


class BroadcasterTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        building = Building.objects.create(name="building1")
        user = User.objects.create(username="pod")
        if FILEPICKER:
            homedir, created = UserFolder.objects.get_or_create(name="Home", owner=user)
            poster = CustomImageModel.objects.create(
                folder=homedir, created_by=user, file="blabla.jpg"
            )
        else:
            poster = CustomImageModel.objects.create(file="blabla.jpg")
        Broadcaster.objects.create(
            name="broadcaster1",
            poster=poster,
            url="http://test.live",
            status=True,
            is_restricted=True,
            building=building,
            public=False,
            main_lang="fr",
            transcription_file="testfile.vtt",
        )
        Broadcaster.objects.create(
            name="broadcaster2",
            poster=poster,
            url="http://test2.live",
            status=True,
            is_restricted=False,
            building=building,
            main_lang="en",
        )
        print(" --->  SetUp of BroadcasterTestCase: OK!")

    def test_attributs(self):
        """Test attributs."""
        broadcaster = Broadcaster.objects.get(id=1)
        self.assertEqual(broadcaster.name, "broadcaster1")
        self.assertTrue("blabla" in broadcaster.poster.name)
        self.assertEqual(broadcaster.url, "http://test.live")
        self.assertEqual(broadcaster.status, True)
        self.assertEqual(broadcaster.public, False)
        self.assertEqual(broadcaster.is_restricted, True)
        self.assertEqual(broadcaster.building.id, 1)
        self.assertEqual(broadcaster.sites.count(), 1)
        self.assertEqual(
            broadcaster.__str__(),
            "%s - %s" % (broadcaster.name, broadcaster.url),
        )
        self.assertEqual(
            broadcaster.get_absolute_url(), "/live/direct/%s/" % broadcaster.slug
        )
        self.assertTrue(isinstance(broadcaster.qrcode, SafeString))
        empty_qrcode = '"data:image/png;base64, "'
        self.assertNotIn(empty_qrcode, broadcaster.qrcode)
        none_qrcode = '"data:image/png;base64, None"'
        self.assertNotIn(none_qrcode, broadcaster.qrcode)
        self.assertEqual(broadcaster.main_lang, "fr")
        trans_file = os.path.join(
            MEDIA_URL, LIVE_TRANSCRIPTIONS_FOLDER, "broadcaster1.vtt"
        )
        self.assertEqual(broadcaster.transcription_file.url, trans_file)
        broadcaster2 = Broadcaster.objects.get(id=2)
        self.assertEqual(broadcaster2.main_lang, "en")
        print("   --->  test_attributs of BroadcasterTestCase: OK!")

    def test_delete_object(self):
        """Test delete object."""
        Broadcaster.objects.get(id=1).delete()
        Broadcaster.objects.get(id=2).delete()
        self.assertEqual(Broadcaster.objects.all().count(), 0)

        print("   --->  test_delete_object of BroadcasterTestCase: OK!")

    def test_is_recording_admin(self):
        html = Broadcaster.objects.get(id=1).is_recording_admin()
        expected_html = '<img src="/static/admin/img/icon-no.svg" alt="No">'
        self.assertEqual(html, expected_html)


class HeartbeatTestCase(TestCase):
    def setUp(self):
        building = Building.objects.create(name="building1")
        broad = Broadcaster.objects.create(
            name="broadcaster1",
            url="http://test.live",
            status=True,
            is_restricted=True,
            building=building,
            public=False,
        )
        user = User.objects.create(username="pod")
        h_type = Type.objects.create(title="type1")
        event = Event.objects.create(
            title="event1", owner=user, broadcaster=broad, type=h_type
        )
        HeartBeat.objects.create(
            user=user,
            viewkey="testkey",
            last_heartbeat=timezone.now(),
            event=event,
        )
        print(" --->  SetUp of HeartbeatTestCase: OK!")

    def test_attributs(self):
        """Test attributs."""
        hb = HeartBeat.objects.get(id=1)
        self.assertEqual(hb.user.username, "pod")
        self.assertEqual(hb.viewkey, "testkey")
        self.assertEqual(hb.event.title, "event1")
        print("   --->  test_attributs of HeartbeatTestCase: OK!")


def add_video(event):
    e_video = Video.objects.get(id=1)
    event.videos.add(e_video)
    return event


class EventTestCase(TestCase):
    def setUp(self):
        building = Building.objects.create(name="building1")
        building2 = Building.objects.create(name="building2")
        e_broad = Broadcaster.objects.create(
            name="broadcaster1",
            building=building,
            url="http://first.url",
            enable_add_event=True,
        )
        Broadcaster.objects.create(
            name="broadcaster2",
            building=building,
            url="http://second.url",
            enable_add_event=True,
        )
        Broadcaster.objects.create(
            name="broadcaster3", building=building, url="http://third.url"
        )
        Broadcaster.objects.create(
            name="broad_b2", building=building2, url="http://firstb2.url"
        )
        e_user = User.objects.create(username="user1")
        e_type = Type.objects.create(title="type1")
        Video.objects.create(
            video="event_video.mp4",
            owner=e_user,
            type=e_type,
        )
        Event.objects.create(
            title="event1",
            owner=e_user,
            broadcaster=e_broad,
            type=e_type,
            password="mdp",
            iframe_url="http://iframe.live",
            iframe_height=120,
            aside_iframe_url="http://asideiframe.live",
        )
        print("--->  SetUp of EventTestCase: OK!")

    def test_class_methods(self):
        self.assertEqual(get_default_event_type(), 1)
        print(" --->  test_class_methods default_event_type: OK!")

        event = Event.objects.get(id=1)
        defaut_event_start_date = event.start_date
        # careful with 2 check in one
        self.assertEqual(
            present_or_future_date(defaut_event_start_date),
            timezone.now().replace(second=0, microsecond=0),
        )

        yesterday = defaut_event_start_date + timezone.timedelta(days=-1)
        with self.assertRaises(ValidationError):
            present_or_future_date(yesterday)
        print(" --->  test_class_methods present_or_future_date: OK!")

    def test_create(self):
        e_broad = Broadcaster.objects.get(id=1)
        e_user = User.objects.get(id=1)
        e_type = Type.objects.get(id=1)
        event = Event.objects.create(
            title="event2",
            owner=e_user,
            broadcaster=e_broad,
            type=e_type,
        )
        self.assertEqual(2, event.id)
        print(" --->  test_create of EventTestCase: OK!")

    def test_attributs(self):
        event = Event.objects.get(id=1)
        self.assertEqual(event.title, "event1")
        self.assertTrue(event.is_draft)
        self.assertFalse(event.is_restricted)
        self.assertFalse(event.is_auto_start)
        self.assertEqual(event.description, "")
        self.assertEqual(event.password, "mdp")
        # fix models.py before uncomment
        # self.assertTrue(event.is_current())
        # self.assertFalse(event.is_past())
        # self.assertFalse(event.is_coming())
        self.assertEqual(event.videos.count(), 0)
        self.assertEqual(event.restrict_access_to_groups.count(), 0)
        self.assertEqual(event.iframe_url, "http://iframe.live")
        self.assertEqual(event.iframe_height, 120)
        self.assertEqual(event.aside_iframe_url, "http://asideiframe.live")
        self.assertEqual(
            event.__str__(),
            "%s - %s" % ("%04d" % 1, "event1"),
        )
        event.id = None
        self.assertEqual(event.__str__(), "None")
        self.assertEqual(event.get_thumbnail_card(), "/static/img/default-event.svg")
        self.assertEqual(
            event.get_full_url(), "//pod.localhost:8000/live/event/0001-event1/"
        )
        print(" --->  test_attributs of EventTestCase: OK!")

    def test_add_thumbnail(self):
        event = Event.objects.get(id=1)
        if FILEPICKER:
            fp_user, created = User.objects.get_or_create(username="pod")
            homedir, created = UserFolder.objects.get_or_create(
                name="Home", owner=fp_user
            )
            thumb = CustomImageModel.objects.create(
                folder=homedir, created_by=fp_user, file="blabla.jpg"
            )
        else:
            thumb = CustomImageModel.objects.create(file="blabla.jpg")
        event.thumbnail = thumb
        event.save()
        self.assertTrue("blabla" in event.thumbnail.name)
        print(" --->  test_add_thumbnail of EventTestCase: OK!")

    def test_add_video_on_hold(self):
        """Test with a video on hold."""
        video = Video.objects.get(id=1)
        event = Event.objects.get(id=1)
        event.video_on_hold = video
        event.save()
        self.assertEqual(event.video_on_hold.id, video.id)
        print(" --->  test_add_video_on_hold of EventTestCase: OK!")

    def test_add_video(self):
        event = Event.objects.get(id=1)
        event = add_video(event)
        self.assertEqual(event.videos.count(), 1)
        print(" --->  test_add_video of EventTestCase: OK!")

    def test_delete_object(self):
        event = Event.objects.get(id=1)
        event.delete()
        self.assertEqual(Event.objects.all().count(), 0)
        print(" --->  test_delete_object of EventTestCase: OK!")

    def test_delete_object_keep_video(self):
        event = Event.objects.get(id=1)
        add_video(event)
        event.delete()
        # video is not deleted with event
        self.assertEqual(Video.objects.all().count(), 1)
        print(" --->  test_delete_object_keep_video of EventTestCase: OK!")

    def test_event_filters(self):
        user = User.objects.get(username="user1")

        # total Broadcaster
        self.assertEqual(Broadcaster.objects.count(), 4)
        print(" --->  test_filter broadcasters EventTestCase: OK!")

        # available broadcasters for user and building
        filtered_broads = get_available_broadcasters_of_building(user, 1)
        self.assertEqual(filtered_broads.count(), 2)
        print(" --->  test_filtered broadcasters 1 of EventTestCase: OK!")

        # available broadcasters for user and building + the one passed in the param
        filtered_broads = get_available_broadcasters_of_building(user, 1, 3)
        self.assertEqual(filtered_broads.count(), 3)
        print(" --->  test_filtered broadcasters 2 of EventTestCase: OK!")

        # total Building
        self.assertEqual(Building.objects.count(), 2)
        print(" --->  test_filter building EventTestCase: OK!")

        filtered_buildings = get_building_having_available_broadcaster(user)
        self.assertEqual(filtered_buildings.count(), 1)
        print(" --->  test_filtered buildings 2 of EventTestCase: OK!")

        # total plus
        filtered_buildings = get_building_having_available_broadcaster(user, 2)
        self.assertEqual(filtered_buildings.count(), 2)
        print(" --->  test_filtered buildings 2 of EventTestCase: OK!")
