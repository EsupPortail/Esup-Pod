"""Esup-Pod Django command to create a video thumbnail.

This management command allows creating thumbnails for one or more videos
by specifying their IDs. It uses the video encoding model to regenerate
thumbnails and provides feedback about the operation's success or failure.
"""

from django.core.management.base import BaseCommand
from pod.video.models import Video
from pod.video_encode_transcript.Encoding_video_model import Encoding_video_model
from pod.video_encode_transcript.models import EncodingLog


class Command(BaseCommand):
    """Command class for creating video thumbnails in Esup-Pod."""

    help = "Add a thumbnail to the video by id (you can add several ids)"

    def add_arguments(self, parser):
        """Define the command-line arguments.
        Args:
            parser: The argument parser to which arguments will be added.

        Arguments:
            ids: One or more video IDs for which thumbnails should be created.
        """
        parser.add_argument(
            "ids",
            type=int,
            nargs="+",
            help="The ids of the videos",
        )

    def handle(self, *args, **options):
        """Execute the thumbnail creation command."""
        for vid_id in options["ids"]:
            try:
                vid = Video.objects.get(id=vid_id)
                encoding_video = Encoding_video_model(vid.id, vid.video.path)
                encoding_video.recreate_thumbnail()
                ec = EncodingLog.objects.get(video=vid)
                new_vid = Video.objects.get(id=vid_id)
                if new_vid.thumbnail:
                    self.stdout.write(
                        self.style.SUCCESS(
                            'Successfully add thumbnail to video "%s"' % vid_id
                        )
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            'The thumbnail is "%s"' % new_vid.thumbnail.file
                        )
                    )
                else:
                    self.stdout.write("Error when adding new thumbnail %s" % ec.log)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        "An error occurred with video %d: %s" % (vid_id, str(e))
                    )
                )
