"""Esup-Pod Django command to create a video thumbnail."""
from django.core.management.base import BaseCommand
from pod.video.models import Video
from pod.video_encode_transcript.Encoding_video_model import Encoding_video_model
from pod.video_encode_transcript.models import EncodingLog


class Command(BaseCommand):
    """Esup-pod create_thumbnail command."""

    help = "Add thumbnail to video by id"

    def add_arguments(self, parser):
        """Add args to the create_thumbnail command."""
        parser.add_argument(
            "id",
            type=int,
            help="The id of the video",
        )

    def handle(self, *args, **options):
        """Handle the create_thumbnail command."""
        vid = Video.objects.get(id=options["id"])
        encoding_video = Encoding_video_model(vid.id, vid.video.path)
        encoding_video.recreate_thumbnail()
        ec = EncodingLog.objects.get(video=vid)
        new_vid = Video.objects.get(id=options["id"])
        if new_vid.thumbnail:
            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully add thumbnail to video "%s"' % options["id"]
                )
            )
            self.stdout.write(
                self.style.SUCCESS('The thumbnail is "%s"' % new_vid.thumbnail.file)
            )
        else:
            self.stdout.write("Error when adding new thumbnail %s" % ec.log)
