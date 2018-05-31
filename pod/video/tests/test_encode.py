from django.conf import settings
from django.test import TestCase
from django.test import override_settings
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.models import User
from django.core.files import File

from pod.video.models import Video
from pod.video import encode
from pod.video.models import EncodingVideo
# from pod.video.models import EncodingAudio
from pod.video.models import EncodingLog
from pod.video.models import PlaylistVideo
try:
    from pod.authentication.models import Owner
except ImportError:
    from django.contrib.auth.models import User as Owner

import urllib3
import shutil
import os

URL_VIDEO_TO_TEST = getattr(
    settings, 'URL_VIDEO_TO_TEST', "http://pod.univ-lille1.fr/media/pod.mp4")
URL_AUDIO_TO_TEST = getattr(
    settings, 'URL_AUDIO_TO_TEST', "http://pod.univ-lille1.fr/media/pod.mp3")
HTTP_PROXY = getattr(settings, 'HTTP_PROXY', None)


@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'media'),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'db.sqlite',
        }
    }
)
class EncodeTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        User.objects.create(username="pod", password="pod1234pod")
        owner1 = Owner.objects.get(user__username="pod")
        video = Video.objects.create(
            title="Video1", owner=owner1, video="test.mp4")
        print("Download video file from %s" % URL_VIDEO_TO_TEST)
        tempfile = NamedTemporaryFile(delete=True)
        if HTTP_PROXY:
            proxy = urllib3.ProxyManager(settings.HTTP_PROXY)
            with proxy.request(
                    'GET',
                    URL_VIDEO_TO_TEST,
                    preload_content=False) as r, open(
                    tempfile.name, 'wb') as out_file:
                shutil.copyfileobj(r, out_file)
        else:
            http = urllib3.PoolManager()
            with http.request(
                    'GET',
                    URL_VIDEO_TO_TEST,
                    preload_content=False) as r, open(
                    tempfile.name, 'wb') as out_file:
                shutil.copyfileobj(r, out_file)
        video.video.save("test.mp4", File(tempfile))

        print("\n ---> Start Encoding")
        encode.encode_video(1)
        print("\n ---> End Encoding")

        print(" --->  SetUp of EncodeTestCase : OK !")

    def test_result_encoding_video(self):
        # video id=1 et audio id=2
        video_to_encode = Video.objects.get(id=1)
        list_mp2t = EncodingVideo.objects.filter(
            video=video_to_encode,
            encoding_format="video/mp2t")
        list_playlist_video = PlaylistVideo.objects.filter(
            video=video_to_encode,
            encoding_format="application/x-mpegURL"
        )
        list_playlist_master = PlaylistVideo.objects.get(
            name="playlist",
            video=video_to_encode,
            encoding_format="application/x-mpegURL")
        list_mp4 = EncodingVideo.objects.filter(
            video=video_to_encode,
            encoding_format="video/mp4")
        el = EncodingLog.objects.get(video=video_to_encode)
        self.assertTrue("NO VIDEO AND AUDIO FOUND" not in el.log)
        self.assertTrue(len(list_mp2t) > 0)
        self.assertEqual(len(list_mp2t) + 1, len(list_playlist_video))
        self.assertTrue(list_playlist_master)
        self.assertTrue(len(list_mp4) > 0)
        self.assertTrue(video_to_encode.overview)
        self.assertTrue(video_to_encode.thumbnail)
        print(
            " --->  test_encode_video of EncodeTestCase : OK !")

    def test_delete_object(self):
        # tester la suppression de la video et la suppression en cascade
        video_to_encode = Video.objects.get(id=1)
        video = video_to_encode.video.path
        overview = video_to_encode.overview.path

        list_mp2t = EncodingVideo.objects.filter(
            video=video_to_encode,
            encoding_format="video/mp2t")
        list_playlist_video = PlaylistVideo.objects.filter(
            video=video_to_encode,
            encoding_format="application/x-mpegURL"
        )
        playlist_master = PlaylistVideo.objects.get(
            name="playlist",
            video=video_to_encode,
            encoding_format="application/x-mpegURL")
        playlist_master_file = playlist_master.source_file.path
        list_mp4 = EncodingVideo.objects.filter(
            video=video_to_encode,
            encoding_format="video/mp4")

        video_to_encode.delete()
        self.assertTrue(not os.path.exists(video))
        self.assertTrue(not os.path.exists(overview))
        self.assertTrue(not os.path.exists(playlist_master_file))

        self.assertEqual(list_mp2t.count(), 0)
        self.assertEqual(list_playlist_video.count(), 0)
        self.assertEqual(list_mp4.count(), 0)

        self.assertEqual(EncodingLog.objects.filter(
            video__id=1).count(), 0)

        self.assertEqual(len(os.listdir(os.path.dirname(overview))), 0)

        print(
            "   --->  test_delete_object of EncodeTestCase : OK !")
