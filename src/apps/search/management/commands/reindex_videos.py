"""
Esup-Pod - reindex_videos management command.

Indexes all or specific videos in Redis Search.
Equivalent to V4 commands:
  - create_pod_index  → reindex_videos --drop
  - index_videos --all → reindex_videos
  - index_videos -id <id> → reindex_videos --video-id <id>
"""

import logging
import time

from django.core.management.base import BaseCommand
from django.utils import translation
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Re-indexes videos in Redis Search.

    Usage:
        python manage.py reindex_videos           # Index all published videos
        python manage.py reindex_videos --drop    # Drop index then reindex all (equiv. V4 create_pod_index)
        python manage.py reindex_videos --video-id 42 56  # Re-index specific videos
    """

    help = (
        "Indexes videos in Redis Search. "
        "Equivalent to V4 index_videos and create_pod_index commands."
    )

    def add_arguments(self, parser):
        """Add custom arguments to the command."""
        parser.add_argument(
            "--drop",
            action="store_true",
            dest="drop",
            help=(
                "Drop the Redis Search index before reindexing. "
                "Equivalent to V4 create_pod_index command."
            ),
        )
        parser.add_argument(
            "--video-id",
            nargs="+",
            type=int,
            dest="video_ids",
            help="Re-index only the specified video PKs.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            dest="batch_size",
            help="Number of videos to index per batch (default: 100).",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        from src.apps.search.conf import search_settings
        from src.apps.search.services.indexer import (
            create_index,
            drop_and_recreate_index,
        )

        # Check engine
        if search_settings.is_disabled:
            self.stdout.write(
                self.style.WARNING("SEARCH_ENGINE is disabled. Nothing to index.")
            )
            return

        if not search_settings.is_redis:
            self.stdout.write(
                self.style.WARNING(
                    "SEARCH_ENGINE is not 'redis'. Only Redis Search indexing is supported."
                )
            )
            return

        # Activate language (same as V4)
        translation.activate(getattr(settings, "LANGUAGE_CODE", "fr"))

        # --drop: drop + recreate index
        if options["drop"]:
            self.stdout.write("Dropping and recreating Redis Search index...")
            if drop_and_recreate_index():
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Index '{search_settings.search_index_name}' recreated."
                    )
                )
            else:
                self.stdout.write(self.style.ERROR("Failed to recreate index."))
                return
        else:
            # Ensure index exists (create if needed)
            create_index()

        # --video-id: index specific videos
        if options["video_ids"]:
            self._index_specific(options["video_ids"])
            translation.deactivate()
            return

        # Default: index all published videos
        self._index_all(batch_size=options["batch_size"])
        translation.deactivate()

    def _index_specific(self, video_ids):
        """Re-index a specific list of videos by ID."""
        from src.apps.search.services.indexer import index_video, delete_video_from_index
        from src.apps.video.models import Video

        for vid_id in video_ids:
            try:
                video = Video.objects.select_related(
                    "owner", "type", "cursus", "language", "channel"
                ).get(pk=vid_id)

                if video.status == Video.Status.DRAFT:
                    delete_video_from_index(vid_id)
                    self.stdout.write(
                        self.style.WARNING(
                            f"Video #{vid_id} is a draft → removed from index."
                        )
                    )
                else:
                    if index_video(video):
                        self.stdout.write(self.style.SUCCESS(f"Video #{vid_id} indexed."))
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"Failed to index video #{vid_id}.")
                        )
            except Video.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Video #{vid_id} does not exist."))

    def _index_all(self, batch_size: int = 100):
        """Re-index all published videos in batches."""
        from src.apps.search.services.indexer import index_video
        from src.apps.video.models import Video
        from django.db import reset_queries
        import gc

        # Force DEBUG to False to prevent Django from keeping SQL queries in memory
        settings.DEBUG = False

        # Use prefetch_related to avoid N+1 queries during document building
        qs = (
            Video.objects.select_related("owner", "type", "cursus", "language", "channel")
            .prefetch_related(
                "contributions__contributor",
                "overlays",
                "themes",
                "disciplines",
                "tags",
                "sites",
            )
            .exclude(status=Video.Status.DRAFT)
            .order_by("pk")
        )

        total = qs.count()
        self.stdout.write(f"Starting indexation of {total} videos...")

        indexed = 0
        errors = 0

        # Use iterator() with chunk_size to prevent loading all objects into memory
        for video in qs.iterator(chunk_size=batch_size):
            try:
                index_video(video)
                indexed += 1
            except Exception as exc:
                errors += 1
                logger.error("Error indexing video #%s: %s", video.pk, exc)

            # Print progress and clear memory at the end of each batch
            if indexed % batch_size == 0:
                self.stdout.write(
                    f"  Progress: {indexed}/{total} "
                    f"(indexed: {indexed}, errors: {errors})"
                )
                reset_queries()
                gc.collect()
                time.sleep(1)

        self.stdout.write(
            self.style.SUCCESS(f"Done. {indexed} videos indexed, {errors} errors.")
        )
