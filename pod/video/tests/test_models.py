"""Video Models test cases."""
from django.test import TestCase
from django.db.models import Count, Q
from django.template.defaultfilters import slugify
from django.db.models.fields.files import ImageFieldFile
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.db import transaction

from ..models import Channel
from ..models import Theme
from ..models import Type
from ..models import Discipline
from ..models import Video
from ..models import ViewCount
from ..models import get_storage_path_video
from ..models import VIDEOS_DIR
from ..models import Notes, AdvancedNotes
from ..models import UserMarkerTime

from pod.video_encode_transcript.models import VideoRendition
from pod.video_encode_transcript.models import EncodingVideo
from pod.video_encode_transcript.models import EncodingAudio
from pod.video_encode_transcript.models import PlaylistVideo
from pod.video_encode_transcript.models import EncodingLog
from pod.video_encode_transcript.models import EncodingStep

from datetime import datetime
from datetime import timedelta

import os

if getattr(settings, "USE_PODFILE", False):
    __FILEPICKER__ = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
else:
    __FILEPICKER__ = False
    from pod.main.models import CustomImageModel


class ChannelTestCase(TestCase):
    """Test the channels."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create Channels to be tested."""
        Channel.objects.create(title="ChannelTest1", slug="blabla")
        Channel.objects.create(
            title="ChannelTest2",
            visible=True,
            color="Black",
            style="italic",
            description="blabla",
        )

        print(" --->  SetUp of ChannelTestCase: OK!")

    def test_Channel_null_attribut(self):
        """
        Test all channel attributs.

        when a channel has been saved with the minimum of attributes
        """
        channel = Channel.objects.annotate(video_count=Count("video", distinct=True)).get(
            title="ChannelTest1"
        )
        self.assertFalse(channel.visible)
        self.assertFalse(channel.slug == slugify("blabla"))
        self.assertEqual(channel.color, None)
        self.assertEqual(channel.description, "")
        if isinstance(channel.headband, ImageFieldFile):
            self.assertEqual(channel.headband.name, "")

        self.assertEqual(channel.style, None)
        self.assertEqual(channel.__str__(), "ChannelTest1")
        self.assertEqual(channel.video_count, 0)
        # self.assertEqual(
        #    channel.get_absolute_url(), "/" + channel.slug + "/")

        print("   --->  test_Channel_null_attribut of ChannelTestCase: OK!")

    def test_Channel_with_attributs(self):
        """Test attributs when a channel has many attributs."""
        channel = Channel.objects.annotate(video_count=Count("video", distinct=True)).get(
            title="ChannelTest2"
        )
        self.assertTrue(channel.visible)
        channel.color = "Blue"
        self.assertEqual(channel.color, "Blue")
        self.assertEqual(channel.description, "blabla")

        self.assertEqual(channel.style, "italic")
        self.assertEqual(channel.__str__(), "ChannelTest2")
        self.assertEqual(channel.video_count, 0)
        # self.assertEqual(
        #    channel.get_absolute_url(), "/" + channel.slug + "/")

        print("   --->  test_Channel_with_attributs of ChannelTestCase: OK!")

    def test_delete_object(self):
        """Test deleting Channels."""
        Channel.objects.get(id=1).delete()
        Channel.objects.get(id=2).delete()
        self.assertEqual(Channel.objects.all().count(), 0)

        print("   --->  test_delete_object of ChannelTestCase: OK!")


