from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from pod.video.models import Video, Type
from pod.video_encode_transcript import encode
from pod.video_encode_transcript.models import EncodingVideo
from pod.video_encode_transcript.models import PlaylistVideo
from pod.completion.models import Track

import shutil
import os
import time
import coverage

VIDEO_TEST = "pod/main/static/video_test/video_test_encodage_transcription.webm"
ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")
POD_API_URL = getattr(settings, "POD_API_URL", "")
POD_API_TOKEN = getattr(settings, "POD_API_TOKEN", "")
USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)
if USE_TRANSCRIPTION:
    from pod.video_encode_transcript import transcript

    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")


class Command(BaseCommand):
    help = "launch of video encoding and transcripting for video test: %s" % VIDEO_TEST

    def handle(self, *args, **options) -> None:
        cov = coverage.coverage()
        cov.start()
        user, created = User.objects.update_or_create(
            username="pod", password="pod1234pod"
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()
        # create token
        if not Token.objects.filter(key=POD_API_TOKEN).exists():
            Token.objects.create(key=POD_API_TOKEN, user=user)
        # owner1 = Owner.objects.get(user__username="pod")
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
        self.test_encoding(video)
        self.test_transcripting(video)
        cov.stop()
        cov.save()
        cov.html_report()
        print("\n -----> End of Encoding/transcripting video test")

    def test_transcripting(self, video) -> None:
        print("\n ---> Start Transcripting video test")
        if video.get_video_mp3() and not video.encoding_in_progress:
            video.transcript = "fr"
            video.save()
            transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
            transcript_video(video.id, threaded=False)
            video.refresh_from_db()
            n = 0
            while video.encoding_in_progress:
                print("... Transcripting in progress: %s " % video.get_encoding_step)
                video.refresh_from_db()
                time.sleep(2)
                n += 1
                if n > 60:
                    raise CommandError("Error while transcripting!!!")
            video.refresh_from_db()
            self.test_result_transcripting(video)
        else:
            raise CommandError("No mp3 found!!!")
        print("\n ---> End of transcripting video test")

    def test_result_transcripting(self, video) -> None:
        if not Track.objects.filter(video=video, lang="fr").exists():
            raise CommandError("Error while transcripting!!!")

    def test_encoding(self, video) -> None:
        print("\n ---> Start Encoding video test")
        encode_video = getattr(encode, ENCODE_VIDEO)
        encode_video(video.id, threaded=False)
        video.refresh_from_db()
        n = 0
        while video.encoding_in_progress:
            print("... Encoding in progress: %s " % video.get_encoding_step)
            video.refresh_from_db()
            time.sleep(2)
            n += 1
            if n > 60:
                raise CommandError("Error while encoding!!!")
        video.refresh_from_db()
        self.test_result_encoding(video)
        print("\n ---> End of Encoding video test")

    def test_result_encoding(self, video) -> None:
        list_mp2t = EncodingVideo.objects.filter(
            video=video, encoding_format="video/mp2t"
        )
        list_playlist_video = PlaylistVideo.objects.filter(
            video=video, encoding_format="application/x-mpegURL"
        )
        list_playlist_master = PlaylistVideo.objects.get(
            name="playlist",
            video=video,
            encoding_format="application/x-mpegURL",
        )
        list_mp4 = EncodingVideo.objects.filter(video=video, encoding_format="video/mp4")
        if not len(list_mp2t) > 0:
            raise CommandError("no video/mp2t found")
        if not len(list_mp2t) + 1 == len(list_playlist_video):
            raise CommandError("Error in playlist count")
        if not list_playlist_master:
            raise CommandError("No playlist master found")
        if not len(list_mp4) > 0:
            raise CommandError("No encoding mp4")
        if not video.overview:
            raise CommandError("No overview")
        if not video.thumbnail:
            raise CommandError("No thumbnails")
