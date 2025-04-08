"""
Video & Audio Remote encoding test cases.

*  run with `python manage.py test pod.video_encode_transcript.tests.test_remote_encode_transcode`
"""

from unittest import TestCase, skipUnless
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.temp import NamedTemporaryFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from pod.cut.models import CutVideo
from pod.dressing.models import Dressing
from pod.video.models import Video, Type
from pod.video_encode_transcript import encode
from pod.video_encode_transcript.models import EncodingVideo, PlaylistVideo, EncodingLog
from pod.completion.models import Track

import shutil
import os
import time
import json

TEST_REMOTE_ENCODE = getattr(settings, "TEST_REMOTE_ENCODE", False)
VIDEO_TEST = "pod/main/static/video_test/video_test_encodage_transcription.mp4"
VIDEO_CREDIT_TEST = "pod/main/static/video_test/pod.mp4"
ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")
POD_API_URL = getattr(settings, "POD_API_URL", "")
POD_API_TOKEN = getattr(settings, "POD_API_TOKEN", "")
USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)
if USE_TRANSCRIPTION:
    from pod.video_encode_transcript import transcript

    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder

    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel


@skipUnless(
    TEST_REMOTE_ENCODE, "Set TEST_REMOTE_ENCODE to True before testing remote encoding."
)
class RemoteEncodeTranscriptTestCase(TestCase):
    """Test case for remote encoding and transcripting of videos."""

    def setUp(self) -> None:
        """Set up the test environment by creating a user, video, and credit video, and copying test files."""
        print("===== SetUp of RemoteEncodeTranscriptTestCase =====")
        print("===> TEST_REMOTE_ENCODE: %s" % TEST_REMOTE_ENCODE)

        user, created = User.objects.update_or_create(
            username="pod", password="pod1234pod"
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.temp_token = False
        # create token
        if not Token.objects.filter(key=POD_API_TOKEN).exists():
            self.temp_token = Token.objects.create(key=POD_API_TOKEN, user=user)
        video, created = Video.objects.update_or_create(
            title="Video1",
            owner=user,
            # video="test.mp4",
            type=Type.objects.get(id=1),
            transcript="",
        )
        tempfile = NamedTemporaryFile(delete=True)
        video.video.save("test.mp4", tempfile)
        dest = os.path.join(settings.MEDIA_ROOT, video.video.name)
        shutil.copyfile(VIDEO_TEST, dest)
        self.user = user
        self.video = video

        # Add credit video for dressing
        credit_video, created = Video.objects.update_or_create(
            title="credit_video",
            owner=user,
            # video="pod.mp4",
            type=Type.objects.get(id=1),
            transcript="",
        )
        tempfile = NamedTemporaryFile(delete=True)
        credit_video.video.save("pod.mp4", tempfile)
        dest = os.path.join(settings.MEDIA_ROOT, credit_video.video.name)
        shutil.copyfile(VIDEO_CREDIT_TEST, dest)
        self.credit_video = credit_video
        credit_videofile = credit_video.video.path
        credit_video_dir = os.path.join(
            os.path.dirname(credit_videofile), "%04d" % credit_video.id
        )
        os.makedirs(credit_video_dir, exist_ok=True)
        with open(os.path.join(credit_video_dir, "info_video.json"), "w") as f:
            json.dump({"list_audio_track": []}, f)
        print(" --->  SetUp of RemoteEncodeTranscriptTestCase: OK!")

    def tearDown(self) -> None:
        """Clean up the test environment by deleting the created video, user, and token."""
        if getattr(self, "video", False):
            self.video.delete()
        if self.temp_token:
            self.temp_token.delete()
        if getattr(self, "user", False):
            self.user.delete()
        print(" --->  tearDown of RemoteEncodeTranscriptTestCase: OK!")

    def wait_for_encode_end(self, title="", max_delay=60) -> None:
        """Wait for the encoding process to complete, raising an error if it takes too long."""
        tstart = time.time()
        self.video.refresh_from_db()
        while self.video.encoding_in_progress:
            tic = time.time()
            delay = tic - tstart
            htic = time.strftime("%M:%S", time.gmtime(tic - tstart))

            print(
                "... [%s] '%04d-%s' remote encoding in progress: %s "
                % (htic, self.video.id, title, self.video.get_encoding_step)
            )
            self.video.refresh_from_db()
            time.sleep(2)
            if delay > max_delay:
                raise ValidationError(
                    "Error while remote encoding '%s' (process too long)!" % title
                )
        self.video.refresh_from_db()

    def test_remote_encoding_transcoding(self) -> None:
        """Test the remote encoding and transcripting of a video."""
        self.remote_encoding()
        if USE_TRANSCRIPTION:
            self.remote_transcripting()
        else:
            print(
                "Remote transcript skipped. Set USE_TRANSCRIPTION to True before testing remote transcoding."
            )
        print(" --->  test_remote_encoding_transcoding: OK!")

    def remote_encoding(self) -> None:
        """Test the remote encoding of a video, verifying the creation of various encoding formats and logs."""
        print("\n ---> Start Remote encoding video test")
        encode_video = getattr(encode, ENCODE_VIDEO)
        encode_video(self.video.id, threaded=False)

        self.wait_for_encode_end("Remote")

        self.assertEqual("Video1", self.video.title)
        list_mp2t = EncodingVideo.objects.filter(
            video=self.video, encoding_format="video/mp2t"
        )
        list_playlist_video = PlaylistVideo.objects.filter(
            video=self.video, encoding_format="application/x-mpegURL"
        )
        list_playlist_master = PlaylistVideo.objects.get(
            name="playlist",
            video=self.video,
            encoding_format="application/x-mpegURL",
        )
        list_mp4 = EncodingVideo.objects.filter(
            video=self.video, encoding_format="video/mp4"
        )
        el = EncodingLog.objects.get(video=self.video)
        self.assertTrue("NO VIDEO AND AUDIO FOUND" not in el.log)
        self.assertTrue(len(list_mp2t) > 0)
        self.assertEqual(len(list_mp2t) + 1, len(list_playlist_video))
        self.assertTrue(list_playlist_master)
        self.assertTrue(len(list_mp4) > 0)
        self.assertTrue(self.video.overview)
        self.assertTrue(self.video.thumbnail)
        print("\n ---> End of Remote encoding video test")

    def test_remote_encoding_cut(self) -> None:
        """Launch test of cut video remote encoding."""
        print("\n ---> Start Remote encoding cut video test")
        encode_video = getattr(encode, ENCODE_VIDEO)

        encode_video(self.video.id, threaded=False)
        self.wait_for_encode_end("Pre-cut")

        CutVideo.objects.create(
            video=self.video,
            start="00:00:00",
            end="00:00:05",
        )
        encode_video(self.video.id, threaded=False)
        self.wait_for_encode_end("Cut")

        self.assertEqual("Video1", self.video.title)
        list_mp2t = EncodingVideo.objects.filter(
            video=self.video, encoding_format="video/mp2t"
        )
        list_playlist_video = PlaylistVideo.objects.filter(
            video=self.video, encoding_format="application/x-mpegURL"
        )
        list_playlist_master = PlaylistVideo.objects.get(
            name="playlist",
            video=self.video,
            encoding_format="application/x-mpegURL",
        )
        list_mp4 = EncodingVideo.objects.filter(
            video=self.video, encoding_format="video/mp4"
        )
        el = EncodingLog.objects.get(video=self.video)
        self.assertTrue("NO VIDEO AND AUDIO FOUND" not in el.log)
        self.assertTrue(len(list_mp2t) > 0)
        self.assertEqual(len(list_mp2t) + 1, len(list_playlist_video))
        self.assertTrue(list_playlist_master)
        self.assertTrue(len(list_mp4) > 0)
        self.assertTrue(self.video.duration < 10)
        # There is no overview for duration < 10s
        self.assertFalse(self.video.overview)
        self.assertTrue(self.video.thumbnail)
        print("\n ---> End of Remote encoding video cut test")

    def test_remote_encoding_dressing(self) -> None:
        """Launch test of video remote encoding for dressing."""
        print("\n ---> Start Remote encoding video dressing test")
        encode_video = getattr(encode, ENCODE_VIDEO)
        currentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        simplefile = SimpleUploadedFile(
            name="testimage.jpg",
            content=open(os.path.join(currentdir, "tests", "testimage.jpg"), "rb").read(),
            content_type="image/jpeg",
        )
        if FILEPICKER:
            home = UserFolder.objects.get(name="home", owner=self.user)
            customImage = CustomImageModel.objects.create(
                name="testimage",
                description="testimage",
                created_by=self.user,
                folder=home,
                file=simplefile,
            )
        else:
            customImage = CustomImageModel.objects.create(file=simplefile)

        dressing = Dressing.objects.create(
            title="Watermark dressing top right",
            watermark=customImage,
            position=Dressing.TOP_RIGHT,
            opacity=50,
            opening_credits=self.credit_video,
            ending_credits=self.credit_video,
        )
        dressing.videos.add(self.video)
        dressing.save()

        # Start encoding
        encode_video(self.video.id, threaded=False)

        # Wait 10 minutes for dressing encode end ??
        self.wait_for_encode_end("dressing", 600)

        print("end of dressing encoding")
        print(self.video.get_encoding_step)

        self.assertEqual("Video1", self.video.title)
        list_mp2t = EncodingVideo.objects.filter(
            video=self.video, encoding_format="video/mp2t"
        )
        list_playlist_video = PlaylistVideo.objects.filter(
            video=self.video, encoding_format="application/x-mpegURL"
        )
        list_playlist_master = PlaylistVideo.objects.get(
            name="playlist",
            video=self.video,
            encoding_format="application/x-mpegURL",
        )
        list_mp4 = EncodingVideo.objects.filter(
            video=self.video, encoding_format="video/mp4"
        )
        el = EncodingLog.objects.get(video=self.video)
        self.assertTrue("NO VIDEO AND AUDIO FOUND" not in el.log)
        self.assertTrue(len(list_mp2t) > 0)
        self.assertEqual(len(list_mp2t) + 1, len(list_playlist_video))
        self.assertTrue(list_playlist_master)
        self.assertTrue(len(list_mp4) > 0)
        self.assertTrue(self.video.overview)
        self.assertTrue(self.video.thumbnail)

        with open(self.video.encodinglog.logfile.path) as json_file:
            info_video = json.load(json_file)
            print(json.dumps(info_video, indent=4, sort_keys=True))
        print("\n ---> End of Remote encoding video dressing test")

    def remote_transcripting(self) -> None:
        """Launch test of video remote transcripting."""
        print("\n ---> Start Remote transcripting video test")
        if self.video.get_video_mp3() and not self.video.encoding_in_progress:
            self.video.transcript = "fr"
            self.video.save()
            transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
            transcript_video(self.video.id, threaded=False)

            self.wait_for_encode_end("Transcripting", 120)

            self.video.refresh_from_db()
            if not Track.objects.filter(video=self.video, lang="fr").exists():
                raise ValidationError("Error while remote transcripting!!!")
        else:
            raise ValidationError("No mp3 found!!!")
        print("\n ---> End of remote transcripting video test")
