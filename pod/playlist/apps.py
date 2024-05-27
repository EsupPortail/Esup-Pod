"""Esup-Pod Playlist apps."""

from django.apps import AppConfig
from django.db import connection
from django.db.models.signals import pre_migrate, post_migrate
from django.utils.translation import gettext_lazy as _

FAVORITE_PLAYLIST_NAME = "Favorites"

FAVORITES_DATA = {}
PLAYLIST_INFORMATIONS = {}
PLAYLIST_CONTENTS = {}


class PlaylistConfig(AppConfig):
    name = "pod.playlist"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Playlists")

    def ready(self) -> None:
        from . import signals  # noqa: F401

        pre_migrate.connect(self.save_previous_data, sender=self)
        post_migrate.connect(self.send_previous_data, sender=self)
        post_migrate.connect(self.remove_previous_favorites_table, sender=self)

    def save_previous_data(self, sender, **kwargs) -> None:
        """Save previous data from various database tables."""
        print("Start save_previous_data | playlists")
        self.save_playlists()
        if len(PLAYLIST_INFORMATIONS) > 0:
            print("PLAYLIST_INFORMATIONS saved %s playlists" % len(PLAYLIST_INFORMATIONS))

        self.save_playlist_content()
        if len(PLAYLIST_CONTENTS) > 0:
            print(
                "PLAYLIST_CONTENTS saved %s videos in playlists" % len(PLAYLIST_CONTENTS)
            )

        self.save_favorites()
        if len(FAVORITES_DATA) > 0:
            print("FAVORITES_DATA saved for %s persons" % len(FAVORITES_DATA))
        print("save_previous_data --> OK | playlists")

    def save_favorites(self) -> None:
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

    def execute_query(self, query, mapping_dict) -> None:
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
                    id = res[0]
                    mapping_dict[id] = [res[i] for i in range(1, len(res))]
        except Exception as e:
            print(e)
            pass

    def save_playlists(self) -> None:
        """Save previous data from playlists table."""
        self.execute_query(
            """
            SELECT id, title, description, visible, owner_id
            FROM playlist_playlist
            ORDER BY id
            """,
            PLAYLIST_INFORMATIONS,
        )

    def save_playlist_content(self) -> None:
        """Save previous data from playlistelement table."""
        self.execute_query(
            """
            SELECT id, position, playlist_id, video_id
            FROM playlist_playlistelement
            ORDER BY id
            """,
            PLAYLIST_CONTENTS,
        )

    def send_previous_data(self, sender, **kwargs) -> None:
        """Send previous data from various database tables."""
        print("Start send_previous_data | playlists")

        if len(PLAYLIST_INFORMATIONS) > 0:
            self.update_playlists()

        if len(PLAYLIST_CONTENTS) > 0:
            self.add_playlists_contents()

        self.create_new_favorites()
        print("send_previous_data --> OK | playlists")

    def create_new_favorites(self) -> None:
        """Create favorites records from existing datas or create favorites playlist."""
        from pod.playlist.models import Playlist, PlaylistContent
        from django.utils.translation import gettext_lazy as _
        from django.contrib.auth.models import User
        from django.contrib.sites.models import Site
        from django.utils import timezone
        from django.db.models import Max
        from django.template.defaultfilters import slugify

        print("Start create_new_favorites")
        # Add Favorites playlist for users without favorites
        users_without_favorites = User.objects.exclude(id__in=FAVORITES_DATA.keys())
        users_with_favorite_playlist = set(
            Playlist.objects.filter(name=FAVORITE_PLAYLIST_NAME).values_list(
                "owner_id", flat=True
            )
        )
        playlist_id = Playlist.objects.aggregate(Max("id"))["id__max"]
        playlist_id = playlist_id + 1 if playlist_id is not None else 1
        favorites_playlists_to_create = []
        for user in users_without_favorites:
            if user.id not in users_with_favorite_playlist:
                playlist = Playlist(
                    slug=f"{playlist_id}-{slugify(FAVORITE_PLAYLIST_NAME)}",
                    name=FAVORITE_PLAYLIST_NAME,
                    owner=user,
                    site=Site.objects.get_current(),
                    description=_("Your favorites videos."),
                    visibility="private",
                    autoplay=True,
                    editable=False,
                )
                favorites_playlists_to_create.append(playlist)
                playlist_id += 1
        Playlist.objects.bulk_create(favorites_playlists_to_create, batch_size=1000)

        # Converting previous favorites to new system
        for owner_id, data_lists in FAVORITES_DATA.items():
            new_favorites_playlist = Playlist.objects.create(
                name=FAVORITE_PLAYLIST_NAME,
                description=_("Your favorites videos."),
                visibility="private",
                autoplay=True,
                owner_id=owner_id,
                editable=False,
            )

            for favorites_datas in data_lists:
                date_added, rank, video_id = favorites_datas
                PlaylistContent.objects.create(
                    date_added=timezone.make_aware(date_added),
                    rank=rank,
                    playlist=new_favorites_playlist,
                    video_id=video_id,
                )

        print("create_new_favorites --> OK")

    def update_playlists(self) -> None:
        """Update previous playlist table."""
        from pod.playlist.models import Playlist

        print("Start update_playlists")
        playlists_to_update = []

        for playlist_id, playlist_datas in PLAYLIST_INFORMATIONS.items():
            title, description, visible, owner_id = playlist_datas
            visibility = "private" if visible == 0 else "public"
            try:
                playlist = Playlist.objects.get(id=playlist_id)
            except Playlist.DoesNotExist:
                print("playlist not exists")
                continue

            playlist.name = title
            playlist.description = description
            playlist.visibility = visibility
            playlist.owner_id = owner_id
            playlist.autoplay = True
            playlist.editable = True

            playlists_to_update.append(playlist)

        Playlist.objects.bulk_update(
            playlists_to_update,
            fields=[
                "name",
                "description",
                "visibility",
                "owner_id",
                "autoplay",
                "editable",
            ],
        )
        print("update_playlists --> OK")

    def add_playlists_contents(self) -> None:
        """Add playlist content record from existing datas."""
        from pod.playlist.models import PlaylistContent

        print("Start add_playlists_contents")
        content_list_to_bulk = []
        for content_datas in PLAYLIST_CONTENTS.values():
            position, playlist_id, video_id = content_datas

            content_list_to_bulk.append(
                PlaylistContent(rank=position, playlist_id=playlist_id, video_id=video_id)
            )
        PlaylistContent.objects.bulk_create(content_list_to_bulk, batch_size=1000)
        print("add_playlists_contents --> OK")

    def remove_previous_favorites_table(self, sender, **kwargs) -> None:
        """Remove the previous favorites table."""
        try:
            with connection.cursor() as c:
                c.execute("DROP TABLE favorite_favorite")
        except Exception as e:
            print(e)
            pass
        print("Remove previous table: favorite_favorite --> OK")
