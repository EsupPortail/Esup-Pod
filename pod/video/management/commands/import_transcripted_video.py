from django.conf import settings

from django.utils import translation
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist

from pod.video.models import Video
from pod.video.remote_transcript import store_remote_transcripting_video


LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", "fr")


class Command(BaseCommand):
    # args = 'video_id'
    help = "Import recorded video into Pod"

    def add_arguments(self, parser):
        parser.add_argument(
            "video_id",
            type=int,
            help="Indicates the id of the video to import encoded files",
        )

    def handle(self, *args, **options):
        # Activate a fixed locale fr
        translation.activate(LANGUAGE_CODE)
        video_id = options["video_id"]
        try:
            video = Video.objects.get(id=video_id)
            store_remote_transcripting_video(video_id)
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully import transcripted video "%s"' % (video)
                )
            )
        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    "******* Video id matching query does not exist: %s *******"
                    % video_id
                )
            )
