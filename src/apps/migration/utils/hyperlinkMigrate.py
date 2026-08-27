"""Esup-Pod - Migration des liens (hyperliens) webtv -> Pod.

- Les entités HTML du titre sont décodées (ex: "&#8217;" -> apostrophe).
- Une transaction par lien : une erreur sur une ligne ne doit pas faire
  échouer tout le run.
"""

from html import unescape

from django.db import connections, transaction
from src.apps.video.models import VideoHyperlink
from src.apps.migration.models import VideoMapping


def hyperlinkMigrate(self, *args, **kwargs):
    """Migrate hyperlinks from the legacy webtv database to the current database."""

    video_mapping = {m.old_id: m.new_id for m in VideoMapping.objects.all()}

    self.stdout.write(f"Vidéos mappées: {len(video_mapping)}")

    with connections["webtv"].cursor() as cursor:
        cursor.execute("SELECT video_id, link_id FROM Ze4fg_video_links")
        video_links = cursor.fetchall()

    if not video_links:
        self.stdout.write("Aucun lien à migrer")
        return

    link_ids = {link_id for _, link_id in video_links}

    with connections["webtv"].cursor() as cursor:
        placeholders = ",".join(["%s"] * len(link_ids))

        cursor.execute(
            f"""
            SELECT id, title, url
            FROM Ze4fg_links
            WHERE id IN ({placeholders})
            """,
            list(link_ids),
        )

        links = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

    created = 0
    skipped = 0
    errors = 0

    for old_video_id, old_link_id in video_links:

        new_video_id = video_mapping.get(old_video_id)
        link_data = links.get(old_link_id)

        if not new_video_id or not link_data:
            skipped += 1
            continue

        title, url = link_data

        try:
            with transaction.atomic():
                VideoHyperlink.objects.get_or_create(
                    video_id=new_video_id,
                    url=url.strip(),
                    defaults={
                        "text": unescape(title) if title else "",
                        "time_start": 0,
                        "time_end": 0,
                    },
                )
                created += 1

        except Exception as e:
            errors += 1
            self.stdout.write(self.style.ERROR(f"Erreur lien video {old_video_id}: {e}"))

    self.stdout.write(
        self.style.SUCCESS(
            f"Terminé — {created} liens créés, "
            f"{skipped} ignorés, "
            f"{errors} erreurs"
        )
    )
