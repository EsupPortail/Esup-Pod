"""Esup-Pod -
Migration des collections webtv -> Pod (Channels, Themes, Favoris, Playlists).

Ze4fg_collections/Ze4fg_collection_categories sont quasi vides sur ce dump
(les vraies données de classification sont dans Ze4fg_vdogrouping, migrées
par groupingMigrate.py) — ce script reste utile si elles sont un jour
peuplées ailleurs.

Un mapping Theme peut pointer vers un Theme supprimé entre-temps : plutôt que
de planter tout le run, le mapping périmé est supprimé et la catégorie est
recréée (voir _resolve_or_recreate_theme_mapping).
"""

from html import unescape

from django.db import connections, transaction
from src.apps.collection.models import Channel, Favorite, Playlist, Theme
from src.apps.collection.models.Playlist import PlaylistItem
from src.apps.migration.models import (
    UserMapping,
    VideoMapping,
    ChannelMapping,
    PlaylistMapping,
    ThemeMapping,
)


def _migrate_channels(self, collections, contributors_by_collection, user_mapping):
    """Migration helper."""
    created = skipped = errors = 0

    for data in collections:
        old_id = data["collection_id"]

        if ChannelMapping.objects.filter(old_id=old_id).exists():
            self.stdout.write(f"Skip Channel {old_id}: déjà migré")
            skipped += 1
            continue

        new_user_id = user_mapping.get(data["userid"])
        if not new_user_id:
            self.stdout.write(
                self.style.WARNING(
                    f"Skip Channel {old_id}: user {data['userid']} introuvable"
                )
            )
            skipped += 1
            continue

        try:
            with transaction.atomic():
                title = (data["collection_name"] or "Sans titre").strip()[:250]
                description = unescape(data["collection_description"] or "")
                is_public = (data["broadcast"] or "").strip().lower() == "public"

                channel = Channel.objects.create(
                    title=title,
                    description=description,
                    owner_id=new_user_id,
                    is_public=is_public,
                    old_v4_id=old_id,
                )

                for contrib in contributors_by_collection.get(old_id, []):
                    new_contrib_id = user_mapping.get(contrib["userid"])
                    if new_contrib_id:
                        channel.collaborators.add(new_contrib_id)

                ChannelMapping.objects.create(old_id=old_id, new_id=channel.id)
                created += 1
                self.stdout.write(f"Channel créé: [{old_id}] {title[:50]}")

        except Exception as e:
            errors += 1
            self.stdout.write(self.style.ERROR(f"Erreur Channel {old_id}: {e}"))

    return created, skipped, errors


def _resolve_or_recreate_theme_mapping(self, old_cat_id):
    """Retourne le Theme existant pour old_cat_id, ou None s'il faut le (re)créer."""
    mapping = ThemeMapping.objects.filter(old_id=old_cat_id).first()
    if not mapping:
        return None

    theme = Theme.objects.filter(id=mapping.new_id).first()
    if theme:
        return theme

    self.stdout.write(
        self.style.WARNING(
            f"Mapping Theme {old_cat_id} orphelin (Theme {mapping.new_id} "
            f"introuvable) — re-création."
        )
    )
    mapping.delete()
    return None


