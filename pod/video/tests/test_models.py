from django.test import TestCase
from django.test import override_settings
from django.db.models import Count
from django.template.defaultfilters import slugify
from django.db.models.fields.files import ImageFieldFile
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError

from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline
try:
    from pod.authentication.models import Owner
except ImportError:
    from django.contrib.auth.models import User as Owner
from pod.video.models import Video
from pod.video.models import ViewCount
from pod.video.models import get_storage_path_video
from pod.video.models import VIDEOS_DIR
from pod.video.models import VideoRendition
from pod.video.models import EncodingVideo

from datetime import datetime
from datetime import timedelta

import os

# Create your tests here.
"""
    test the channel
"""


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    }
)
class ChannelTestCase(TestCase):

    def setUp(self):
        Channel.objects.create(title="ChannelTest1", slug="blabla")
        Channel.objects.create(title="ChannelTest2", visible=True,
                               color="Black", style="italic",
                               description="blabla")

        print(" --->  SetUp of ChannelTestCase : OK !")

    """
        test all attributs when a channel have been save with the minimum of
        attributs
    """

    def test_Channel_null_attribut(self):
        channel = Channel.objects.annotate(video_count=Count(
            "video", distinct=True)).get(title="ChannelTest1")
        self.assertEqual(channel.visible, False)
        self.assertFalse(channel.slug == slugify("blabla"))
        self.assertEqual(channel.color, None)
        self.assertEqual(
            channel.description,
            _('-- sorry, no translation provided --')
        )
        if isinstance(channel.headband, ImageFieldFile):
            self.assertEqual(channel.headband.name, '')

        self.assertEqual(channel.style, None)
        self.assertEqual(channel.__str__(), 'ChannelTest1')
        self.assertEqual(channel.video_count, 0)
        # self.assertEqual(
        #    channel.get_absolute_url(), "/" + channel.slug + "/")

        print(
            "   --->  test_Channel_null_attribut of ChannelTestCase : OK !")

    """
        test attributs when a channel have many attributs
    """

    def test_Channel_with_attributs(self):
        channel = Channel.objects.annotate(video_count=Count(
            "video", distinct=True)).get(title="ChannelTest2")
        self.assertEqual(channel.visible, True)
        channel.color = "Blue"
        self.assertEqual(channel.color, "Blue")
        self.assertEqual(channel.description, 'blabla')

        self.assertEqual(channel.style, "italic")
        self.assertEqual(channel.__str__(), 'ChannelTest2')
        self.assertEqual(channel.video_count, 0)
        # self.assertEqual(
        #    channel.get_absolute_url(), "/" + channel.slug + "/")

        print(
            "   --->  test_Channel_with_attributs of ChannelTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Channel.objects.get(id=1).delete()
        Channel.objects.get(id=2).delete()
        self.assertEqual(Channel.objects.all().count(), 0)

        print(
            "   --->  test_delete_object of ChannelTestCase : OK !")


"""
    test the theme
"""


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    }
)
class ThemeTestCase(TestCase):

    def setUp(self):
        Channel.objects.create(title="ChannelTest1")
        Theme.objects.create(
            title="Theme1", slug="blabla",
            channel=Channel.objects.get(title="ChannelTest1"))
        Theme.objects.create(parentId=Theme.objects.get(title="Theme1"),
                             title="Theme2", slug="blabla",
                             channel=Channel.objects.get(title="ChannelTest1"))
        print(" --->  SetUp of ThemeTestCase : OK !")

    """
        test all attributs when a theme have been save with the minimum
        of attributs
    """

    def test_Theme_null_attribut(self):
        theme = Theme.objects.annotate(video_count=Count(
            "video", distinct=True)).get(title="Theme1")
        self.assertFalse(theme.slug == slugify("blabla"))
        if isinstance(theme.headband, ImageFieldFile):
            self.assertEqual(theme.headband.name, '')
        self.assertEqual(theme.__str__(), "ChannelTest1: Theme1")
        self.assertEqual(theme.video_count, 0)
        self.assertEqual(
            theme.description,
            _('-- sorry, no translation provided --')
        )
        # self.assertEqual(
        #    theme.get_absolute_url(), "/" + theme.channel.slug + "/"
        #    + theme.slug + "/")
        print(
            "   --->  test_Theme_null_attribut of ThemeTestCase : OK !")
    """
        test attributs when a theme have many attributs
    """

    def test_Theme_with_attributs(self):
        theme = Theme.objects.get(title="Theme1")
        theme.description = "blabla"
        self.assertEqual(theme.description, 'blabla')
        print(
            "   --->  test_Theme_with_attributs of ThemeTestCase : OK !")

    """
        test attributs when a theme have many attributs
    """

    def test_Theme_with_parent(self):
        theme1 = Theme.objects.get(title="Theme1")
        theme2 = Theme.objects.get(title="Theme2")
        self.assertEqual(theme2.parentId, theme1)
        self.assertIn(theme2, theme1.theme_set.all())
        print(
            "   --->  test_Theme_with_parent of ThemeTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Theme.objects.get(id=1).delete()
        self.assertEqual(Theme.objects.all().count(), 0)
        print(
            "   --->  test_delete_object of ThemeTestCase : OK !")


"""
    test the type
"""


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    }
)
class TypeTestCase(TestCase):

    def setUp(self):
        Type.objects.create(title="Type1")

        print(" --->  SetUp of TypeTestCase : OK !")

    """
        test all attributs when a type have been save with the minimum
        of attributs
    """

    def test_Type_null_attribut(self):
        type1 = Type.objects.annotate(video_count=Count(
            "video", distinct=True)).get(title="Type1")
        self.assertEqual(type1.slug, slugify(type1.title))
        if isinstance(type1.icon, ImageFieldFile):
            self.assertEqual(type1.icon.name, '')
        self.assertEqual(type1.__str__(), "Type1")
        self.assertEqual(type1.video_count, 0)
        self.assertEqual(
            type1.description,
            _('-- sorry, no translation provided --')
        )
        print(
            "   --->  test_Type_null_attribut of TypeTestCase : OK !")

    """
        test attributs when a type have many attributs
    """

    def test_Type_with_attributs(self):
        type1 = Type.objects.get(title="Type1")
        type1.description = "blabla"
        self.assertEqual(type1.description, 'blabla')
        print(
            "   --->  test_Type_with_attributs of TypeTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Type.objects.get(id=1).delete()
        self.assertEquals(Type.objects.all().count(), 0)
        print(
            "   --->  test_delete_object of TypeTestCase : OK !")


"""
    test the discipline
"""


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    }
)
class DisciplineTestCase(TestCase):

    def setUp(self):
        Discipline.objects.create(title="Discipline1")

        print(" --->  SetUp of DisciplineTestCase : OK !")

    """
        test all attributs when a type have been save with the minimum
        of attributs
    """

    def test_Discipline_null_attribut(self):
        discipline1 = Discipline.objects.annotate(video_count=Count(
            "video", distinct=True)).get(title="Discipline1")
        self.assertEqual(discipline1.slug, slugify(discipline1.title))
        if isinstance(discipline1.icon, ImageFieldFile):
            self.assertEqual(discipline1.icon.name, '')
        self.assertEqual(discipline1.__str__(), "Discipline1")
        self.assertEqual(discipline1.video_count, 0)
        self.assertEqual(
            discipline1.description,
            _('-- sorry, no translation provided --')
        )
        print(
            "   --->  test_Type_null_attribut of TypeTestCase : OK !")

    """
        test attributs when a type have many attributs
    """

    def test_Discipline_with_attributs(self):
        discipline1 = Discipline.objects.get(title="Discipline1")
        discipline1.description = "blabla"
        self.assertEqual(discipline1.description, 'blabla')
        print(
            "   --->  test_Discipline_with_attributs of TypeTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Discipline.objects.get(id=1).delete()
        self.assertEqual(Discipline.objects.all().count(), 0)
        print(
            "   --->  test_delete_object of TypeTestCase : OK !")


"""
    test the Video and ViewCount
"""


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    }
)
class VideoTestCase(TestCase):

    def setUp(self):
        User.objects.create(username="pod", password="pod1234pod")
        owner1 = Owner.objects.get(user__username="pod")
        Video.objects.create(
            title="Video1", owner=owner1, video="test.mp4")
        type = Type.objects.create(title="autre")
        filename = "test.mp4"
        fname, dot, extension = filename.rpartition('.')

        video2 = Video.objects.create(
            type=type, title="Video2",
            date_added=datetime.today(),
            owner=owner1, date_evt=datetime.today(),
            video=os.path.join(VIDEOS_DIR, owner1.hashkey,
                               '%s.%s' % (slugify(fname), extension)),
            allow_downloading=True, description="fl",
            thumbnail="blabla.jpg", is_draft=False, duration=3)

        ViewCount.objects.create(video=video2, date=datetime.today(), count=1)
        tomorrow = datetime.today() + timedelta(days=1)
        ViewCount.objects.create(video=video2, date=tomorrow, count=2)
        print(" --->  SetUp of VideoTestCase : OK !")

    def test_Video_null_attributs(self):
        video = Video.objects.get(id=1)
        self.assertEqual(video.video.name, "test.mp4")
        self.assertEqual(video.allow_downloading, False)
        self.assertEqual(
            video.description,
            _('-- sorry, no translation provided --')
        )
        self.assertEqual(video.slug,
                         "%04d-%s" % (video.id, slugify(video.title)))
        date = datetime.today()

        self.assertEqual(video.owner, Owner.objects.get(user__username="pod"))
        self.assertEqual(video.date_added.year, date.year)
        self.assertEqual(video.date_added.month, date.month)
        self.assertEqual(video.date_added.day, date.day)
        self.assertEqual(video.date_evt, video.date_added)

        self.assertEqual(video.get_viewcount(), 0)

        self.assertEqual(video.is_draft, True)

        if isinstance(video.thumbnail, ImageFieldFile):
            self.assertEqual(video.thumbnail.name, '')

        self.assertEqual(video.duration, 0)
        # self.assertEqual(pod.get_absolute_url(), "/video/" + pod.slug + "/")
        self.assertEqual(video.__str__(), "%s - %s" %
                         ('%04d' % video.id, video.title))

        print(
            "   --->  test_Video_null_attributs of VideoTestCase : OK !")

    def test_Video_many_attributs(self):
        video2 = Video.objects.get(id=2)
        self.assertEqual(video2.video.name,
                         get_storage_path_video(video2, "test.mp4"))
        self.assertEqual(video2.allow_downloading, True)
        self.assertEqual(video2.description, 'fl')
        self.assertEqual(video2.get_viewcount(), 3)
        self.assertEqual(ViewCount.objects.get(
            video=video2, date=datetime.today()).count, 1)
        self.assertEqual(video2.allow_downloading, True)
        self.assertEqual(video2.is_draft, False)
        self.assertEqual(video2.duration, 3)
        self.assertEqual(video2.video.__str__(), video2.video.name)

        print(
            "   --->  test_Video_many_attributs of VideoTestCase : OK !")


