"""Esup-Pod -
Migration des documents webtv -> Pod (métadonnées uniquement, pas de copie
physique des fichiers).

Un document peut être attaché à plusieurs vidéos, mais completion.Document
exige exactement une vidéo par ligne : chaque couple (vidéo, document) devient
son propre Document (les documents partagés sont dupliqués, pas perdus).
"""

from html import unescape

from django.db import connections, transaction

from src.apps.completion.models import Document
from src.apps.migration.models import DocumentMapping, VideoMapping


def _fetch_documents(cursor):
    """Migration helper."""
    cursor.execute("SELECT id, title, storedfilename FROM Ze4fg_documents")
    cols = [c[0] for c in cursor.description]
    return {row[0]: dict(zip(cols, row)) for row in cursor.fetchall()}


def _fetch_video_documents(cursor):
    """Migration helper."""
    cursor.execute("SELECT id, video_id, document_id FROM Ze4fg_video_documents")
    return cursor.fetchall()


def _migrate_documents(self, video_documents, documents_by_id, video_mapping):
    """Migration helper."""
    created = skipped = errors = 0

    for old_id, old_video_id, old_document_id in video_documents:

        if DocumentMapping.objects.filter(old_id=old_id).exists():
            skipped += 1
            continue

        new_video_id = video_mapping.get(old_video_id)
        doc_data = documents_by_id.get(old_document_id)

        if not new_video_id or not doc_data:
            self.stdout.write(
                self.style.WARNING(
                    f"Skip video_document {old_id}: video {old_video_id} ou "
                    f"document {old_document_id} introuvable"
                )
            )
            skipped += 1
            continue

        try:
            with transaction.atomic():
                document = Document.objects.create(
                    video_id=new_video_id,
                    title=unescape(doc_data["title"] or "Sans titre").strip()[:250],
                    file=(doc_data["storedfilename"] or "")[:100],
                    is_private=False,
                )
                DocumentMapping.objects.create(old_id=old_id, new_id=document.id)
                created += 1
                self.stdout.write(f"Document créé: [{old_id}] {document.title[:50]}")

        except Exception as e:
            errors += 1
            self.stdout.write(self.style.ERROR(f"Erreur Document {old_id}: {e}"))

    return created, skipped, errors


def documentMigrate(self, *args, **kwargs):
    """Migration helper."""
    video_mapping = {m.old_id: m.new_id for m in VideoMapping.objects.all()}
    self.stdout.write(f"Videos mappées: {len(video_mapping)}")

    with connections["webtv"].cursor() as cursor:
        documents_by_id = _fetch_documents(cursor)
        video_documents = _fetch_video_documents(cursor)

    self.stdout.write(
        f"{len(documents_by_id)} documents, {len(video_documents)} liaisons vidéo trouvées"
    )

    created, skipped, errors = _migrate_documents(
        self, video_documents, documents_by_id, video_mapping
    )

    self.stdout.write(
        self.style.SUCCESS(
            f"Terminé — {created} documents créés, {skipped} ignorés, {errors} erreurs"
        )
    )