def _migrate_themes(self, categories):
    """Migration helper."""
    created = skipped = errors = 0
    theme_map = {}  # old_cat_id -> Theme (pour relier les parents ensuite)

    # Passe 1 : création sans parent
    for cat in categories:
        old_cat_id = cat["category_id"]

        existing_theme = _resolve_or_recreate_theme_mapping(self, old_cat_id)
        if existing_theme:
            theme_map[old_cat_id] = existing_theme
            self.stdout.write(f"Skip Theme {old_cat_id}: déjà migré")
            skipped += 1
            continue

        try:
            with transaction.atomic():
                title = (cat["category_name"] or "Sans nom").strip()[:250]
                description = unescape(cat["category_desc"] or "")

                theme = Theme.objects.create(
                    title=title,
                    description=description,
                    old_v4_id=old_cat_id,
                )
                theme_map[old_cat_id] = theme
                ThemeMapping.objects.create(old_id=old_cat_id, new_id=theme.id)
                created += 1
                self.stdout.write(f"Theme créé: [{old_cat_id}] {title[:50]}")

        except Exception as e:
            errors += 1
            self.stdout.write(self.style.ERROR(f"Erreur Theme {old_cat_id}: {e}"))

    # Passe 2 : liaison des parents
    for cat in categories:
        old_cat_id = cat["category_id"]
        parent_id = cat["parent_id"]
        theme = theme_map.get(old_cat_id)
        parent_theme = theme_map.get(parent_id)

        if theme and parent_theme and parent_id != old_cat_id:
            try:
                theme.parent = parent_theme
                theme.save()
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Impossible de lier parent du Theme {old_cat_id}: {e}"
                    )
                )

    return created, skipped, errors


def _migrate_favorites(self, favorites, user_mapping, video_mapping):
    """Migration helper."""
    created = skipped = errors = 0

    for data in favorites:
        old_video_id = data["videoid"]
        new_user_id = user_mapping.get(data["userid"])
        new_video_id = video_mapping.get(old_video_id)

        if not new_user_id:
            self.stdout.write(
                self.style.WARNING(
                    f"Skip Favori video {old_video_id}: user {data['userid']} introuvable"
                )
            )
            skipped += 1
            continue

        if not new_video_id:
            self.stdout.write(
                self.style.WARNING(f"Skip Favori video {old_video_id}: video introuvable")
            )
            skipped += 1
            continue

        try:
            with transaction.atomic():
                _, was_created = Favorite.objects.get_or_create(
                    user_id=new_user_id,
                    video_id=new_video_id,
                )
                if was_created:
                    created += 1

        except Exception as e:
            errors += 1
            self.stdout.write(
                self.style.ERROR(f"Erreur Favori video {old_video_id}: {e}")
            )

    return created, skipped, errors


def _migrate_playlists(
    self, playlists, playlist_items_by_playlist, user_mapping, video_mapping
):
    """Migration helper."""
    created = skipped = errors = 0

    for data in playlists:
        old_playlist_id = data["playlist_id"]

        if PlaylistMapping.objects.filter(old_id=old_playlist_id).exists():
            self.stdout.write(f"Skip Playlist {old_playlist_id}: déjà migrée")
            skipped += 1
            continue

        new_user_id = user_mapping.get(data["userid"])
        if not new_user_id:
            self.stdout.write(
                self.style.WARNING(
                    f"Skip Playlist {old_playlist_id}: user {data['userid']} introuvable"
                )
            )
            skipped += 1
            continue

        try:
            with transaction.atomic():
                title = (data["playlist_name"] or "Sans titre").strip()[:250]
                description = unescape(data["description"] or "")
                is_public = (data["privacy"] or "private").strip().lower() == "public"

                playlist = Playlist.objects.create(
                    title=title,
                    description=description,
                    owner_id=new_user_id,
                    is_public=is_public,
                    old_v4_id=old_playlist_id,
                )

                for item in playlist_items_by_playlist.get(old_playlist_id, []):
                    new_video_id = video_mapping.get(item["object_id"])
                    if new_video_id:
                        PlaylistItem.objects.get_or_create(
                            playlist=playlist,
                            video_id=new_video_id,
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Video {item['object_id']} introuvable "
                                f"pour playlist {old_playlist_id}"
                            )
                        )

                PlaylistMapping.objects.create(
                    old_id=old_playlist_id,
                    new_id=playlist.id,
                )
                created += 1
                self.stdout.write(f"Playlist créée: [{old_playlist_id}] {title[:50]}")

        except Exception as e:
            errors += 1
            self.stdout.write(self.style.ERROR(f"Erreur Playlist {old_playlist_id}: {e}"))

    return created, skipped, errors