class ThemeTestCase(TestCase):
    """Test the theme."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create themes to be tested."""
        Channel.objects.create(title="ChannelTest1")
        Theme.objects.create(
            title="Theme1",
            slug="blabla",
            channel=Channel.objects.get(title="ChannelTest1"),
        )
        Theme.objects.create(
            parentId=Theme.objects.get(title="Theme1"),
            title="Theme2",
            slug="blabla",
            channel=Channel.objects.get(title="ChannelTest1"),
        )
        print(" --->  SetUp of ThemeTestCase: OK!")

    def test_Theme_null_attribut(self):
        """
        Test all attributs.

        when a theme has been saved with the minimum of attributs.
        """
        theme = Theme.objects.annotate(video_count=Count("video", distinct=True)).get(
            title="Theme1"
        )
        self.assertFalse(theme.slug == slugify("blabla"))
        if isinstance(theme.headband, ImageFieldFile):
            self.assertEqual(theme.headband.name, "")
        self.assertEqual(theme.__str__(), "ChannelTest1: Theme1")
        self.assertEqual(theme.video_count, 0)
        self.assertEqual(theme.description, None)
        # self.assertEqual(
        #    theme.get_absolute_url(), "/" + theme.channel.slug + "/"
        #    + theme.slug + "/")
        print("   --->  test_Theme_null_attribut of ThemeTestCase: OK!")

    def test_Theme_with_attributs(self):
        """Test attributs when a theme have many attributs."""
        theme = Theme.objects.get(title="Theme1")
        theme.description = "blabla"
        self.assertEqual(theme.description, "blabla")
        print("   --->  test_Theme_with_attributs of ThemeTestCase: OK!")

    def test_Theme_with_parent(self):
        """Test attributs when a theme have many attributs."""
        theme1 = Theme.objects.get(title="Theme1")
        theme2 = Theme.objects.get(title="Theme2")
        self.assertEqual(theme2.parentId, theme1)
        self.assertIn(theme2, theme1.children.all())
        print("   --->  test_Theme_with_parent of ThemeTestCase: OK!")

    def test_delete_object(self):
        """Test delete object."""
        Theme.objects.get(id=1).delete()
        self.assertEqual(Theme.objects.all().count(), 0)
        print("   --->  test_delete_object of ThemeTestCase: OK!")


class TypeTestCase(TestCase):
    """Test the video type."""

    # fixtures = ['initial_data.json', ]

    def setUp(self):
        """Create types to be tested."""
        Type.objects.create(title="Type1")

        print(" --->  SetUp of TypeTestCase: OK!")

    def test_Type_null_attribut(self):
        """
        Test all attributs.

        when a type have been save with the minimum of attributs.
        """
        type1 = Type.objects.annotate(video_count=Count("video", distinct=True)).get(
            title="Type1"
        )
        self.assertEqual(type1.slug, slugify(type1.title))
        if isinstance(type1.icon, ImageFieldFile):
            self.assertEqual(type1.icon.name, "")
        self.assertEqual(type1.__str__(), "Type1")
        self.assertEqual(type1.video_count, 0)
        self.assertEqual(type1.description, _("-- sorry, no translation provided --"))
        print("   --->  test_Type_null_attribut of TypeTestCase: OK!")

    def test_Type_with_attributs(self):
        """Test attributs when a type have many attributs."""
        type1 = Type.objects.get(title="Type1")
        type1.description = "blabla"
        self.assertEqual(type1.description, "blabla")
        print("   --->  test_Type_with_attributs of TypeTestCase: OK!")

    def test_delete_object(self):
        """Test delete object."""
        Type.objects.get(id=1).delete()
        self.assertEquals(Type.objects.all().count(), 0)
        print("   --->  test_delete_object of TypeTestCase: OK!")


class DisciplineTestCase(TestCase):
    """Test the discipline."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create disciplines to be tested."""
        Discipline.objects.create(title="Discipline1")

        print(" --->  SetUp of DisciplineTestCase: OK!")

    def test_Discipline_null_attribut(self):
        """
        Test all attributs.

        when a type has been save with the minimum of attributs.
        """
        discipline1 = Discipline.objects.annotate(
            video_count=Count("video", distinct=True)
        ).get(title="Discipline1")
        self.assertEqual(discipline1.slug, slugify(discipline1.title))
        if isinstance(discipline1.icon, ImageFieldFile):
            self.assertEqual(discipline1.icon.name, "")
        self.assertEqual(discipline1.__str__(), "Discipline1")
        self.assertEqual(discipline1.video_count, 0)
        self.assertEqual(
            discipline1.description, _("-- sorry, no translation provided --")
        )
        print("   --->  test_Type_null_attribut of TypeTestCase: OK!")

    def test_Discipline_with_attributs(self):
        """Test attributs when a type has many attributs."""
        discipline1 = Discipline.objects.get(title="Discipline1")
        discipline1.description = "blabla"
        self.assertEqual(discipline1.description, "blabla")
        print("   --->  test_Discipline_with_attributs of TypeTestCase: OK!")

    def test_delete_object(self):
        """Test delete object."""
        Discipline.objects.get(id=1).delete()
        self.assertEqual(Discipline.objects.all().count(), 0)
        print("   --->  test_delete_object of TypeTestCase: OK!")