"""
    test the Video Rendition
"""


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    }
)
class VideoRenditionTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def create_video_rendition(self, resolution="640x360", video_bitrate="1000k", audio_bitrate="300k", encode_mp4=False):
        return VideoRendition.objects.create(resolution=resolution, video_bitrate=video_bitrate, audio_bitrate=audio_bitrate, encode_mp4=encode_mp4)

    def test_VideoRendition_creation_by_default(self):
        vr = self.create_video_rendition()
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(
            vr.__str__(), 
            "VideoRendition num %s with resolution %s" %
                         ('%04d' % vr.id, vr.resolution))
        vr.clean()
        print(
            " --->  test_VideoRendition_creation_by_default of VideoRenditionTestCase : OK !")

    def test_VideoRendition_creation_with_values(self):
        print("check resolution error")
        vr = self.create_video_rendition(resolution="totototo")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(vr.__str__(), "VideoRendition num %s with resolution %s" %
                         ('%04d' % vr.id, vr.resolution))
        self.assertRaises(ValidationError, vr.clean)
        vr = self.create_video_rendition(resolution="totoxtoto")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(vr.__str__(), "VideoRendition num %s with resolution %s" %
                         ('%04d' % vr.id, vr.resolution))
        self.assertRaises(ValidationError, vr.clean)
        print("check video bitrate error")
        vr = self.create_video_rendition(
            resolution="640x360", video_bitrate="dfk")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(vr.__str__(), "VideoRendition num %s with resolution %s" %
                         ('%04d' % vr.id, vr.resolution))
        self.assertRaises(ValidationError, vr.clean)
        vr = self.create_video_rendition(
            resolution="640x360", video_bitrate="100")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(vr.__str__(), "VideoRendition num %s with resolution %s" %
                         ('%04d' % vr.id, vr.resolution))
        self.assertRaises(ValidationError, vr.clean)
        print("check audio bitrate error")
        vr = self.create_video_rendition(
            resolution="640x360", audio_bitrate="dfk")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(vr.__str__(), "VideoRendition num %s with resolution %s" %
                         ('%04d' % vr.id, vr.resolution))
        self.assertRaises(ValidationError, vr.clean)
        vr = self.create_video_rendition(
            resolution="640x360", audio_bitrate="100")
        self.assertTrue(isinstance(vr, VideoRendition))
        self.assertEqual(vr.__str__(), "VideoRendition num %s with resolution %s" %
                         ('%04d' % vr.id, vr.resolution))
        self.assertRaises(ValidationError, vr.clean)
        print(
            " --->  test_VideoRendition_creation_with_values of VideoRenditionTestCase : OK !")

