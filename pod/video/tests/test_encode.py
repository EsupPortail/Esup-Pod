from django.conf import settings
from django.test import TestCase
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.models import User


from pod.video.models import Video, Type
from pod.video import encode
from pod.video.models import EncodingVideo
from pod.video.models import EncodingAudio
from pod.video.models import EncodingLog
from pod.video.models import PlaylistVideo

import shutil
import os

VIDEO_TEST = getattr(
    settings, 'VIDEO_TEST', 'pod/main/static/video_test/pod.mp4')

AUDIO_TEST = getattr(
    settings, 'VIDEO_TEST', 'pod/main/static/video_test/pod.mp3')


class EncodeTestCase(TestCase):
    fixtures = ['initial_data.json', ]

    def setUp(self):
        user = User.objects.create(username="pod", password="pod1234pod")
        # owner1 = Owner.objects.get(user__username="pod")
        video = Video.objects.create(
            title="Video1", owner=user, video="test.mp4",
            type=Type.objects.get(id=1))
        tempfile = NamedTemporaryFile(delete=True)
        video.video.save("test.mp4", tempfile)
        dest = os.path.join(settings.MEDIA_ROOT, video.video.name)
        shutil.copyfile(
            VIDEO_TEST, dest)
        print("\n ---> Start Encoding video")
        encode.encode_video(video.id)
        print("\n ---> End Encoding video")

        audio = Video.objects.create(
            title="Audio1", owner=user, video="test.mp3",
            type=Type.objects.get(id=1))
        tempfile = NamedTemporaryFile(delete=True)
        audio.video.save("test.mp3", tempfile)
        dest = os.path.join(settings.MEDIA_ROOT, audio.video.name)
        shutil.copyfile(
            AUDIO_TEST, dest)
        print("\n ---> Start Encoding audio")
        encode.encode_video(audio.id)
        print("\n ---> End Encoding audio")

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

    def test_result_encoding_audio(self):
        # video id=1 et audio id=2
        audio = Video.objects.get(id=2)
        list_m4a = EncodingAudio.objects.filter(
            video=audio,
            encoding_format="video/mp4")
        list_mp3 = EncodingAudio.objects.filter(
            video=audio,
            encoding_format="audio/mp3")
        el = EncodingLog.objects.get(video=audio)
        self.assertTrue("NO VIDEO AND AUDIO FOUND" not in el.log)
        self.assertTrue(len(list_mp3) > 0)
        self.assertTrue(len(list_m4a) > 0)
        self.assertFalse(audio.overview)
        self.assertFalse(audio.thumbnail)
        print(
            " --->  test_result_encoding_audio of EncodeTestCase : OK !")

    def test_delete_object(self):
        # tester la suppression de la video et la suppression en cascade
        video_to_encode = Video.objects.get(id=1)
        video = video_to_encode.video.path
        log_file = os.path.join(
            os.path.dirname(video),
            "%04d" % video_to_encode.id,
            'encoding.log')

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
        self.assertTrue(not os.path.exists(log_file))
        self.assertTrue(not os.path.exists(playlist_master_file))

        self.assertEqual(list_mp2t.count(), 0)
        self.assertEqual(list_playlist_video.count(), 0)
        self.assertEqual(list_mp4.count(), 0)

        self.assertEqual(EncodingLog.objects.filter(
            video__id=1).count(), 0)
        self.assertEqual(len(os.listdir(os.path.dirname(log_file))), 0)

        audio = Video.objects.get(id=2)
        audio_video_path = audio.video.path
        audio_log_file = os.path.join(
            os.path.dirname(video),
            "%04d" % audio.id,
            'encoding.log')
        audio.delete()
        self.assertTrue(not os.path.exists(audio_video_path))
        self.assertTrue(not os.path.exists(audio_log_file))
        self.assertEqual(len(os.listdir(os.path.dirname(audio_log_file))), 0)

        print(
            "   --->  test_delete_object of EncodeTestCase : OK !")
