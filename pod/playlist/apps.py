from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db import connection
from django.db.models.signals import pre_migrate, post_migrate


FAVORITES_DATA = {}


class PlaylistConfig(AppConfig):
    name = "pod.playlist"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Playlists")

    def ready(self) -> None:
        from . import signals
        pre_migrate.connect(self.save_previous_data, sender=self)
        post_migrate.connect(self.send_previous_data, sender=self)

    def execute_query(self, query, mapping_dict):
        """
        Execute the given query and populate the mapping dictionary with the results.

        Args:
            query (str): The given query to execute
            mapping_dict (dict): The dictionary.
        """
        try:
            with connection.cursor() as c:
                c.execute(query)
                results = c.fetchall()
                for res in results:
                    mapping_dict["%s" % res[0]] = [res[i] for i in range(1, len(res))]
        except Exception as e:
            print(e)
            pass

    def save_previous_data(self, sender, **kwargs):
        """Save previous data from favorites table."""
        self.execute_query(
            """
            SELECT id, date_added, rank, owner_id, video_id
            FROM favorite_favorite
            GROUP BY owner_id ASC
            """,
            FAVORITES_DATA
        )

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
        for data_lists in FAVORITES_DATA.values():
            new_favorites_playlist = Playlist.objects.create(
                name="Favorites",
                description=_("Your favorites videos."),
                visibility="private",
                autoplay=True,
                owner=data_lists[0]["owner_id"],
                editable=False
            )

            for favorites_datas in data_lists:
                date_added, rank, _, video_id = favorites_datas
                PlaylistContent.objects.create(
                    date_added=date_added,
                    rank=rank,
                    playlist=new_favorites_playlist,
                    video_id=video_id
                )

        print("create_new_favorites --> OK")
