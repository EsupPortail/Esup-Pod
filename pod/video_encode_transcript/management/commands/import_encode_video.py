from django.core.management.base import BaseCommand
from pod.video_encode_transcript.Encoding_video_model import Encoding_video_model
from pod.video_encode_transcript.encode import store_encoding_info, end_of_encoding
from pod.video.models import Video


class Command(BaseCommand):
    help = "Import encoded video"

    def add_arguments(self, parser) -> None:
        parser.add_argument("video_id", type=int)

    def handle(self, *args, **options) -> None:
        video_id = options["video_id"]
        vid = Video.objects.get(id=video_id)
        encoding_video = Encoding_video_model(video_id, vid.video.path)
        final_video = store_encoding_info(video_id, encoding_video)
        end_of_encoding(final_video)
        self.stdout.write(self.style.SUCCESS('Successfully import video "%s"' % video_id))
