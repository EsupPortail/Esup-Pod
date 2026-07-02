from django.db import connections, transaction
from html.parser import HTMLParser
from django.utils.text import slugify
from django.utils import timezone
from html import unescape
from src.apps.video.models import Video
from src.apps.migration.models import UserMapping, VideoMapping


class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        self._parts.append(data)

    def get_text(self):
        return " ".join(self._parts).strip()


def strip_html(text: str) -> str:
    """Retire toutes les balises HTML et décode les entités HTML."""
    if not text:
        return ""
    text = unescape(text)
    stripper = _HTMLStripper()
    stripper.feed(text)
    return stripper.get_text()


BROADCAST_MAP = {
    "public": "PU",
    "unlisted": "RE",
}


def videoMigrate(self, *args, **kwargs):
    limit = kwargs.get("limit", 0)

    mapping = {m.old_id: m.new_id for m in UserMapping.objects.all()}
    self.stdout.write(f"Mapping chargé: {len(mapping)} users")

    with connections["webtv"].cursor() as cursor:
        query = """
            SELECT videoid, userid, file_name, title, description, views,
                   duration, datecreated, date_added, broadcast,
                   allow_comments, video_password, active, tags
            FROM Ze4fg_video
        """
        # WHERE status = 'Successful'
        if limit > 0:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    self.stdout.write(f"{len(rows)} vidéos à migrer")

    created_count = 0
    skipped_count = 0
    error_count = 0

    for row in rows:
        data = dict(zip(columns, row))
        old_video_id = data["videoid"]
        old_user_id = data["userid"]

        try:
            with transaction.atomic():
                new_user_id = mapping.get(old_user_id)
                if not new_user_id:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skip vidéo {old_video_id}: "
                            f"user {old_user_id} introuvable dans le mapping"
                        )
                    )
                    skipped_count += 1
                    continue

                title = unescape(data["title"] or "Sans titre").strip()[:250]
                slug = _unique_slug(title)

                try:
                    duration = int(float(data["duration"] or 0))
                except (ValueError, TypeError):
                    duration = 0

                status = BROADCAST_MAP.get(data["broadcast"], "DR")
                disable_comment = (data["allow_comments"] or "").strip().lower() != "yes"
                #description = strip_html(data["description"] or "")
                description = data["description"] or ""
                video_file = data["file_name"] or ""
                now = timezone.now()
                dateCreation = now

                if data["datecreated"]:
                    dateCreation = timezone.make_aware(data["datecreated"])
                elif data["date_added"] and str(data["date_added"]) != "0000-00-00 00:00:00":
                    dateCreation = timezone.make_aware(data["date_added"])

                video = Video.objects.create(
                    title=title,
                    slug=slug,
                    description=description,
                    video_file=video_file,
                    duration=duration,
                    view_count=int(data["views"]),
                    status=status,
                    encoding_status="DO",
                    is_video=True,
                    is_360=False,
                    is_auth_required=False,
                    disable_comment=disable_comment,
                    allow_downloading=False,
                    password=data["video_password"] or None,
                    created_at=dateCreation,
                    updated_at=now,
                    owner_id=new_user_id,
                    cursus="",
                    language="fr",
                    transcript_language="",
                )

                # Sauvegarde le mapping
                VideoMapping.objects.create(
                    old_id=old_video_id,
                    new_id=video.id,
                )

                # Migre les tags
                raw_tags = unescape(data.get("tags") or "")
                if raw_tags:
                    tag_list = [t.strip() for t in raw_tags.split(",") if t.strip()]
                    video.tags.set(tag_list)

                created_count += 1
                self.stdout.write(f"Créé: [{old_video_id}] {title[:50]}")

        except Exception as e:
            error_count += 1
            self.stdout.write(
                self.style.ERROR(f"Erreur vidéo {old_video_id}: {e}")
            )

    self.stdout.write(
        self.style.SUCCESS(
            f"Terminé — {created_count} créées, "
            f"{skipped_count} skippées, "
            f"{error_count} erreurs"
        )
    )


def _unique_slug(title: str) -> str:
    base_slug = slugify(title)[:240] or "video"
    slug = base_slug
    counter = 1
    while Video.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug