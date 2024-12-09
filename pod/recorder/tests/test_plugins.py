"""Unit test for Pod recorder plugins.

*  run with 'python manage.py test pod.recorder.tests.test_plugins'
"""

import os
import shutil
import importlib
from defusedxml import minidom

from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from pod.video.models import Video, Type
from ..models import Recording, Recorder
from ...live.models import Event, Building, Broadcaster
from ...main.settings import BASE_DIR

VIDEO_TEST = getattr(settings, "VIDEO_TEST", "pod/main/static/video_test/pod.mp4")

AUDIOVIDEOCAST_TEST = getattr(
    settings, "AUDIOVIDEOCAST_TEST", "pod/main/static/video_test/pod.zip"
)


class PluginVideoTestCase(TestCase):
    """Test case for video plugin."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        mediatype = Type.objects.create(title="others")
        Type.objects.create(title="second")
        user = User.objects.create(username="pod", is_staff=True)
        # Setup recorder and recording for Video
        recorder1 = Recorder.objects.create(
            user=user,
            name="recorder1",
            address_ip="16.3.10.47",
            type=mediatype,
            cursus="0",
            directory="dirVideo",
        )
        source_file1 = os.path.join(settings.MEDIA_ROOT, os.path.basename(VIDEO_TEST))
        Recording.objects.create(
            id=1,
            user=user,
            title="media1",
            type="video",
            source_file=source_file1,
            recorder=recorder1,
        )
        # Setup recorder and recording for AudioVideoCast
        recorder2 = Recorder.objects.create(
            user=user,
            name="recorder2",
            address_ip="16.3.10.48",
            type=mediatype,
            cursus="0",
            directory="dirAudioVideoCast",
        )
        source_file2 = os.path.join(
            settings.MEDIA_ROOT, os.path.basename(AUDIOVIDEOCAST_TEST)
        )
        Recording.objects.create(
            id=2,
            user=user,
            title="media2",
            type="audiovideocast",
            source_file=source_file2,
            recorder=recorder2,
        )

        print(" --->  SetUp of PluginVideoTestCase: OK!")

    def test_type_video_published_attributs(self) -> None:
        recording = Recording.objects.get(id=1)
        recorder = recording.recorder
        shutil.copyfile(VIDEO_TEST, recording.source_file)
        mod = importlib.import_module("pod.recorder.plugins.type_%s" % ("video"))
        nbnow = Video.objects.all().count()
        nbtest = nbnow + 1
        mod.encode_recording(recording)
        # print("Number of video after encode: ", Video.objects.all().count())
        self.assertEqual(Video.objects.all().count(), nbtest)
        video = Video.objects.last()
        self.assertEqual(video.is_draft, recorder.is_draft)
        self.assertEqual(video.channel.all().count(), recorder.channel.all().count())
        self.assertEqual(video.theme.all().count(), recorder.theme.all().count())
        self.assertEqual(
            video.discipline.all().count(), recorder.discipline.all().count()
        )
        self.assertEqual(video.main_lang, recorder.main_lang)
        self.assertEqual(video.cursus, recorder.cursus)
        self.assertEqual(video.tags, recorder.tags)

        print("   --->  test_type_video_published_attributs of PluginVideoTestCase: OK!")

    def test_type_audiovideocast_published_attributs(self) -> None:
        recording = Recording.objects.get(id=2)
        recorder = recording.recorder
        shutil.copyfile(AUDIOVIDEOCAST_TEST, recording.source_file)
        mod = importlib.import_module("pod.recorder.plugins.type_%s" % "audiovideocast")
        nbnow = Video.objects.all().count()
        nbtest = nbnow + 1
        mod.encode_recording(recording)
        # print("Number of video after encode: ", Video.objects.all().count())
        self.assertEqual(Video.objects.all().count(), nbtest)
        video = Video.objects.last()
        # print("Number of slide after encode: ",
        #       video.enrichment_set.all().count())
        self.assertEqual((video.enrichment_set.all().count() > 0), True)
        self.assertEqual(video.is_draft, recorder.is_draft)
        self.assertEqual(video.channel.all().count(), recorder.channel.all().count())
        self.assertEqual(video.theme.all().count(), recorder.theme.all().count())
        self.assertEqual(
            video.discipline.all().count(), recorder.discipline.all().count()
        )
        self.assertEqual(video.main_lang, recorder.main_lang)
        self.assertEqual(video.cursus, recorder.cursus)
        self.assertEqual(video.tags, recorder.tags)
        print(
            "   --->  test_type_video_published_attributs "
            "of PluginAudioVideoCastTestCase: OK!"
        )

    def test_change_title(self) -> None:
        """Test method change_title."""
        from ..plugins.type_studio import change_title

        recording = Recording.objects.get(id=1)
        title = "A new title"
        self.assertNotEqual(recording.title, title)

        change_title(recording, title)
        recording = Recording.objects.get(id=1)
        self.assertEqual(recording.title, title)
        print("   --->  test_change_title of PluginVideoTestCase: OK!")

    def test_change_user(self) -> None:
        """Test method change_user."""
        from ..plugins.type_studio import change_user

        recording = Recording.objects.get(id=1)
        user2 = User.objects.create(username="another_user", is_staff=True)
        self.assertNotEqual(recording.user, user2)

        change_user(recording, user2.username)
        recording = Recording.objects.get(id=1)
        self.assertEqual(recording.user, user2)
        print("   --->  test_change_user of PluginVideoTestCase: OK!")

    def test_link_video_to_event(self) -> None:
        """Test method link_video_to_event."""
        from ..plugins.type_studio import link_video_to_event

        user_pod = User.objects.filter(id=1).first()
        recording = Recording.objects.get(id=1)
        video = Video.objects.create(
            title="video",
            owner=user_pod,
            video="test.mp4",
            type=Type.objects.get(id=1),
            is_restricted=True,
            is_draft=False,
            password="pod1234pod",
        )
        building = Building.objects.create(name="building1")
        broadcaster = Broadcaster.objects.create(
            name="broadcaster1",
            building=building,
        )
        user2 = User.objects.create(username="another_user", is_staff=True)
        event_draft = Event.objects.create(
            title="event1",
            owner=user2,
            is_draft=True,
            type=Type.objects.get(id=2),
            broadcaster=broadcaster,
            description="random desc",
        )
        event_not_draft = Event.objects.create(
            title="event2",
            owner=user2,
            is_draft=False,
            type=Type.objects.get(id=2),
            broadcaster=broadcaster,
            description="event_draft desc",
        )

        self.assertTrue(event_draft.videos.count() == 0)
        self.assertNotIn(event_draft.owner, video.additional_owners.all())

        self.assertNotEqual(event_draft.description, video.description)
        self.assertNotEqual(event_draft.is_draft, video.is_draft)
        self.assertNotEqual(event_draft.type, video.type)

        # Call the method
        link_video_to_event(recording, video, event_draft.id)

        self.assertEqual(event_draft.description, video.description)
        self.assertEqual(event_draft.is_draft, video.is_draft)
        self.assertEqual(event_draft.type, video.type)
        self.assertIsNone(video.password)
        self.assertFalse(video.is_restricted)
        self.assertEqual(video.restrict_access_to_groups.count(), 0)

        # Test the association
        self.assertTrue(event_draft.videos.count() == 1)

        # Test Video additional users contains Event's owner
        self.assertIn(event_draft.owner, video.additional_owners.all())

        # Test persistence in db
        event_from_db = Event.objects.get(id=1)
        self.assertTrue(event_from_db.videos.count() == 1)

        video_from_db = Video.objects.get(id=video.id)
        self.assertIn(event_from_db.owner, video_from_db.additional_owners.all())

        # With not draft event
        link_video_to_event(recording, video, event_not_draft.id)
        self.assertEqual(event_not_draft.is_draft, video.is_draft)
        self.assertEqual(event_not_draft.is_restricted, video.is_restricted)

        print("   --->  test_link_video_to_event of PluginVideoTestCase: OK!")

    def test_get_attribute_by_name(self) -> None:
        """Test method getAttributeByName."""
        from ..plugins.type_studio import getAttributeByName

        xml_content = (
            '<?xml version="1.0" encoding="UTF-8"?><root>'
            '<mytag id="1" name="with letter e" />'
            '<mytag id="2" name="never retrieve" />'
            "</root>"
        )

        xml_doc = minidom.parseString(xml_content)

        # Test case 1: Retrieve the attribute 'id' from the first element with tag name
        id_attribute = getAttributeByName(xml_doc, "mytag", "id")
        self.assertEqual(id_attribute, "1")

        # Test case 2: Test the exclusion of value containing the letter 'e'
        excluded_attribute = getAttributeByName(xml_doc, "mytag", "name")
        self.assertIsNone(excluded_attribute)

        # Test case 3: Non-existing tag name 'nonexistent'
        non_existing_attribute = getAttributeByName(xml_doc, "nonexistent", "id")
        self.assertIsNone(non_existing_attribute)

        # Test case 4: Non-existing attribute from the first element
        non_existing_attribute_2 = getAttributeByName(xml_doc, "mytag", "nonexistent")
        self.assertIsNone(non_existing_attribute_2)
        print("   --->  test_get_attribute_by_name of PluginVideoTestCase: OK!")

    def test_get_elements_by_name(self) -> None:
        """Test method getElementsByName."""
        from ..plugins.type_studio import getElementsByName

        __MEDIA_TMP_FOLDER__ = os.path.join("media", "test_plugins")
        __MEDIA_TMP_PATH__ = os.path.join(BASE_DIR, __MEDIA_TMP_FOLDER__)
        image_url = os.path.join(__MEDIA_TMP_FOLDER__, "image.jpg")
        video_url = os.path.join(__MEDIA_TMP_FOLDER__, "video.mp4")

        # Test case 1: xml document without the expected tag
        xml_content = '<?xml version="1.0" encoding="UTF-8"?><root><data type="empty"></data></root>'
        parsed = minidom.parseString(xml_content)
        elements = getElementsByName(parsed, "element")
        self.assertEqual(elements, [])

        # Create directory and sample files
        os.makedirs(__MEDIA_TMP_PATH__)
        with open(os.path.join(BASE_DIR, image_url), "w") as image_file:
            image_file.write("Sample image content")

        with open(os.path.join(BASE_DIR, video_url), "w") as video_file:
            video_file.write("Sample video content")

        # Test case 2: xml document with expected tags
        xml_content = (
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f"<root>"
            f'<mytag type="image"><url>/{image_url}</url></mytag>'
            f'<mytag type="video"><url>/{video_url}</url></mytag>'
            f"</root>"
        )
        parsed = minidom.parseString(xml_content)

        # Gets elements
        elements = getElementsByName(parsed, "mytag")

        # Remove directory and sample files before test ends
        os.remove(os.path.join(BASE_DIR, image_url))
        os.remove(os.path.join(BASE_DIR, video_url))
        os.removedirs(__MEDIA_TMP_PATH__)

        expected_elements = [
            {"type": "image", "src": os.path.join(BASE_DIR, image_url)},
            {"type": "video", "src": os.path.join(BASE_DIR, video_url)},
        ]

        self.assertEqual(elements, expected_elements)
        print("   --->  test_get_elements_by_name of PluginVideoTestCase: OK!")

    def test_getElementValueByName(self) -> None:
        """Test method getElementValueByName."""
        from ..plugins.type_studio import getElementValueByName

        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<myNode xmlns="http://www.opencastproject.org/xsd/1.0/dublincore/" '
            'xmlns:dcterms="http://purl.org/dc/terms/">'
            "<dcterms:title>test</dcterms:title>"
            "<dcterms:creator>randomuser</dcterms:creator>"
            "</myNode>"
        )
        parsed = minidom.parseString(xml)
        self.assertEqual("", getElementValueByName(parsed, "myNode"))
        self.assertEqual("randomuser", getElementValueByName(parsed, "dcterms:creator"))
        self.assertEqual("", getElementValueByName(parsed, "notexisting"))
        print("   --->  test_getElementValueByName of PluginVideoTestCase: OK!")