class VideoTestCase(TestCase):
    """Test the Video and ViewCount."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Create videos to be tested."""
        user = User.objects.create(username="pod", password="pod1234pod")

        # Video 1 with minimum attributes
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        type = Type.objects.create(title="autre")
        filename = "test.mp4"
        fname, dot, extension = filename.rpartition(".")

        if __FILEPICKER__:
            homedir, created = UserFolder.objects.get_or_create(name="Home", owner=user)
            thumbnail = CustomImageModel.objects.create(
                folder=homedir, created_by=user, file="blabla.jpg"
            )
        else:
            thumbnail = CustomImageModel.objects.create(file="blabla.jpg")

        # Video 1 with full attributes
        video2 = Video.objects.create(
            type=type,
            title="Video2",
            password=None,
            date_added=datetime.today(),
            encoding_in_progress=False,
            owner=user,
            date_evt=datetime.today(),
            video=os.path.join(
                VIDEOS_DIR,
                user.owner.hashkey,
                "%s.%s" % (slugify(fname), extension),
            ),
            allow_downloading=True,
            description="fl",
            thumbnail=thumbnail,
            is_draft=False,
            duration=3,
        )

        ViewCount.objects.create(video=video2, date=datetime.today(), count=1)
        tomorrow = datetime.today() + timedelta(days=1)
        ViewCount.objects.create(video=video2, date=tomorrow, count=2)
        print(" --->  SetUp of VideoTestCase: OK!")

    def test_last_Video_display(self):
        filter_en = Video.objects.filter(encoding_in_progress=False, is_draft=False)
        filter_pass = filter_en.filter(
            Q(password="") | Q(password=None), is_restricted=False
        )
        self.assertFalse(bool(filter_pass.filter(password="toto")))
        self.assertFalse(bool(filter_pass.filter(password="")))
        self.assertTrue(bool(filter_pass.filter(password__isnull=True)))
        print("--->  test_last_Video_display of VideoTestCase: OK")

    def test_Video_null_attributs(self):
        video = Video.objects.get(id=1)
        self.assertEqual(video.video.name, "test.mp4")
        self.assertFalse(video.allow_downloading)
        self.assertEqual(video.description, "")
        self.assertEqual(video.slug, "%04d-%s" % (video.id, slugify(video.title)))
        date = datetime.today()
        self.assertEqual(video.owner, User.objects.get(username="pod"))
        self.assertEqual(video.date_added.year, date.year)
        self.assertEqual(video.date_added.month, date.month)
        self.assertEqual(video.date_added.day, date.day)
        # self.assertEqual(video.date_evt, video.date_added)
        self.assertEqual(video.get_viewcount(), 0)

        self.assertTrue(video.is_draft)

        if isinstance(video.thumbnail, ImageFieldFile):
            self.assertEqual(video.thumbnail.name, "")

        self.assertEqual(video.duration, 0)
        # self.assertEqual(pod.get_absolute_url(), "/video/" + pod.slug + "/")
        self.assertEqual(video.__str__(), "%s - %s" % ("%04d" % video.id, video.title))

        print("   --->  test_Video_null_attributs of VideoTestCase: OK!")

    def test_Video_many_attributs(self):
        video2 = Video.objects.get(id=2)
        self.assertEqual(video2.video.name, get_storage_path_video(video2, "test.mp4"))
        self.assertTrue(video2.allow_downloading)
        self.assertEqual(video2.description, "fl")
        self.assertEqual(video2.get_viewcount(), 3)
        self.assertEqual(
            ViewCount.objects.get(video=video2, date=datetime.today()).count, 1
        )
        self.assertTrue(video2.allow_downloading)
        self.assertFalse(video2.is_draft)
        self.assertEqual(video2.duration, 3)
        self.assertEqual(video2.video.__str__(), video2.video.name)

        print("   --->  test_Video_many_attributs of VideoTestCase: OK!")

    def test_delete_object(self):
        """Test deleting videos objects."""
        for vid_id in [1, 2]:
            vid_object = Video.objects.get(id=vid_id)
            vid_object.delete()

        # Check that all videos are properly deleted.
        self.assertEqual(Video.objects.all().count(), 0)

        # Check delete view count cascade
        self.assertEqual(ViewCount.objects.all().count(), 0)

        print("   --->  test_delete_object of Video: OK!")


