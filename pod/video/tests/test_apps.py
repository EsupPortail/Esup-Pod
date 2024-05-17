"""Unit tests for Esup-Pod video apps.

test with `python manage.py test pod.video.tests.test_apps`
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist

from pod.video.models import Channel, Theme, Video, Type, Discipline
from pod.video_encode_transcript.models import VideoRendition
from pod.video.apps import set_default_site, update_video_passwords

# ggignore-start
# gitguardian:ignore
PWD = "azerty1234"  # nosec
# ggignore-end


class VideoTestApps(TestCase):
    """TestCase for Esup-Pod video apps."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self) -> None:
        """Set up required objects for next tests."""
        self.user = User.objects.create(username="pod", password=PWD)  # nosem
        self.chan = Channel.objects.create(title="ChannelTest1")
        self.theme = Theme.objects.create(
            title="Theme1", slug="blabla", channel=self.chan
        )
        self.disc = Discipline.objects.create(title="Discipline1")
        self.type = Type.objects.get(id=1)
        self.vr = VideoRendition.objects.get(id=1)
        self.vid = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            password=PWD,  # nosem
            type=Type.objects.get(id=1),
        )
        print("\n --->  SetUp of VideoTestApps: OK!")

    def test_set_default_site(self) -> None:
        """Test the set_default_site function."""
        cur_site = Site.objects.get_current()
        multi_sites = [self.vid, self.type, self.vr]
        single_site = [self.chan, self.disc]

        for obj in multi_sites:
            obj.sites.remove(cur_site)
            self.assertNotIn(cur_site, obj.sites.all())
        for obj in single_site:
            obj.site = None
            obj.save()
            obj.site
            self.assertRaises(ObjectDoesNotExist)

        set_default_site(self)

        for obj in multi_sites:
            self.assertIn(cur_site, obj.sites.all())
        for obj in single_site:
            self.assertEqual(cur_site, obj.site)

        print("   --->  test_set_default_site of VideoTestApps: OK!")

    def test_update_video_passwords(self) -> None:
        """Test the update_video_passwords function."""
        self.assertNotIn("pbkdf2_sha256$", self.vid.password)

        update_video_passwords(self)
        self.vid = Video.objects.get(id=1)

        self.assertIn("pbkdf2_sha256$", self.vid.password)
