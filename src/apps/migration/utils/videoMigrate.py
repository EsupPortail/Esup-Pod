"""Esup-Pod -
Migration des vidéos webtv -> Pod (métadonnées uniquement, pas de copie
physique des fichiers).

- thumbnail/licence volontairement absents : webtv n'a pas de vraies
  miniatures dans cet export, et les "licences" webtv sont en réalité des
  documents d'autorisation (voir documentMigrate.py), pas des licences
  Creative Commons.
- Résolution vidéo toujours en 1080p : le flag is_hd de webtv n'est pas
  fiable (souvent faux même quand le fichier 1080p existe).
- Une transaction par vidéo : une erreur sur une ligne ne doit pas faire
  échouer tout le run.
"""

from html import unescape
from html.parser import HTMLParser

from django.db import IntegrityError, connections, transaction
from django.utils import timezone

from src.apps.migration.models import UserMapping, VideoMapping
from src.apps.video.models import Video

# -------------------------
# MAPPINGS SAFE
# -------------------------

BROADCAST_MAP = {
    "public": "PU",
    "unlisted": "RE",
}

ENCODING_MAP = {
    "Successful": "DO",
    "Processing": "PR",
    "Failed": "ER",
}
# Statut vide/inconnu (~9 lignes dans le dump webtv) -> erreur plutôt que "Terminé".
DEFAULT_ENCODING_STATUS = "ER"


# -------------------------
# HTML STRIPPER
# -------------------------


class _HTMLStripper(HTMLParser):
    """Migration helper."""

    def __init__(self):
        """Migration helper."""
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        self._parts.append(data)

    def get_text(self):
        return " ".join(self._parts).strip()


def strip_html(text: str) -> str:
    """Migration helper."""
    if not text:
        return ""
    text = unescape(text)
    stripper = _HTMLStripper()
    stripper.feed(text)
    return stripper.get_text()


# -------------------------
# DATE SAFE PARSING
# -------------------------


def _parse_created_date(data):
    """Migration helper."""
    now = timezone.now()

    datecreated = data.get("datecreated")
    if datecreated:
        try:
            return timezone.make_aware(datecreated)
        except Exception:
            return datecreated

    date_added = data.get("date_added")
    if date_added and str(date_added) != "0000-00-00 00:00:00":
        try:
            return timezone.make_aware(date_added)
        except Exception:
            return date_added

    return now


# -------------------------
# LEGACY PATH BUILDER
# -------------------------


def _build_legacy_video_path(file_directory, file_name, resolution="1080"):
    """Migration helper."""
    # La copie physique devra vérifier l'existence réelle du fichier et
    # retomber sur 720/480/240 si le 1080p est absent.
    if not file_directory or not file_name:
        return ""
    return f"{file_directory}/{file_name}-{resolution}.mp4"


# -------------------------
# ROW -> VIDEO FIELDS
# -------------------------


def _parse_video_fields(data):
    """Construit les arguments de Video.objects.create() à partir d'une ligne webtv."""
    try:
        duration = int(float(data.get("duration") or 0))
    except Exception:
        duration = 0

    try:
        views = int(data.get("views") or 0)
    except Exception:
        views = 0

    active = str(data.get("active") or "").lower() in ["1", "yes", "true"]
    broadcast = (data.get("broadcast") or "").lower()
    status = BROADCAST_MAP.get(broadcast, "DR") if active else "DR"

    encoding_status = ENCODING_MAP.get(data.get("status"), DEFAULT_ENCODING_STATUS)

    disable_comment = str(data.get("allow_comments") or "").lower() != "yes"

    legacy_path = _build_legacy_video_path(
        data.get("file_directory"), data.get("file_name")
    )

    return {
        "title": (data.get("title") or "Sans titre").strip()[:250],
        "description": strip_html(data.get("description") or ""),
        "video_file": legacy_path,
        "duration": duration,
        "view_count": views,
        "status": status,
        "encoding_status": encoding_status,
        "disable_comment": disable_comment,
        "password": data.get("video_password") or None,
        "created_at": _parse_created_date(data),
    }


# -------------------------
# MAIN MIGRATION
# -------------------------


def videoMigrate(self, *args, **kwargs):
    """Migration helper."""
    limit = kwargs.get("limit", 0)

    user_mapping = {m.old_id: m.new_id for m in UserMapping.objects.all()}

    migrated_ids = set(VideoMapping.objects.values_list("old_id", flat=True))

    self.stdout.write(f"Users mappés: {len(user_mapping)}")
    self.stdout.write(f"Videos déjà migrées: {len(migrated_ids)}")

    with connections["webtv"].cursor() as cursor:
        query = """
            SELECT videoid, userid, file_name, file_directory, title, description,
                   views, duration, datecreated, date_added, broadcast,
                   allow_comments, video_password, active, tags, is_hd, status
            FROM Ze4fg_video
        """

        if limit > 0:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        columns = [c[0] for c in cursor.description]
        rows = cursor.fetchall()

    self.stdout.write(f"{len(rows)} vidéos trouvées")

    created_count = 0
    skipped_count = 0
    error_count = 0
    already_migrated = 0

    for row in rows:

        data = dict(zip(columns, row))
        old_id = data["videoid"]

        if old_id in migrated_ids:
            already_migrated += 1
            continue

        new_user_id = user_mapping.get(data["userid"])
        if not new_user_id:
            skipped_count += 1
            continue

        try:
            with transaction.atomic():
                video = Video.objects.create(
                    **_parse_video_fields(data),
                    is_video=True,
                    is_360=False,
                    is_auth_required=False,
                    allow_downloading=False,
                    updated_at=timezone.now(),
                    owner_id=new_user_id,
                    transcript_language="",
                )

                VideoMapping.objects.create(old_id=old_id, new_id=video.id)

                raw_tags = unescape(data.get("tags") or "")
                if raw_tags:
                    tag_list = [t.strip() for t in raw_tags.split(",") if t.strip()]
                    video.tags.set(tag_list)

                created_count += 1

        except IntegrityError:
            # Déjà migrée par un run concurrent/précédent entre temps.
            already_migrated += 1

        except Exception as e:
            error_count += 1
            self.stdout.write(self.style.ERROR(f"[ERROR VIDEO {old_id}] {e}"))

    self.stdout.write(
        self.style.SUCCESS(
            f"Terminé — {created_count} créées, "
            f"{already_migrated} déjà migrées, "
            f"{skipped_count} skippées, "
            f"{error_count} erreurs"
        )
    )