class VideoRenditionTestCase(TestCase):
    """Test the Video Rendition."""

    # fixtures = ['initial_data.json', ]

    def create_video_rendition(
        self,
        resolution="640x360",
        minrate="500k",
        video_bitrate="1000k",
        maxrate="2000k",
        audio_bitrate="300k",
        encode_mp4=False,
    ):
        # print("create_video_rendition: %s" % resolution)
        return VideoRendition.objects.create(
            resolution=resolution,
            minrate=minrate,
            video_bitrate=video_bitrate,
            maxrate=maxrate,
            audio_bitrate=audio_bitrate,
            encode_mp4=encode_mp4,
        )

    def test_VideoRendition_creation_by_default(self):
        vr = self.create_video_rendition()
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(
            vr.__str__(),
            "VideoRendition num %s with resolution %s" % ("%04d" % vr.id, vr.resolution),
        )
        vr.clean()
        print(
            " --->  test_VideoRendition_creation_by_default of \
            VideoRenditionTestCase: OK!"
        )

    def test_VideoRendition_creation_with_values(self):
        # print("check resolution error")
        vr = self.create_video_rendition(resolution="totototo")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(
            vr.__str__(),
            "VideoRendition num %s with resolution %s" % ("%04d" % vr.id, vr.resolution),
        )
        self.assertRaises(ValidationError, vr.clean)
        vr = self.create_video_rendition(resolution="totoxtoto")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(
            vr.__str__(),
            "VideoRendition num %s with resolution %s" % ("%04d" % vr.id, vr.resolution),
        )
        self.assertRaises(ValidationError, vr.clean)
        print("check video bitrate error")
        vr = self.create_video_rendition(resolution="640x361", video_bitrate="dfk")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(
            vr.__str__(),
            "VideoRendition num %s with resolution %s" % ("%04d" % vr.id, vr.resolution),
        )
        self.assertRaises(ValidationError, vr.clean)
        vr = self.create_video_rendition(resolution="640x362", video_bitrate="100")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(
            vr.__str__(),
            "VideoRendition num %s with resolution %s" % ("%04d" % vr.id, vr.resolution),
        )
        self.assertRaises(ValidationError, vr.clean)
        print("check audio bitrate error")
        vr = self.create_video_rendition(resolution="640x363", audio_bitrate="dfk")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(
            vr.__str__(),
            "VideoRendition num %s with resolution %s" % ("%04d" % vr.id, vr.resolution),
        )
        self.assertRaises(ValidationError, vr.clean)
        vr = self.create_video_rendition(resolution="640x364", audio_bitrate="100")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(
            vr.__str__(),
            "VideoRendition num %s with resolution %s" % ("%04d" % vr.id, vr.resolution),
        )
        self.assertRaises(ValidationError, vr.clean)
        print(
            " --->  test_VideoRendition_creation_with_values of \
            VideoRenditionTestCase: OK!"
        )

    def test_delete_object(self):
        self.create_video_rendition(resolution="640x365")
        VideoRendition.objects.get(id=1).delete()
        self.assertEqual(VideoRendition.objects.all().count(), 0)

        print("   --->  test_delete_object of VideoRenditionTestCase: OK!")