"""
    test the Video Encoding model
"""


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    }
)
class EncodingVideoTestCase(TestCase):

    def setUp(self):
        User.objects.create(username="pod", password="pod1234pod")
        owner1 = Owner.objects.get(user__username="pod")
        Video.objects.create(
            title="Video1", owner=owner1, video="test.mp4")
        VideoRendition.objects.create(
            resolution="640x360", 
            video_bitrate="1000k", 
            audio_bitrate="300k", 
            encode_mp4=False)
        print(" --->  SetUp of EncodingVideoTestCase : OK !")

    def test_EncodingVideo_null_attributs(self):
        ev = EncodingVideo.objects.create(
            video=Video.objects.get(id=1),
            rendition=VideoRendition.objects.get(resolution="640x360"))
        self.assertTrue(isinstance(ev, EncodingVideo))
        evslug = "EncodingVideo num : %s with resolution %s for video %s in %s"\
        % ('%04d' % ev.id,
           ev.name,
           ev.video.id,
           ev.encoding_format)
        self.assertEqual(ev.__str__(), evslug)
        self.assertEqual(ev.name, "360p")
        self.assertEqual(ev.encoding_format, "video/mp4")
        self.assertEqual(ev.owner, Video.objects.get(id=1).owner)
        ev.clean()
        print(" --->  SetUp of test_EncodingVideo_null_attributs : OK !")

    def test_EncodingVideo_with_attributs(self):
        ev = EncodingVideo.objects.create(
            video=Video.objects.get(id=1),
            rendition=VideoRendition.objects.get(resolution="640x360"),
            name="480p",
            encoding_format = "audio/mp3")
        self.assertTrue(isinstance(ev, EncodingVideo))
        evslug = "EncodingVideo num : %s with resolution %s for video %s in %s"\
        % ('%04d' % ev.id,
           ev.name,
           ev.video.id,
           ev.encoding_format)
        self.assertEqual(ev.__str__(), evslug)
        self.assertEqual(ev.name, "480p")
        self.assertEqual(ev.encoding_format, "audio/mp3")
        self.assertEqual(ev.owner, Video.objects.get(id=1).owner)
        ev.clean()
        print(" --->  SetUp of test_EncodingVideo_with_attributs : OK !")

    def test_EncodingVideo_with_false_attributs(self):
        ev = EncodingVideo.objects.create(
            video=Video.objects.get(id=1),
            rendition=VideoRendition.objects.get(resolution="640x360"),
            name="error",
            encoding_format = "error")
        self.assertTrue(isinstance(ev, EncodingVideo))
        self.assertEqual(ev.name, "error")
        self.assertRaises(ValidationError, ev.clean)
        print(" --->  SetUp of test_EncodingVideo_with_false_attributs : OK !")
# EncodingAudio

# PlaylistM3U8

# EncodingLog
