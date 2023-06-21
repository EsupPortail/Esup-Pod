from django.apps import AppConfig
from django.db import connection
from django.db.models.signals import pre_migrate, post_migrate
from django.utils.translation import gettext_lazy as _

FAVORITES_DATA = {}


class PlaylistConfig(AppConfig):
    name = "pod.playlist"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Playlists")

    def ready(self) -> None:
        from . import signals
        pre_migrate.connect(self.save_previous_data, sender=self)
        post_migrate.connect(self.send_previous_data, sender=self)

    def save_previous_data(self, sender, **kwargs):
        """Save previous data from favorites table."""
        try:
            with connection.cursor() as c:
                c.execute(
                    """
                    SELECT owner_id, date_added, rank, video_id
                    FROM favorite_favorite
                    ORDER BY owner_id
                    """
                )
                results = c.fetchall()
                for res in results:
                    owner_id = res[0]
                    data = [res[i] for i in range(1, len(res))]
                    FAVORITES_DATA.setdefault(owner_id, []).append(data)
        except Exception as e:
            print(e)

        if len(FAVORITES_DATA) > 0:
            print("FAVORITES_DATA saved for %s persons" % len(FAVORITES_DATA))

    def send_previous_data(self, sender, **kwargs):
        """Send previous data from favorites table."""
        if len(FAVORITES_DATA) > 0:
            print("Sending datas")
            self.import_data()
        else:
            return

    def import_data(self):
        if len(FAVORITES_DATA) > 0:
            self.create_new_favorites()

    def create_new_favorites(self):
        from pod.playlist.models import Playlist, PlaylistContent
        from django.utils.translation import gettext_lazy as _
        for owner_id, data_lists in FAVORITES_DATA.items():
            new_favorites_playlist = Playlist.objects.create(
                name="Favorites",
                description=_("Your favorites videos."),
                visibility="private",
                autoplay=True,
                owner_id=owner_id,
                editable=False
            )

            for favorites_datas in data_lists:
                date_added, rank, video_id = favorites_datas
                PlaylistContent.objects.create(
                    date_added=date_added,
                    rank=rank,
                    playlist=new_favorites_playlist,
                    video_id=video_id
                )

        print("create_new_favorites --> OK")
