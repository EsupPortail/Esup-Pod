"""
Esup-Pod - Redis cache warm-up management command.

Equivalent to V4: pod/video/management/commands/cache_video_data.py

Pre-loads the most frequently accessed data into Redis (DB 1):
  - Video metadata (licenses, cursus, languages, statuses)
  - Clears stale search caches (pod:search:*)

Usage:
    python manage.py warm_cache
    python manage.py warm_cache --clear-only
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    """Pre-load the Redis cache with static video data — equivalent to V4 cache_video_data."""

    help = (
        "Pre-load the Redis cache (DB 1) with static video data. "
        "Equivalent to the V4 cache_video_data management command."
    )

    def add_arguments(self, parser):
        """Add optional --clear-only argument to skip cache preloading."""
        parser.add_argument(
            "--clear-only",
            action="store_true",
            help="Clear the cache only, without reloading it.",
        )

    def handle(self, *args, **options):
        """Clear stale Redis caches and optionally preload static video metadata."""
        self.stdout.write("🗑️  Clearing stale caches...")

        # Delete known cache keys
        keys_to_delete = ["pod:video:metadata"]
        cache.delete_many(keys_to_delete)
        self.stdout.write(self.style.WARNING(f"   Deleted: {keys_to_delete}"))

        # Clear search caches by pattern (django-redis only)
        try:
            cache.delete_pattern("pod:search:*")
            self.stdout.write(self.style.WARNING("   Deleted: pod:search:* (pattern)"))
        except AttributeError:
            self.stdout.write(
                self.style.NOTICE(
                    "   ⚠️  delete_pattern not supported (non-Redis backend) — skipped."
                )
            )

        if options["clear_only"]:
            self.stdout.write(self.style.SUCCESS("✅ Cache cleared (--clear-only)."))
            return

        # --- Preload video metadata ---
        self.stdout.write("🔄 Pre-loading video cache...")

        try:
            from src.apps.video.models import License, Cursus, Language, Video

            metadata = {
                "licenses": [
                    {"value": lic.slug, "label": lic.name}
                    for lic in License.objects.all()
                ],
                "cursus": [
                    {"value": c.slug, "label": c.name} for c in Cursus.objects.all()
                ],
                "statuses": [
                    {"value": c[0], "label": c[1]} for c in Video.Status.choices
                ],
                "languages": [
                    {"value": lang.slug, "label": lang.name}
                    for lang in Language.objects.all()
                ],
            }
            cache.set("pod:video:metadata", metadata, timeout=600)

            self.stdout.write(
                self.style.SUCCESS(
                    f"   ✅ pod:video:metadata — "
                    f"{len(metadata['licenses'])} licenses, "
                    f"{len(metadata['cursus'])} cursus, "
                    f"{len(metadata['languages'])} languages"
                )
            )

        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"   ❌ Error during preload: {exc}"))

        self.stdout.write(self.style.SUCCESS("\n✅ Redis cache successfully pre-loaded."))
        self.stdout.write(
            self.style.NOTICE(
                "💡 Tip: add this command to cron to keep the cache warm:\n"
                "   */10 * * * * python manage.py warm_cache"
            )
        )
