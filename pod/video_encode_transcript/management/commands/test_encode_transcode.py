from django.core.management.base import BaseCommand

from django.conf import settings
from django.core.files.temp import NamedTemporaryFile
from django.contrib.auth.models import User

from pod.video.models import Video, Type

import shutil
import os
# import time

VIDEO_TEST = "pod/main/static/video_test/video_test_encodage_transcription.webm"

USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)

if USE_TRANSCRIPTION:
    # from pod.video_encode_transcript import transcript
    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")


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
        self.stdout.write(self.style.WARNING("\n ---> Start Encoding video test"))
        # video.launch_encode = True
        video.encoding_in_progress = True
        video.save()
        self.stdout.write(self.style.SUCCESS('Successfully encode video'))

        """
        video.refresh_from_db()
        print("start")
        n = 0
        while video.encoding_in_progress:
            self.stdout.write(self.style.WARNING("\n ... Encoding in progress"))
            print("start")
            video.refresh_from_db()
            time.sleep(2)
            n += 1
            if n > 30:
                raise CommandError('Error while encoding !!!')
                break
        self.stdout.write(self.style.WARNING("\n ---> End of Encoding video test"))
        print("end")
        # raise CommandError('Poll "%s" does not exist' % poll_id)
        self.stdout.write(self.style.SUCCESS('Successfully encode video'))
        """
