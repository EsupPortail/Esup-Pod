"""
Esup-Pod - WebTV V4 to V5 video migration (metadata only, no physical file copy).
"""

from html import unescape
from html.parser import HTMLParser

from django.db import connections, transaction
from django.utils import timezone
from django.utils.text import slugify

from src.apps.migration.models import UserMapping, VideoMapping
from src.apps.video.models import Video

RESOLUTIONS = ["1080", "720", "480", "240"]

BROADCAST_MAP = {
    "public": "PU",
    "unlisted": "RE",
}


class _HTMLStripper(HTMLParser):
    """Minimal HTML tag stripper used to clean legacy V4 descriptions."""

    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        """Collects text data outside of tags."""
        self._parts.append(data)

    def get_text(self):
        """Returns the concatenated stripped text."""
        return " ".join(self._parts).strip()


def strip_html(text: str) -> str:
    """Removes HTML tags and decodes HTML entities."""
    if not text:
        return ""
    text = unescape(text)
    stripper = _HTMLStripper()
    stripper.feed(text)
    return stripper.get_text()


def _unique_slug(title: str) -> str:
    """Generates a unique slug based on the given title."""
    base_slug = slugify(title)[:240] or "video"
    slug = base_slug
    counter = 1
    while Video.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


def _build_legacy_video_path(file_directory, file_name, resolution="1080"):
    """
    Builds the logical V4 path for a video file, without checking
    physical existence on disk. Used as a placeholder until the
    physical migration step is run separately.
    Pattern: {file_directory}/{file_name}-{resolution}.mp4
    """
    return f"{file_directory}/{file_name}-{resolution}.mp4"


def _parse_created_date(data):
    """Safely parses the video creation date, falling back to now()."""
    now = timezone.now()

    if data["datecreated"]:
        try:
            return timezone.make_aware(data["datecreated"])
        except ValueError:
            return data["datecreated"]  # already aware

    date_added = data.get("date_added")
    if date_added and str(date_added) != "0000-00-00 00:00:00":
        try:
            return timezone.make_aware(date_added)
        except ValueError:
            return date_added

    return now


def videoMigrate(self, *args, **kwargs):
    """
    Migrates WebTV V4 video metadata into Pod V5.
    Physical file copy is NOT performed here — only the logical legacy
    path is stored for later processing by a dedicated file-migration step.
    """
    limit = kwargs.get("limit", 0)

    user_mapping = {m.old_id: m.new_id for m in UserMapping.objects.all()}
    self.stdout.write(f"Mapping chargé: {len(user_mapping)} users")

    migrated_ids = set(VideoMapping.objects.values_list("old_id", flat=True))

    with connections["webtv"].cursor() as cursor:
        query = """
            SELECT videoid, userid, file_name, file_directory, title, description,
                   views, duration, datecreated, date_added, broadcast,
                   allow_comments, video_password, active, tags, is_hd
            FROM Ze4fg_video
            WHERE status = 'Successful'
        """
        if limit > 0:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    self.stdout.write(f"{len(rows)} vidéos à traiter")

    created_count = 0
    skipped_count = 0
    error_count = 0

    for row in rows:
        data = dict(zip(columns, row))
        old_video_id = data["videoid"]
        old_user_id = data["userid"]

        if old_video_id in migrated_ids:
            self.stdout.write(f"Skip vidéo {old_video_id} (déjà migrée)")
            skipped_count += 1
            continue

        new_user_id = user_mapping.get(old_user_id)
        if not new_user_id:
            self.stdout.write(
                self.style.WARNING(
                    f"Skip vidéo {old_video_id}: "
                    f"user {old_user_id} introuvable dans le mapping"
                )
            )
            skipped_count += 1
            continue

        try:
            with transaction.atomic():
                title = unescape(data["title"] or "Sans titre").strip()[:250]

                try:
                    duration = int(float(data["duration"] or 0))
                except (ValueError, TypeError):
                    duration = 0

                try:
                    views = int(data["views"] or 0)
                except (ValueError, TypeError):
                    views = 0

                status = BROADCAST_MAP.get(data["broadcast"], "DR")
                disable_comment = (
                    (data["allow_comments"] or "").strip().lower() != "yes"
                )
                description = strip_html(data["description"] or "")
                created_at = _parse_created_date(data)
                now = timezone.now()

                # Highest resolution available, based on is_hd flag (no disk check)
                source_resolution = "1080" if data["is_hd"] == "yes" else "480"
                legacy_path = _build_legacy_video_path(
                    data["file_directory"], data["file_name"], source_resolution
                )

                video = Video.objects.create(
                    title=title,
                    description=description,
                    video_file=legacy_path,
                    duration=duration,
                    view_count=views,
                    status=status,
                    encoding_status="DO",
                    is_video=True,
                    is_360=False,
                    is_auth_required=False,
                    disable_comment=disable_comment,
                    allow_downloading=False,
                    password=data["video_password"] or None,
                    created_at=created_at,
                    updated_at=now,
                    owner_id=new_user_id,
                    #cursus="",
                    #language="fr",
                    transcript_language="",
                )

                VideoMapping.objects.create(old_id=old_video_id, new_id=video.id)

                raw_tags = unescape(data.get("tags") or "")
                if raw_tags:
                    tag_list = [t.strip() for t in raw_tags.split(",") if t.strip()]
                    video.tags.set(tag_list)

                created_count += 1
                self.stdout.write(
                    f"Créé: [{old_video_id}] {title[:50]} (slug={video.slug})"
                )

        except Exception as e:
            error_count += 1
            self.stdout.write(self.style.ERROR(f"Erreur vidéo {old_video_id}: {e}"))

    self.stdout.write(
        self.style.SUCCESS(
            f"Terminé — {created_count} créées, "
            f"{skipped_count} skippées, "
            f"{error_count} erreurs"
        )
    )