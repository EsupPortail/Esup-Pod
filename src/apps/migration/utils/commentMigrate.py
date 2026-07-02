from django.db import connections, transaction
from django.utils import timezone
from src.apps.video.models.Comment import Comment
from src.apps.migration.models import UserMapping, VideoMapping, CommentMapping


def commentMigrate(self, *args, **kwargs):
    limit = kwargs.get("limit", 0)

    user_mapping = {m.old_id: m.new_id for m in UserMapping.objects.all()}
    video_mapping = {m.old_id: m.new_id for m in VideoMapping.objects.all()}
    self.stdout.write(f"Users mappés: {len(user_mapping)}, Vidéos mappées: {len(video_mapping)}")

    with connections["webtv"].cursor() as cursor:
        query = """
            SELECT comment_id, comment, userid, parent_id, type_id, date_added
            FROM Ze4fg_comments
            WHERE type = 'vid'
            ORDER BY comment_id ASC
        """
        if limit > 0:
            query += f" LIMIT {limit}"

        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()

    self.stdout.write(f"{len(rows)} commentaires à migrer")

    created_count = 0
    skipped_count = 0
    error_count = 0

    # Mapping comment_id
    comment_mapping = {}

    for row in rows:
        data = dict(zip(columns, row))
        old_comment_id = data["comment_id"]
        old_user_id = data["userid"]
        old_video_id = data["type_id"]
        old_parent_id = data["parent_id"]

        try:
            with transaction.atomic():
                new_user_id = user_mapping.get(old_user_id)
                if not new_user_id:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skip commentaire {old_comment_id}: "
                            f"user {old_user_id} introuvable"
                        )
                    )
                    skipped_count += 1
                    continue

                new_video_id = video_mapping.get(old_video_id)
                if not new_video_id:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skip commentaire {old_comment_id}: "
                            f"vidéo {old_video_id} introuvable"
                        )
                    )
                    skipped_count += 1
                    continue

                # parent_id=0 --> pas de parent dans l'ancienne BDD
                new_parent_id = None
                new_direct_parent_id = None
                if old_parent_id and old_parent_id != 0:
                    new_parent_id = comment_mapping.get(old_parent_id)
                    new_direct_parent_id = new_parent_id
                    if not new_parent_id:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Commentaire {old_comment_id}: "
                                f"parent {old_parent_id} introuvable, créé sans parent"
                            )
                        )

                # Gestion de la date
                if data["date_added"]:
                    try:
                        added = timezone.make_aware(data["date_added"])
                    except Exception:
                        added = timezone.now()
                else:
                    added = timezone.now()

                comment = Comment.objects.create(
                    content=data["comment"] or "",
                    author_id=new_user_id,
                    video_id=new_video_id,
                    parent_id=new_parent_id,
                    direct_parent_id=new_direct_parent_id,
                )

                # Sauvegarde du mapping en mémoire et en base
                comment_mapping[old_comment_id] = comment.id
                CommentMapping.objects.create(
                    old_id=old_comment_id,
                    new_id=comment.id,
                )

                created_count += 1

        except Exception as e:
            error_count += 1
            self.stdout.write(
                self.style.ERROR(f"Erreur commentaire {old_comment_id}: {e}")
            )

    self.stdout.write(
        self.style.SUCCESS(
            f"Terminé — {created_count} créés, "
            f"{skipped_count} skippés, "
            f"{error_count} erreurs"
        )
    )