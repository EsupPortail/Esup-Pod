"""Encoding video by id."""

from django.core.management.base import BaseCommand
from pod.video_encode_transcript.encode import encode_video


class Command(BaseCommand):
    help = "Encoding video by id"

    def add_arguments(self, parser):
        parser.add_argument(
            "id",
            type=int,
            help="The id of the video",
        )

    def handle(self, *args, **options):
        encode_video(options["id"])
