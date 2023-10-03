from django.core.management.base import BaseCommand
from django.core.cache import cache
from pod.video.context_processors import context_video_data
from django.core import serializers
import json


class Command(BaseCommand):
    """Command to store video data in cache."""
    help = "Store video data in django cache : " \
        + "types, discipline, video count and videos duration"

    def handle(self, *args, **options):
        """Function called to store video data in cache."""
        cache.delete_many(['DISCIPLINES', 'VIDEOS_COUNT', 'VIDEOS_DURATION', 'TYPES'])
        video_data = context_video_data(request=None)
        msg = 'Successfully store video data in cache'
        for data in video_data:
            try:
                msg += "\n %s : %s" % (
                    data,
                    json.dumps(serializers.serialize("json", video_data[data]))
                )
            except (TypeError, AttributeError):
                msg += "\n %s : %s" % (data, video_data[data])
        self.stdout.write(
            self.style.SUCCESS(msg)
        )
