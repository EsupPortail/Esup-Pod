"""Esup-Pod command to encode video by id."""

from django.core.management.base import BaseCommand
from pod.video_encode_transcript.encode import encode_video


class Command(BaseCommand):
    """Encode Video by ID."""

    help = "Encoding video by id"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "id",
            type=int,
            help="The id of the video",
        )

    def handle(self, *args, **options) -> None:
        encode_video(options["id"])
