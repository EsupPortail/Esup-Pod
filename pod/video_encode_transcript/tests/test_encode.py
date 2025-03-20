"""
Video & Audio encoding test cases.

*  run with `python manage.py test pod.video_encode_transcript.tests.test_encode`
"""

from django.conf import settings
from django.test import TestCase
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.models import User


from pod.video.models import Video, Type
from pod.video_encode_transcript import encode
from pod.video_encode_transcript.models import EncodingVideo
from pod.video_encode_transcript.models import EncodingAudio
from pod.video_encode_transcript.models import EncodingLog
from pod.video_encode_transcript.models import PlaylistVideo

import shutil
import os

VIDEO_TEST = getattr(settings, "VIDEO_TEST", "pod/main/static/video_test/pod.mp4")

AUDIO_TEST = getattr(settings, "AUDIO_TEST", "pod/main/static/video_test/pod.mp3")


class EncodeTestCase(TestCase):
    """Video and audio encoding tests."""

    fixtures = [
        "initial_data.json",
    ]

    _one_time_setup_complete = False

    def setUp(self):
        """Set up video and audio encoding tests."""
        if not self._one_time_setup_complete:
            self.before_running_all_tests()
            self._one_time_setup_complete = True

        self.before_running_each_test()

    def before_running_all_tests(self):
        """Set up that must be run just once before all tests."""
        user = User.objects.create(username="pod", password="pod1234pod")
        # owner1 = Owner.objects.get(user__username="pod")
        video = Video.objects.create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )
        tempfile = NamedTemporaryFile(delete=True)
        video.video.save("test.mp4", tempfile)
        dest = os.path.join(settings.MEDIA_ROOT, video.video.name)
        shutil.copyfile(VIDEO_TEST, dest)
        print("\n ---> Start Encoding video test.mp4")
        encode.encode_video(video.id)
        print("\n ---> End Encoding video test.mp4")

        audio = Video.objects.create(
            title="Audio1",
            owner=user,
            video="test.mp3",
            type=Type.objects.get(id=1),
        )
        tempfile = NamedTemporaryFile(delete=True)
        audio.video.save("test.mp3", tempfile)
        dest = os.path.join(settings.MEDIA_ROOT, audio.video.name)
        shutil.copyfile(AUDIO_TEST, dest)
        print("\n ---> Start Encoding audio test.mp3")
        encode.encode_video(audio.id)
        print("\n ---> End Encoding audio test.mp3")

        print(" --->  SetUp of EncodeTestCase: OK!")

    def before_running_each_test(self):
        """Set up what must be run before each test."""
        pass

    def test_encoding_wrong_file(self):
        """Test if a try to encode a wrong file ends well."""
        video = Video.objects.create(
            title="Video2",
            owner=User.objects.get(id=1),
            video="test.txt",
            type=Type.objects.get(id=1),
        )
        print("\n ---> Try to Encode video 2")
        encode.encode_video(video.id)
        el = EncodingLog.objects.get(video=video)
        self.assertTrue("Wrong file or path:" in el.log)

    def test_result_encoding_video(self) -> None:
        """Test if video encoding worked properly."""
        # video id=1 et audio id=2
        video_to_encode = Video.objects.get(id=1)
        self.assertEqual("Video1", video_to_encode.title)
        list_mp2t = EncodingVideo.objects.filter(
            video=video_to_encode, encoding_format="video/mp2t"
        )
        list_playlist_video = PlaylistVideo.objects.filter(
            video=video_to_encode, encoding_format="application/x-mpegURL"
        )
        list_playlist_master = PlaylistVideo.objects.get(
            name="playlist",
            video=video_to_encode,
            encoding_format="application/x-mpegURL",
        )
        list_mp4 = EncodingVideo.objects.filter(
            video=video_to_encode, encoding_format="video/mp4"
        )
        el = EncodingLog.objects.get(video=video_to_encode)
        self.assertTrue("NO VIDEO AND AUDIO FOUND" not in el.log)
        self.assertTrue(len(list_mp2t) > 0)
        self.assertEqual(len(list_mp2t) + 1, len(list_playlist_video))
        self.assertTrue(list_playlist_master)
        self.assertTrue(len(list_mp4) > 0)
        self.assertTrue(video_to_encode.overview)
        self.assertTrue(video_to_encode.thumbnail)
        print(" --->  test_encode_video of EncodeTestCase: OK!")

    def test_result_encoding_audio(self):
        """Test if audio encoding worked properly."""
        # video id=1 & audio id=2
        audio = Video.objects.get(id=2)
        self.assertEqual("Audio1", audio.title)
        list_m4a = EncodingAudio.objects.filter(video=audio, encoding_format="video/mp4")
        list_mp3 = EncodingAudio.objects.filter(video=audio, encoding_format="audio/mp3")
        el = EncodingLog.objects.get(video=audio)
        self.assertTrue("NO VIDEO AND AUDIO FOUND" not in el.log)
        self.assertTrue(len(list_mp3) > 0)
        self.assertTrue(len(list_m4a) > 0)
        self.assertFalse(audio.overview)
        self.assertFalse(audio.thumbnail)
        print(" --->  test_result_encoding_audio of EncodeTestCase: OK!")

    def test_delete_video(self):
        """Test video deletion and cascade deleting."""
        video_to_encode = Video.objects.get(id=1)
        self.assertEqual("Video1", video_to_encode.title)
        video = video_to_encode.video.path
        video_dir = os.path.join(os.path.dirname(video), "%04d" % video_to_encode.id)
        log_file = os.path.join(video_dir, "info_video.json")

        list_mp2t = EncodingVideo.objects.filter(
            video=video_to_encode, encoding_format="video/mp2t"
        )
        list_playlist_video = PlaylistVideo.objects.filter(
            video=video_to_encode, encoding_format="application/x-mpegURL"
        )
        playlist_master = PlaylistVideo.objects.get(
            name="playlist",
            video=video_to_encode,
            encoding_format="application/x-mpegURL",
        )
        playlist_master_file = playlist_master.source_file.path
        list_mp4 = EncodingVideo.objects.filter(
            video=video_to_encode, encoding_format="video/mp4"
        )

        image_overview = os.path.join(
            os.path.dirname(video_to_encode.overview.path), "overview.png"
        )
        self.assertTrue(os.path.isfile(image_overview))
        self.assertTrue(video_to_encode.thumbnail.file_exist())
        image_thumbnail = video_to_encode.thumbnail.file.path

        video_to_encode.delete()

        self.assertFalse(os.path.exists(video))
        self.assertFalse(os.path.exists(log_file))
        self.assertFalse(os.path.exists(playlist_master_file))
        self.assertFalse(os.path.exists(image_overview))
        self.assertFalse(os.path.exists(image_thumbnail))

        self.assertEqual(list_mp2t.count(), 0)
        self.assertEqual(list_playlist_video.count(), 0)
        self.assertEqual(list_mp4.count(), 0)

        self.assertEqual(EncodingLog.objects.filter(video__id=1).count(), 0)
        # check video folder remove
        self.assertFalse(os.path.isdir(video_dir))

        audio = Video.objects.get(id=2)
        self.assertEqual("Audio1", audio.title)
        audio_video_path = audio.video.path
        audio_dir = os.path.join(os.path.dirname(audio_video_path), "%04d" % audio.id)
        audio_log_file = os.path.join(audio_dir, "info_video.json")
        audio.delete()
        self.assertTrue(not os.path.exists(audio_video_path))
        self.assertTrue(not os.path.exists(audio_log_file))
        # check audio folder remove
        self.assertFalse(os.path.isdir(audio_dir))

        print("   --->  test_delete_video of EncodeTestCase: OK!")
