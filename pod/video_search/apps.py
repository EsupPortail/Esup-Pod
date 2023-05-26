from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VideoSearchConfig(AppConfig):
    name = "pod.video_search"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Video search")
