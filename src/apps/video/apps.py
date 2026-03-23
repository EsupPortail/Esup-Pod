"""
Esup-Pod - Video application configuration.
"""

from django.apps import AppConfig


class VideoConfig(AppConfig):
    """
    Esup-Pod - Configuration for the video app.
    """

    name = "src.apps.video"
    label = "video"
    verbose_name = "Video Management"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import src.apps.video.signals  # noqa
