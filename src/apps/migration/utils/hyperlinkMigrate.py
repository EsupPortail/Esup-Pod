from django.db import connections, transaction
from src.apps.video.models import VideoHyperlink
from src.apps.migration.models import VideoMapping


def hyperlinkMigrate(self, *args, **kwargs):
    video_mapping = {m.old_id: m.new_id for m in VideoMapping.objects.all()}
    self.stdout.write(f"Vidéos mappées: {len(video_mapping)}")

    with connections["webtv"].cursor() as cursor:
        cursor.execute("SELECT video_id, link_id FROM Ze4fg_video_links")
        video_links = cursor.fetchall()

    link_ids = {link_id for _, link_id in video_links}

    with connections["webtv"].cursor() as cursor:
        placeholders = ",".join(["%s"] * len(link_ids))
        cursor.execute(
            f"SELECT id, title, url FROM Ze4fg_links WHERE id IN ({placeholders})",
            list(link_ids),
        )
        links = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

    created_count = 0
    skipped_count = 0
    error_count = 0

    for old_video_id, old_link_id in video_links:
        new_video_id = video_mapping.get(old_video_id)
        link_data = links.get(old_link_id)

        if not new_video_id or not link_data:
            skipped_count += 1
            continue

        title, url = link_data

        try:
            with transaction.atomic():
                VideoHyperlink.objects.create(
                    video_id=new_video_id,
                    url=url,
                    text=title or "",
                    time_start=0,
                    time_end=0,
                )
                created_count += 1
        except Exception as e:
            error_count += 1
            self.stdout.write(self.style.ERROR(f"Erreur liaison {old_video_id}: {e}"))

    self.stdout.write(
        self.style.SUCCESS(
            f"Terminé — {created_count} liens créés, "
            f"{skipped_count} skippés, "
            f"{error_count} erreurs"
        )
    )