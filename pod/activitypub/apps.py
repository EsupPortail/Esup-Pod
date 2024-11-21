from django.apps import AppConfig
from django.db.models.signals import post_delete, pre_save, post_save
from django.conf import settings

USE_ACTIVITYPUB = getattr(settings, "USE_ACTIVITYPUB", False)


class ActivitypubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pod.activitypub"

    def ready(self):
        """Set signals on videos for activitypub broadcasting."""
        from pod.video.models import Video

        from .signals import on_video_delete, on_video_save, on_video_pre_save

        if USE_ACTIVITYPUB:
            pre_save.connect(on_video_pre_save, sender=Video)
            post_save.connect(on_video_save, sender=Video)
            post_delete.connect(on_video_delete, sender=Video)
