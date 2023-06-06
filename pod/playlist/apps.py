from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PlaylistConfig(AppConfig):
    name = "pod.playlist"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Playlists")

    def ready(self) -> None:
        import pod.playlist.signals