class EncodingVideoTestCase(TestCase):
    """Test the Video Encoding model."""

    # fixtures = ['initial_data.json', ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        Type.objects.create(title="test")
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        VideoRendition.objects.create(
            resolution="640x360",
            video_bitrate="1000k",
            audio_bitrate="300k",
            encode_mp4=False,
        )
        print(" --->  SetUp of EncodingVideoTestCase: OK!")

    def test_EncodingVideo_null_attributs(self):
        ev = EncodingVideo.objects.create(
            video=Video.objects.get(id=1),
            rendition=VideoRendition.objects.get(resolution="640x360"),
        )
        self.assertTrue(isinstance(ev, EncodingVideo))
        evslug = "EncodingVideo num: %s with resolution %s " % (
            "%04d" % ev.id,
            ev.name,
        )
        evslug += "for video %s in %s" % (ev.video.id, ev.encoding_format)
        self.assertEqual(ev.__str__(), evslug)
        self.assertEqual(ev.name, "360p")
        self.assertEqual(ev.encoding_format, "video/mp4")
        self.assertEqual(ev.owner, Video.objects.get(id=1).owner)
        ev.clean()
        print(" --->  SetUp of test_EncodingVideo_null_attributs: OK!")

    def test_EncodingVideo_with_attributs(self):
        ev = EncodingVideo.objects.create(
            video=Video.objects.get(id=1),
            rendition=VideoRendition.objects.get(resolution="640x360"),
            name="480p",
            encoding_format="audio/mp3",
        )
        self.assertTrue(isinstance(ev, EncodingVideo))
        evslug = "EncodingVideo num: %s with resolution %s " % (
            "%04d" % ev.id,
            ev.name,
        )
        evslug += "for video %s in %s" % (ev.video.id, ev.encoding_format)
        self.assertEqual(ev.__str__(), evslug)
        self.assertEqual(ev.name, "480p")
        self.assertEqual(ev.encoding_format, "audio/mp3")
        self.assertEqual(ev.owner, Video.objects.get(id=1).owner)
        ev.clean()
        print(" --->  SetUp of test_EncodingVideo_with_attributs: OK!")

    def test_EncodingVideo_with_false_attributs(self):
        ev = EncodingVideo.objects.create(
            video=Video.objects.get(id=1),
            rendition=VideoRendition.objects.get(resolution="640x360"),
            name="error",
            encoding_format="error",
        )
        self.assertTrue(isinstance(ev, EncodingVideo))
        self.assertEqual(ev.name, "error")
        self.assertRaises(ValidationError, ev.clean)
        print(" --->  SetUp of test_EncodingVideo_with_false_attributs: OK!")

    def test_delete_object(self):
        EncodingVideo.objects.create(
            video=Video.objects.get(id=1),
            rendition=VideoRendition.objects.get(resolution="640x360"),
        )
        EncodingVideo.objects.get(id=1).delete()
        self.assertEqual(EncodingVideo.objects.all().count(), 0)

        print("   --->  test_delete_object of EncodingVideoTestCase: OK!")


