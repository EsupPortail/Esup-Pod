from django.core.management.base import BaseCommand
from pod.video.Encoding_video_model import Encoding_video_model


class Command(BaseCommand):
    help = "Test new encoding"

    def add_arguments(self, parser):
        parser.add_argument(
            "id",
            type=int,
            help="The id of the future video",
        )
        parser.add_argument(
            "input_file",
            type=str,
            help="The input file",
        )

    def handle(self, *args, **options):
        encoding_video = Encoding_video_model(options["id"], options["input_file"], 1, 2)
        # encoding_video.encode_video()
        encoding_video.store_json_info()
