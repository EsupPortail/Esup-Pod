"""
Video & Audio encoding test cases.

*  run with `python manage.py test pod.video_encode_transcript.tests.test_encode`
"""

from django.conf import settings
from django.test import TestCase
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.models import User


from pod.video.models import Video, Type
from ..models import EncodingVideo
from ..models import PlaylistVideo
from ..models import EncodingStep
from .. import encode

import shutil
import os
import time

VIDEO_TEST = "pod/main/static/video_test/video_test_encodage_transcription.webm"
TEST_REMOTE_ENCODE = getattr(settings, "TEST_REMOTE_ENCODE", False)
ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")

class TestRemoteEncodeTestCase(TestCase):
    """Video and audio encoding tests."""

    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        """Set up video for remote encoding tests."""
        self.user = User.objects.create(username="pod", password="pod1234pod")
        # owner1 = Owner.objects.get(user__username="pod")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )

    def test_remote_encoding_file(self):
        if not TEST_REMOTE_ENCODE:
            return
        tempfile = NamedTemporaryFile(delete=True)
        self.video.video.save("test.mp4", tempfile)
        dest = os.path.join(settings.MEDIA_ROOT, self.video.video.name)
        shutil.copyfile(VIDEO_TEST, dest)
        print("\n ---> Start Encoding video test")
        encode_video = getattr(encode, ENCODE_VIDEO)
        encode_video(self.video.id, threaded=False)
        self.video.refresh_from_db()
        n = 0
        while self.video.encoding_in_progress:
            print("... Encoding in progress : %s " % self.video.get_encoding_step)
            self.video.refresh_from_db()
            time.sleep(2)
            n += 1
            if n > 60:
                raise Exception('Error while encoding !!!')

        print("\n ---> End of Encoding video test")
        list_mp2t = EncodingVideo.objects.filter(
            video=self.video, encoding_format="video/mp2t"
        )
        list_playlist_video = PlaylistVideo.objects.filter(
            video=self.video, encoding_format="application/x-mpegURL"
        )
        list_playlist_master = PlaylistVideo.objects.filter(
            name="playlist",
            video=self.video,
            encoding_format="application/x-mpegURL",
        )
        list_mp4 = EncodingVideo.objects.filter(
            video=self.video, encoding_format="video/mp4"
        )
        print(list_mp2t)
        print(list_playlist_video)
        print(list_playlist_master)
        print(list_mp4)
        print('Successfully encode video')