class EncodingAudioTestCase(TestCase):
    """Test the Audio Encoding model."""

    # fixtures = ['initial_data.json', ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        Type.objects.create(title="test")
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        print(" --->  SetUp of EncodingAudioTestCase: OK!")

    def test_EncodingVideo_null_attributs(self):
        ea = EncodingAudio.objects.create(video=Video.objects.get(id=1))
        self.assertTrue(isinstance(ea, EncodingAudio))
        easlug = "EncodingAudio num: %s for video %s in %s" % (
            "%04d" % ea.id,
            ea.video.id,
            ea.encoding_format,
        )
        self.assertEqual(ea.__str__(), easlug)
        self.assertEqual(ea.name, "audio")
        self.assertEqual(ea.encoding_format, "audio/mp3")
        self.assertEqual(ea.owner, Video.objects.get(id=1).owner)
        ea.clean()
        print(" --->  test_EncodingVideo_null_attributs: OK!")

    def test_EncodingAudio_with_attributs(self):
        ea = EncodingAudio.objects.create(
            video=Video.objects.get(id=1),
            name="audio",
            encoding_format="video/mp4",
        )
        self.assertTrue(isinstance(ea, EncodingAudio))
        easlug = "EncodingAudio num: %s for video %s in %s" % (
            "%04d" % ea.id,
            ea.video.id,
            ea.encoding_format,
        )
        self.assertEqual(ea.__str__(), easlug)
        self.assertEqual(ea.name, "audio")
        self.assertEqual(ea.encoding_format, "video/mp4")
        self.assertEqual(ea.owner, Video.objects.get(id=1).owner)
        ea.clean()
        print(" --->  test_EncodingAudio_with_attributs: OK!")

    def test_EncodingAudio_with_false_attributs(self):
        ea = EncodingAudio.objects.create(
            video=Video.objects.get(id=1), name="error", encoding_format="error"
        )
        self.assertTrue(isinstance(ea, EncodingAudio))
        self.assertEqual(ea.name, "error")
        self.assertRaises(ValidationError, ea.clean)
        print(" --->  test_EncodingAudio_with_false_attributs: OK!")

    def test_delete_object(self):
        EncodingAudio.objects.create(video=Video.objects.get(id=1))
        EncodingAudio.objects.get(id=1).delete()
        self.assertEqual(EncodingAudio.objects.all().count(), 0)

        print("   --->  test_delete_object of EncodingAudioTestCase: OK!")


class PlaylistVideoTestCase(TestCase):
    """Test the PlaylistVideo model."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        print(" --->  SetUp of PlaylistVideoTestCase: OK!")

    def test_PlaylistVideo_null_attributs(self):
        pv = PlaylistVideo.objects.create(video=Video.objects.get(id=1))
        self.assertTrue(isinstance(pv, PlaylistVideo))
        pvslug = "Playlist num: %s for video %s in %s" % (
            "%04d" % pv.id,
            pv.video.id,
            pv.encoding_format,
        )
        self.assertEqual(pv.__str__(), pvslug)
        self.assertEqual(pv.name, "360p")
        self.assertEqual(pv.encoding_format, "application/x-mpegURL")
        self.assertEqual(pv.owner, Video.objects.get(id=1).owner)
        pv.clean()
        print(" --->  test_PlaylistVideo_null_attributs: OK!")

    def test_PlaylistVideo_with_attributs(self):
        pv = PlaylistVideo.objects.create(
            video=Video.objects.get(id=1),
            name="audio",
            encoding_format="video/mp4",
        )
        self.assertTrue(isinstance(pv, PlaylistVideo))
        pvslug = "Playlist num: %s for video %s in %s" % (
            "%04d" % pv.id,
            pv.video.id,
            pv.encoding_format,
        )
        self.assertEqual(pv.__str__(), pvslug)
        self.assertEqual(pv.name, "audio")
        self.assertEqual(pv.encoding_format, "video/mp4")
        self.assertEqual(pv.owner, Video.objects.get(id=1).owner)
        pv.clean()
        print(" --->  test_PlaylistVideo_with_attributs: OK!")

    def test_PlaylistVideo_with_false_attributs(self):
        pv = PlaylistVideo.objects.create(
            video=Video.objects.get(id=1), name="error", encoding_format="error"
        )
        self.assertTrue(isinstance(pv, PlaylistVideo))
        self.assertEqual(pv.name, "error")
        self.assertRaises(ValidationError, pv.clean)
        print(" --->  test_PlaylistVideo_with_false_attributs: OK!")

    def test_delete_object(self):
        PlaylistVideo.objects.create(video=Video.objects.get(id=1))
        PlaylistVideo.objects.get(id=1).delete()
        self.assertEqual(PlaylistVideo.objects.all().count(), 0)

        print("   --->  test_delete_object of PlaylistVideoTestCase: OK!")


class EncodingLogTestCase(TestCase):
    """Test the EncodingLog model."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        print(" --->  SetUp of EncodingLogTestCase: OK!")

    def test_EncodingLogTestCase_null_attributs(self):
        el = EncodingLog.objects.create(video=Video.objects.get(id=1))
        self.assertTrue(isinstance(el, EncodingLog))
        elslug = "Log for encoding video %s" % (el.video.id)
        self.assertEqual(el.__str__(), elslug)
        self.assertEqual(el.log, None)
        print(" --->  test_EncodingLogTestCase_null_attributs: OK!")

    def test_EncodingLogTestCase_with_attributs(self):
        el = EncodingLog.objects.create(video=Video.objects.get(id=1), log="encoding log")
        self.assertTrue(isinstance(el, EncodingLog))
        elslug = "Log for encoding video %s" % (el.video.id)
        self.assertEqual(el.__str__(), elslug)
        self.assertEqual(el.log, "encoding log")
        print(" --->  test_EncodingLogTestCase_with_attributs: OK!")

    def test_delete_object(self):
        EncodingLog.objects.create(video=Video.objects.get(id=1))
        EncodingLog.objects.get(id=1).delete()
        self.assertEqual(EncodingLog.objects.all().count(), 0)

        print("   --->  test_delete_object of EncodingLogTestCase: OK!")


