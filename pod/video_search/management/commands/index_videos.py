"""index_videos management command."""
from django.core.management.base import BaseCommand
from django.utils import translation
from pod.video.models import Video
from django.conf import settings
from pod.video.context_processors import get_available_videos
from pod.video_search.utils import index_es, delete_es
from pod.video_search.utils import delete_index_es, create_index_es
import time


class Command(BaseCommand):
    """Indexes all or specified video in Elasticsearch."""

    args = "--all or -id <video_id video_id ...>"
    help = "Indexes the specified video in Elasticsearch."

    def add_arguments(self, parser):
        """Add arguments of index_videos command."""
        parser.add_argument("-id", "--video_id", nargs="+", type=int, dest="video_id")
        parser.add_argument(
            "--all",
            action="store_true",
            dest="all",
            help="index all video",
        )

    def handle(self, *args, **options):
        """Handle an index_videos command call."""
        translation.activate(settings.LANGUAGE_CODE)
        if options["all"]:
            delete_index_es()
            time.sleep(10)
            create_index_es()
            time.sleep(10)
            iteration = 0
            videos = get_available_videos()
            for video in videos:
                if iteration % 1000 == 0:
                    time.sleep(10)
                iteration += 1
                index_es(video)
        elif options["video_id"]:
            for video_id in options["video_id"]:
                self.manage_es(video_id)
        else:
            self.stdout.write(
                self.style.ERROR(
                    "****** Warning: you must give some arguments: %s ******" % self.args
                )
            )
        translation.deactivate()

    def manage_es(self, video_id):
        """Index or delete a video in ES."""
        try:
            video = Video.objects.get(pk=video_id)
            if video.is_draft is False:
                index_es(video)
                self.stdout.write(
                    self.style.SUCCESS('Successfully index Video "%s"' % video_id)
                )
            else:
                delete_es(video)
        except Video.DoesNotExist:
            self.stdout.write(self.style.ERROR('Video "%s" does not exist' % video_id))
