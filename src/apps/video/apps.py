"""
Esup-Pod - Video application configuration.
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate


def sync_metadata(sender, **kwargs):
    """Sync Cursus, Language, and License from config defaults to DB."""
    try:
        from src.apps.video.models import Language, License, Cursus
        from src.apps.video.conf import video_settings

        for order, item in enumerate(video_settings.languages):
            Language.objects.get_or_create(
                slug=item["value"],
                defaults={"name": item["label"], "order": order},
            )

        for order, item in enumerate(video_settings.licenses):
            License.objects.get_or_create(
                slug=item["value"],
                defaults={"name": item["label"], "order": order},
            )

        for order, item in enumerate(video_settings.cursus):
            Cursus.objects.get_or_create(
                slug=item["value"],
                defaults={"name": item["label"], "order": order},
            )
    except Exception:
        pass


class VideoConfig(AppConfig):
    """
    Configuration for the video app.
    """

    name = "src.apps.video"
    label = "video"
    verbose_name = "Video Management"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        """Connects signals and performs initialization on app startup."""
        import src.apps.video.signals  # noqa: F401

        post_migrate.connect(sync_metadata, sender=self)
