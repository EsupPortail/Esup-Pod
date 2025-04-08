"""Import encoded recording into Pod."""

from django.conf import settings

from django.utils import translation
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from pod.recorder.models import Recording
from pod.video.remote_encode import store_remote_encoding_studio


LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", "fr")


class Command(BaseCommand):
    # args = 'video_id'
    help = "Import encoded recording into Pod"

    def add_arguments(self, parser):
        parser.add_argument(
            "recording_id",
            type=int,
            help="Indicates the id of the video to import encoded files",
        )
        parser.add_argument(
            "output_video",
            type=str,
            help="Indicates the path of the encoded video",
        )

    def handle(self, *args, **options):
        # Activate a fixed locale fr
        translation.activate(LANGUAGE_CODE)
        recording_id = options["recording_id"]
        output_video = options["output_video"]
        try:
            recording = Recording.objects.get(id=recording_id)
            print(recording_id, output_video)
            store_remote_encoding_studio(recording_id, output_video)
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully import recording video "%s"' % (recording)
                )
            )
        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "******* Recording id matching query does not exist: %s *******"
                    % recording_id
                )
            )