class EncodingStepTestCase(TestCase):
    """Test the EncodingStep model."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        print(" --->  SetUp of EncodingLogTestCase: OK!")

    def test_EncodingStepTestCase_null_attributs(self):
        es = EncodingStep.objects.create(video=Video.objects.get(id=1))
        self.assertTrue(isinstance(es, EncodingStep))
        esslug = "Step for encoding video %s" % (es.video.id)
        self.assertEqual(es.__str__(), esslug)
        self.assertEqual(es.num_step, 0)
        self.assertEqual(es.desc_step, None)
        print(" --->  test_EncodingStepTestCase_null_attributs: OK!")

    def test_EncodingStepTestCase_with_attributs(self):
        es = EncodingStep.objects.create(
            video=Video.objects.get(id=1),
            num_step=1,
            desc_step="encoding step",
        )
        self.assertTrue(isinstance(es, EncodingStep))
        esslug = "Step for encoding video %s" % (es.video.id)
        self.assertEqual(es.__str__(), esslug)
        self.assertEqual(es.num_step, 1)
        self.assertEqual(es.desc_step, "encoding step")
        print(" --->  test_EncodingStepTestCase_with_attributs: OK!")

    def test_delete_object(self):
        EncodingStep.objects.create(video=Video.objects.get(id=1))
        EncodingStep.objects.get(id=1).delete()
        self.assertEqual(EncodingStep.objects.all().count(), 0)

        print("   --->  test_delete_object of EncodingStepTestCase: OK!")


class NotesTestCase(TestCase):
    """Test the Note model."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        print(" --->  SetUp of EncodingLogTestCase: OK!")

    def test_NotesTestCase_null_attributs(self):
        note = Notes.objects.create(
            user=User.objects.get(username="pod"), video=Video.objects.get(id=1)
        )
        advnote = AdvancedNotes.objects.create(
            user=User.objects.get(username="pod"), video=Video.objects.get(id=1)
        )
        self.assertTrue(isinstance(note, Notes))
        self.assertTrue(isinstance(advnote, AdvancedNotes))
        self.assertEqual(note.__str__(), "%s-%s" % (note.user.username, note.video))
        self.assertEqual(
            advnote.__str__(),
            "%s-%s-%s" % (advnote.user.username, advnote.video, advnote.timestamp),
        )
        self.assertEqual(note.note, None)
        self.assertEqual(advnote.note, None)
        self.assertEqual(advnote.timestamp, None)
        self.assertEqual(advnote.status, "0")
        print(" --->  test_NotesTestCase_null_attributs: OK!")

    def test_NotesTestCase_with_attributs(self):
        note = Notes.objects.create(
            user=User.objects.get(username="pod"),
            video=Video.objects.get(id=1),
            note="coucou",
        )
        advnote = AdvancedNotes.objects.create(
            user=User.objects.get(username="pod"),
            video=Video.objects.get(id=1),
            note="coucou",
            timestamp=0,
            status="1",
        )
        self.assertTrue(isinstance(note, Notes))
        self.assertTrue(isinstance(advnote, AdvancedNotes))
        self.assertEqual(note.__str__(), "%s-%s" % (note.user.username, note.video))
        self.assertEqual(
            advnote.__str__(),
            "%s-%s-%s" % (advnote.user.username, advnote.video, advnote.timestamp),
        )
        self.assertEqual(note.note, "coucou")
        self.assertEqual(advnote.note, "coucou")
        self.assertEqual(advnote.timestamp, 0)
        self.assertEqual(advnote.status, "1")
        print(" --->  test_NotesTestCase_with_attributs: OK!")

    def test_delete_object(self):
        Notes.objects.create(
            user=User.objects.get(username="pod"), video=Video.objects.get(id=1)
        )
        AdvancedNotes.objects.create(
            user=User.objects.get(username="pod"), video=Video.objects.get(id=1)
        )
        Notes.objects.get(id=1).delete()
        AdvancedNotes.objects.get(id=1).delete()
        self.assertEqual(Notes.objects.all().count(), 0)
        self.assertEqual(AdvancedNotes.objects.all().count(), 0)

        print("   --->  test_delete_object of NotesTestCase: OK!")


