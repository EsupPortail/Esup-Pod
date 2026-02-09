from django.apps import AppConfig


class VideoConfig(AppConfig):
    name = "src.apps.video"
    label = "video"
    verbose_name = "Gestion Vidéo"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        import src.apps.video.signals  # noqa