def _fetch_collections(cursor, limit):
    """Migration helper."""
    query = """
        SELECT
            collection_id, collection_name, collection_description,
            userid, broadcast, date_added, active
        FROM Ze4fg_collections
    """
    if limit > 0:
        query += f" LIMIT {limit}"
    cursor.execute(query)
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _fetch_contributors_by_collection(cursor):
    """Migration helper."""
    cursor.execute("""
        SELECT collection_id, userid, can_edit
        FROM Ze4fg_collection_contributors
    """)
    cols = [col[0] for col in cursor.description]
    contributors_by_collection = {}
    for row in cursor.fetchall():
        d = dict(zip(cols, row))
        contributors_by_collection.setdefault(d["collection_id"], []).append(d)
    return contributors_by_collection


def _fetch_categories(cursor):
    """Migration helper."""
    cursor.execute("""
        SELECT category_id, parent_id, category_name, category_desc
        FROM Ze4fg_collection_categories
    """)
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _fetch_favorites(cursor):
    """Migration helper."""
    cursor.execute("""
        SELECT videoid, userid, date_added
        FROM Ze4fg_video_favourites
    """)
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _fetch_playlists(cursor):
    """Migration helper."""
    cursor.execute("""
        SELECT playlist_id, playlist_name, userid,
               description, privacy, allow_comments, date_added
        FROM Ze4fg_playlists
    """)
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _fetch_playlist_items_by_playlist(cursor):
    """Migration helper."""
    cursor.execute("""
        SELECT object_id, playlist_id, date_added
        FROM Ze4fg_playlist_items
        WHERE playlist_item_type = 'video'
    """)
    cols = [col[0] for col in cursor.description]
    playlist_items_by_playlist = {}
    for row in cursor.fetchall():
        d = dict(zip(cols, row))
        playlist_items_by_playlist.setdefault(d["playlist_id"], []).append(d)
    return playlist_items_by_playlist


def collectionMigrate(self, *args, **kwargs):
    """Migration helper."""
    limit = kwargs.get("limit", 0)

    user_mapping = {m.old_id: m.new_id for m in UserMapping.objects.all()}
    video_mapping = {m.old_id: m.new_id for m in VideoMapping.objects.all()}
    self.stdout.write(
        f"Mapping chargé: {len(user_mapping)} users, {len(video_mapping)} videos"
    )

    with connections["webtv"].cursor() as cursor:
        collections = _fetch_collections(cursor, limit)
        self.stdout.write(f"{len(collections)} collections trouvées")

        contributors_by_collection = _fetch_contributors_by_collection(cursor)

        categories = _fetch_categories(cursor)
        self.stdout.write(f"{len(categories)} catégories trouvées")

        favorites = _fetch_favorites(cursor)
        self.stdout.write(f"{len(favorites)} favoris trouvés")

        playlists = _fetch_playlists(cursor)
        self.stdout.write(f"{len(playlists)} playlists trouvées")

        playlist_items_by_playlist = _fetch_playlist_items_by_playlist(cursor)

    self.stdout.write("--- Migration Channels ---")
    c_created, c_skipped, c_errors = _migrate_channels(
        self, collections, contributors_by_collection, user_mapping
    )

    self.stdout.write("--- Migration Themes ---")
    t_created, t_skipped, t_errors = _migrate_themes(self, categories)

    self.stdout.write("--- Migration Favorites ---")
    f_created, f_skipped, f_errors = _migrate_favorites(
        self, favorites, user_mapping, video_mapping
    )

    self.stdout.write("--- Migration Playlists ---")
    p_created, p_skipped, p_errors = _migrate_playlists(
        self, playlists, playlist_items_by_playlist, user_mapping, video_mapping
    )

    created_count = c_created + t_created + f_created + p_created
    skipped_count = c_skipped + t_skipped + f_skipped + p_skipped
    error_count = c_errors + t_errors + f_errors + p_errors

    self.stdout.write(
        self.style.SUCCESS(
            f"Terminé — {created_count} créés, "
            f"{skipped_count} skippés, "
            f"{error_count} erreurs"
        )
    )