class UserMarkerTimeTestCase(TestCase):
    """Test the UserMarkerTime model."""
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        print(" --->  SetUp of UserMarkerTimeTestCase: OK!")

    def test_create_UserMarkerTime_default(self):
        user = User.objects.get(username="pod")
        video = Video.objects.get(id=1)
        markerTime = UserMarkerTime.objects.create(video=video, user=user)
        self.assertTrue(isinstance(markerTime, UserMarkerTime))
        self.assertEqual(UserMarkerTime.objects.all().count(), 1)
        self.assertEqual(markerTime.markerTime, 0)
        print(" ---> test_create_UserMarkerTime_default: OK!")

    def test_create_UserMarkerTime_with_attribut(self):
        user = User.objects.get(username="pod")
        video = Video.objects.get(id=1)
        markerTime = UserMarkerTime(video=video, user=user, markerTime=60)
        markerTime.save()
        self.assertTrue(isinstance(markerTime, UserMarkerTime))
        self.assertEqual(UserMarkerTime.objects.all().count(), 1)
        self.assertEqual(markerTime.user, user)
        self.assertEqual(markerTime.video, video)
        self.assertEqual(markerTime.markerTime, 60)
        print(" ---> test_create_UserMarkerTime_with_attribut: OK!")

    def test_create_UserMarkerTime_already_exist(self):
        user = User.objects.get(username="pod")
        video = Video.objects.get(id=1)
        UserMarkerTime.objects.create(video=video, user=user)
        newMarkerTime = UserMarkerTime(video=video, user=user)
        try:
            with transaction.atomic():
                newMarkerTime.save()
            self.fail('Duplicate marker allowed.')
        except IntegrityError:
            pass
        self.assertEqual(UserMarkerTime.objects.all().count(), 1)
        print(" ---> test_create_UserMarkerTime_already_exist: OK!")

    def test_modify_UserMarkerTime(self):
        user = User.objects.get(username="pod")
        video = Video.objects.get(id=1)
        markerTime = UserMarkerTime(video=video, user=user, markerTime=60)
        markerTime.save()
        self.assertEqual(markerTime.markerTime, 60)
        markerTime.markerTime = 120
        markerTime.save()
        markerTime.refresh_from_db()
        self.assertEqual(markerTime.markerTime, 120)
        print(" ---> test_modify_UserMarkerTime: OK!")

    def test_delete_UserMarkerTime(self):
        user = User.objects.get(username="pod")
        video = Video.objects.get(id=1)
        markerTime = UserMarkerTime(video=video, user=user, markerTime=60)
        markerTime.save()
        self.assertEqual(UserMarkerTime.objects.all().count(), 1)
        markerTime.delete()
        self.assertEqual(UserMarkerTime.objects.all().count(), 0)
        print(" ---> test_delete_UserMarkerTime: OK!")
