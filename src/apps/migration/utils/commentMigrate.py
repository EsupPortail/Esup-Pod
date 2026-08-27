"""Esup-Pod -
Migration des commentaires webtv -> Pod.

- `direct_parent` est le commentaire auquel on répond directement ;
  `parent` doit toujours être la racine du fil (pas juste le parent direct).
  Pour une réponse de niveau 3+, on remonte via le `parent` déjà résolu du
  parent direct plutôt que de recalculer toute la chaîne.
- `Comment.added` utilise auto_now_add (ignoré par create()) : la date
  d'origine webtv est réappliquée juste après via un update().
"""

from django.db import connections, transaction
from django.utils import timezone

from src.apps.video.models.Comment import Comment
from src.apps.migration.models import UserMapping, VideoMapping, CommentMapping


def _parse_added_date(date_added):
    """Migration helper."""
    if not date_added:
        return timezone.now()
    try:
        return timezone.make_aware(date_added)
    except Exception:
        return timezone.now()


def _resolve_parents(self, old_comment_id, old_parent_id, comment_mapping):
    """Résout (parent_id, direct_parent_id) pour un commentaire en cours de migration."""
    if not old_parent_id:
        return None, None

    direct_parent_new_id = comment_mapping.get(old_parent_id)
    if not direct_parent_new_id:
        existing = CommentMapping.objects.filter(old_id=old_parent_id).first()
        direct_parent_new_id = existing.new_id if existing else None

    if not direct_parent_new_id:
        self.stdout.write(
            self.style.WARNING(
                f"Commentaire {old_comment_id}: parent {old_parent_id} "
                f"introuvable, créé sans parent"
            )
        )
        return None, None

    direct_parent = (
        Comment.objects.filter(id=direct_parent_new_id).values("parent_id").first()
    )
    root_new_id = (
        direct_parent["parent_id"] if direct_parent else None
    ) or direct_parent_new_id
    return root_new_id, direct_parent_new_id


def _migrate_comment_row(self, data, user_mapping, video_mapping, comment_mapping):
    """Migration helper."""
    old_comment_id = data["comment_id"]

    if CommentMapping.objects.filter(old_id=old_comment_id).exists():
        return "skipped"

    new_user_id = user_mapping.get(data["userid"])
    if not new_user_id:
        self.stdout.write(
            self.style.WARNING(
                f"Skip commentaire {old_comment_id}: user {data['userid']} introuvable"
            )
        )
        return "skipped"

    new_video_id = video_mapping.get(data["type_id"])
    if not new_video_id:
        self.stdout.write(
            self.style.WARNING(
                f"Skip commentaire {old_comment_id}: vidéo {data['type_id']} introuvable"
            )
        )
        return "skipped"

    # parent_id=0 --> pas de parent dans l'ancienne BDD
    old_parent_id = data["parent_id"] or None
    new_parent_id, new_direct_parent_id = _resolve_parents(
        self, old_comment_id, old_parent_id, comment_mapping
    )

    added = _parse_added_date(data["date_added"])

    comment = Comment.objects.create(
        content=data["comment"] or "",
        author_id=new_user_id,
        video_id=new_video_id,
        parent_id=new_parent_id,
        direct_parent_id=new_direct_parent_id,
    )
    Comment.objects.filter(pk=comment.pk).update(added=added)

    comment_mapping[old_comment_id] = comment.id
    CommentMapping.objects.create(old_id=old_comment_id, new_id=comment.id)
    return "created"


def commentMigrate(self, *args, **kwargs):
    """Migration helper."""
    limit = kwargs.get("limit", 0)

    user_mapping = {m.old_id: m.new_id for m in UserMapping.objects.all()}
    video_mapping = {m.old_id: m.new_id for m in VideoMapping.objects.all()}
    self.stdout.write(
        f"Users mappés: {len(user_mapping)}, Vidéos mappées: {len(video_mapping)}"
    )

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

    created_count = skipped_count = error_count = 0
    comment_mapping = {}

    for row in rows:
        data = dict(zip(columns, row))
        old_comment_id = data["comment_id"]

        try:
            with transaction.atomic():
                result = _migrate_comment_row(
                    self, data, user_mapping, video_mapping, comment_mapping
                )
                if result == "created":
                    created_count += 1
                else:
                    skipped_count += 1

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
