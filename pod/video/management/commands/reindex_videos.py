"""Script reindexing all videos (useful in case of loss of the ElasticSearch database)"""

from django.core.management.base import BaseCommand
from pod.video.models import Video
from pod.video_search.models import index_video


def reindex_all_videos(dry_run: bool) -> int:
    """Reindex all videos."""
    print("\nReindexing all videos...")
    videos = Video.objects.all()
    nb_videos = 0
    for vid in videos:
        print(".", end="")
        if not dry_run:
            index_video(vid)
        nb_videos += 1
    print("")
    return nb_videos


class Command(BaseCommand):
    """Reindex all videos."""

    help = "Reindex all videos (useful in case of loss of the ElasticSearch database)"

    def add_arguments(self, parser) -> None:
        """Allow arguments to be used with the command."""
        parser.add_argument(
            "--dry",
            help="Simulate what would be reindexed.",
            action="store_true",
            default=False,
        )

    def handle(self, *args, **options) -> None:
        """Handle the clean_video_files command call."""
        if options["dry"]:
            print("Simulation mode ('dry'). Nothing will be deleted.")
        self.nb_reindexed = reindex_all_videos(options["dry"])

        self.print_resume(options["dry"])

    def print_resume(self, dry_run: bool) -> None:
        """Print summary of reindexed objects."""

        if dry_run:
            print(
                "[DRY RUN] %i video(s) would have been reindexed." % (self.nb_reindexed)
            )
        else:
            print("%i video(s) reindexed." % self.nb_reindexed)
        print("Have a nice day ;)")
