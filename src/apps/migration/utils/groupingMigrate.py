"""Esup-Pod -
Migration of webtv groupings -> Pod (Channels and Themes).

Ze4fg_vdogrouping is the actual webtv classification system (used much more
than Ze4fg_collections/Ze4fg_collection_categories, which are nearly empty in
this dump): groupings of type "Collection" become Channels, while those of
type "Thematic" become Themes.

- Channel: Video.channel is a simple ForeignKey (one per video).
  A video in several webtv Collections keeps only the first one
  (smallest id); the others are logged rather than silently discarded.
- Theme: many-to-many relationship through ThemeItem, so no data can be lost.
"""

from html import unescape

from django.contrib.auth import get_user_model
from django.db import connections, transaction

from src.apps.collection.models import Channel, Theme
from src.apps.collection.models.Theme import ThemeItem
from src.apps.migration.models import GroupingMapping, VideoMapping
from src.apps.video.models import Video

COLLECTION_TYPE_NAME = "collection"


def _fetch_grouping_type_ids(cursor):
    """Return the Ze4fg_vdogrouping_type id whose name is "Collection"."""
    cursor.execute("SELECT id, name FROM Ze4fg_vdogrouping_type")
    collection_type_id = None
    for type_id, name in cursor.fetchall():
        if (name or "").strip().lower() == COLLECTION_TYPE_NAME:
            collection_type_id = type_id
    return collection_type_id


def _fetch_groupings(cursor):
    """Migration helper."""
    cursor.execute("""
        SELECT id, grouping_type_id, name, description, private
        FROM Ze4fg_vdogrouping
    """)
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _fetch_video_groupings(cursor):
    """Migration helper."""
    cursor.execute("SELECT video_id, vdogrouping_id FROM Ze4fg_video_grouping")
    return cursor.fetchall()


def _group_videos_by_grouping(video_groupings):
    """Migration helper."""
    grouping_videos = {}
    for video_id, grouping_id in video_groupings:
        grouping_videos.setdefault(grouping_id, []).append(video_id)
    for old_ids in grouping_videos.values():
        old_ids.sort()
    return grouping_videos


def _resolve_channel_owner(old_video_ids, video_mapping, fallback_owner_id):
    """The owner of a migrated Channel is the owner of its oldest source video."""
    for old_video_id in old_video_ids:
        new_video_id = video_mapping.get(old_video_id)
        if not new_video_id:
            continue
        video = Video.objects.filter(id=new_video_id).values("owner_id").first()
        if video:
            return video["owner_id"]
    return fallback_owner_id


def _migrate_channels(self, groupings, grouping_videos, video_mapping, fallback_owner_id):
    """Migration helper."""
    created = skipped = errors = 0
    grouping_map = {}

    for g in groupings:
        old_id = g["id"]

        existing = GroupingMapping.objects.filter(old_id=old_id).first()
        if existing:
            grouping_map[old_id] = existing.new_id
            skipped += 1
            continue

        try:
            with transaction.atomic():
                owner_id = _resolve_channel_owner(
                    grouping_videos.get(old_id, []), video_mapping, fallback_owner_id
                )
                channel = Channel.objects.create(
                    title=(g["name"] or "Untitled").strip()[:250],
                    description=unescape(g["description"] or ""),
                    owner_id=owner_id,
                    is_public=not bool(g["private"]),
                    old_v4_id=old_id,
                )
                GroupingMapping.objects.create(
                    old_id=old_id,
                    new_id=channel.id,
                    target_type=GroupingMapping.TARGET_CHANNEL,
                )
                grouping_map[old_id] = channel.id
                created += 1
                self.stdout.write(f"Channel created: [{old_id}] {channel.title[:50]}")

        except Exception as e:
            errors += 1
            self.stdout.write(
                self.style.ERROR(f"Channel error (grouping {old_id}): {e}")
            )

    return created, skipped, errors, grouping_map


def _migrate_themes(self, groupings):
    """Migration helper."""
    created = skipped = errors = 0
    grouping_map = {}

    for g in groupings:
        old_id = g["id"]

        existing = GroupingMapping.objects.filter(old_id=old_id).first()
        if existing:
            grouping_map[old_id] = existing.new_id
            skipped += 1
            continue

        try:
            with transaction.atomic():
                theme = Theme.objects.create(
                    title=(g["name"] or "Unnamed").strip()[:250],
                    description=unescape(g["description"] or ""),
                    old_v4_id=old_id,
                )
                GroupingMapping.objects.create(
                    old_id=old_id,
                    new_id=theme.id,
                    target_type=GroupingMapping.TARGET_THEME,
                )
                grouping_map[old_id] = theme.id
                created += 1
                self.stdout.write(f"Theme created: [{old_id}] {theme.title[:50]}")

        except Exception as e:
            errors += 1
            self.stdout.write(self.style.ERROR(f"Theme error (grouping {old_id}): {e}"))

    return created, skipped, errors, grouping_map


