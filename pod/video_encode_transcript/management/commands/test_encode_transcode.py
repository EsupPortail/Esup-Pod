from django.core.management.base import BaseCommand, CommandError

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.models import User

from pod.video.models import Video, Type
from pod.video_encode_transcript import encode

import shutil
import os
import time

VIDEO_TEST = "pod/main/static/video_test/video_test_encodage_transcription.webm"
ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")


class Command(BaseCommand):
    help = 'launch of video encoding and transcoding for video test : %s' % VIDEO_TEST

    def handle(self, *args, **options):
        print("handle")
        user, created = User.objects.update_or_create(username="pod", password="pod1234pod")
        # owner1 = Owner.objects.get(user__username="pod")
        video, created = Video.objects.update_or_create(
            title="Video1",
            owner=user,
            video="test.mp4",
            type=Type.objects.get(id=1),
        )

        tempfile = NamedTemporaryFile(delete=True)
        video.video.save("test.mp4", tempfile)
        dest = os.path.join(settings.MEDIA_ROOT, video.video.name)
        shutil.copyfile(VIDEO_TEST, dest)
        print("\n ---> Start Encoding video test")
        encode_video = getattr(encode, ENCODE_VIDEO)
        encode_video(video.id, threaded=False)
        video.refresh_from_db()
        n = 0
        while video.encoding_in_progress:
            print("... Encoding in progress : %s " % video.get_encoding_step)
            video.refresh_from_db()
            time.sleep(2)
            n += 1
            if n > 60:
                raise Exception('Error while encoding !!!')

        print("\n ---> End of Encoding video test")