def _assign_video_channels(
    self, video_groupings, channel_type_id, groupings_by_id, channel_map, video_mapping
):
    """Each video keeps only its smallest-id Collection as Video.channel."""
    video_channel_groupings = {}
    for video_id, grouping_id in video_groupings:
        if (
            groupings_by_id.get(grouping_id, {}).get("grouping_type_id")
            == channel_type_id
        ):
            video_channel_groupings.setdefault(video_id, []).append(grouping_id)

    updated = 0
    conflicts = 0

    for old_video_id, old_grouping_ids in video_channel_groupings.items():
        new_video_id = video_mapping.get(old_video_id)
        if not new_video_id:
            continue

        old_grouping_ids.sort()
        chosen_id = channel_map.get(old_grouping_ids[0])
        if not chosen_id:
            continue

        if len(old_grouping_ids) > 1:
            conflicts += 1
            self.stdout.write(
                self.style.WARNING(
                    f"Video {old_video_id}: {len(old_grouping_ids)} Collections "
                    f"({old_grouping_ids}) — only the first (grouping "
                    f"{old_grouping_ids[0]}) is kept as the Channel."
                )
            )

        Video.objects.filter(id=new_video_id).update(channel_id=chosen_id)
        updated += 1

    return updated, conflicts


def _assign_video_themes(self, video_groupings, theme_map, video_mapping):
    """Migration helper."""
    created = 0

    for old_video_id, old_grouping_id in video_groupings:
        new_theme_id = theme_map.get(old_grouping_id)
        if new_theme_id is None:
            continue

        new_video_id = video_mapping.get(old_video_id)
        if not new_video_id:
            continue

        try:
            _, was_created = ThemeItem.objects.get_or_create(
                theme_id=new_theme_id,
                video_id=new_video_id,
            )
            if was_created:
                created += 1
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"ThemeItem error video={old_video_id} theme={old_grouping_id}: {e}"
                )
            )

    return created


def groupingMigrate(self, *args, **kwargs):
    """Migration helper."""
    video_mapping = {m.old_id: m.new_id for m in VideoMapping.objects.all()}
    self.stdout.write(f"Mapped videos: {len(video_mapping)}")

    fallback_owner = (
        get_user_model().objects.filter(is_superuser=True).order_by("id").first()
    )
    fallback_owner_id = fallback_owner.id if fallback_owner else None

    with connections["webtv"].cursor() as cursor:
        collection_type_id = _fetch_grouping_type_ids(cursor)
        groupings = _fetch_groupings(cursor)
        video_groupings = _fetch_video_groupings(cursor)

    groupings_by_id = {g["id"]: g for g in groupings}
    channel_groupings = [
        g for g in groupings if g["grouping_type_id"] == collection_type_id
    ]
    theme_groupings = [
        g for g in groupings if g["grouping_type_id"] != collection_type_id
    ]

    self.stdout.write(
        f"{len(groupings)} groupings found "
        f"({len(channel_groupings)} Collections, {len(theme_groupings)} Thematic)"
    )

    grouping_videos = _group_videos_by_grouping(video_groupings)

    self.stdout.write("--- Channel migration (Collections) ---")
    c_created, c_skipped, c_errors, channel_map = _migrate_channels(
        self, channel_groupings, grouping_videos, video_mapping, fallback_owner_id
    )

    self.stdout.write("--- Theme migration (Thematic) ---")
    t_created, t_skipped, t_errors, theme_map = _migrate_themes(self, theme_groupings)

    self.stdout.write("--- Assigning videos -> Channel ---")
    video_updated, conflicts = _assign_video_channels(
        self,
        video_groupings,
        collection_type_id,
        groupings_by_id,
        channel_map,
        video_mapping,
    )

    self.stdout.write("--- Assigning videos -> Themes ---")
    theme_items_created = _assign_video_themes(
        self, video_groupings, theme_map, video_mapping
    )

    self.stdout.write(
        self.style.SUCCESS(
            f"Completed — {c_created} Channels, {t_created} Themes, "
            f"{video_updated} videos assigned to a Channel "
            f"({conflicts} with multiple Collections, only one kept), "
            f"{theme_items_created} Theme links created, "
            f"{c_skipped + t_skipped} groupings already migrated, "
            f"{c_errors + t_errors} errors"
        )
    )
