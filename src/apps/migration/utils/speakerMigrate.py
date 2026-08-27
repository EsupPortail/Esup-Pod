"""Esup-Pod -
Migration des intervenants webtv -> Pod (Speakers -> Contributors).

Ze4fg_speaker devient un Contributor, Ze4fg_speakerfunction fournit son
job_title (tronqué à 200 caractères : ~4% des descriptions webtv dépassent
la limite du modèle), et Ze4fg_video_speaker crée les Contribution
(role="speaker") reliant Contributor et Video.
"""

from django.db import connections, transaction
from html import unescape

from src.apps.completion.models import Contributor, Contribution
from src.apps.migration.models import VideoMapping, CompletionMapping


def _migrate_contributors(self, speakers, contributor_mapping):
    """Migration helper."""
    created = 0
    errors = 0

    for old_id, firstname, lastname in speakers:

        # skip si déjà migré
        if old_id in contributor_mapping:
            continue

        try:
            with transaction.atomic():
                contributor = Contributor.objects.create(
                    first_name=(firstname or "")[:200],
                    last_name=(lastname or "")[:200],
                )

                CompletionMapping.objects.create(
                    old_id=old_id,
                    new_id=contributor.id,
                )

                contributor_mapping[old_id] = contributor.id
                created += 1

        except Exception as e:
            errors += 1
            self.stdout.write(self.style.ERROR(f"Erreur speaker {old_id}: {e}"))

    return created, errors


def _build_function_mapping(functions, contributor_mapping):
    """Migration helper."""
    function_mapping = {}

    for old_id, description, old_speaker_id in functions:
        contributor_id = contributor_mapping.get(old_speaker_id)

        if not contributor_id:
            continue

        function_mapping[old_id] = {
            "contributor_id": contributor_id,
            "job_title": unescape(description or "")[:200],
        }

    return function_mapping


def _migrate_contributions(self, links, function_mapping, video_mapping):
    """Migration helper."""
    created = skipped = errors = 0

    for old_video_id, old_function_id in links:

        new_video_id = video_mapping.get(old_video_id)
        data = function_mapping.get(old_function_id)

        if not new_video_id or not data:
            skipped += 1
            continue

        try:
            with transaction.atomic():
                _, created_flag = Contribution.objects.get_or_create(
                    video_id=new_video_id,
                    contributor_id=data["contributor_id"],
                    role="speaker",
                    defaults={
                        "job_title": data["job_title"],
                    },
                )

                if created_flag:
                    created += 1

        except Exception as e:
            errors += 1
            self.stdout.write(
                self.style.ERROR(
                    f"Erreur Contribution video={old_video_id} function={old_function_id}: {e}"
                )
            )

    return created, skipped, errors


def speakerMigrate(self, *args, **kwargs):
    """Migration helper."""
    limit = kwargs.get("limit", 0)

    video_mapping = {m.old_id: m.new_id for m in VideoMapping.objects.all()}
    contributor_mapping = {m.old_id: m.new_id for m in CompletionMapping.objects.all()}

    self.stdout.write(f"Videos mappées: {len(video_mapping)}")
    self.stdout.write(f"Contributors déjà mappés: {len(contributor_mapping)}")

    # -------------------------
    # 1. SPEAKERS -> CONTRIBUTORS
    # -------------------------
    with connections["webtv"].cursor() as cursor:
        query = "SELECT id, firstname, lastname FROM Ze4fg_speaker"
        if limit > 0:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        speakers = cursor.fetchall()

    created_contributors, contributor_errors = _migrate_contributors(
        self, speakers, contributor_mapping
    )
    self.stdout.write(f"{created_contributors} contributors créés")

    # -------------------------
    # 2. SPEAKERFUNCTION -> META INFOS
    # -------------------------
    with connections["webtv"].cursor() as cursor:
        cursor.execute("SELECT id, description, speaker_id FROM Ze4fg_speakerfunction")
        functions = cursor.fetchall()

    function_mapping = _build_function_mapping(functions, contributor_mapping)

    # -------------------------
    # 3. VIDEO SPEAKER -> CONTRIBUTION
    # -------------------------
    with connections["webtv"].cursor() as cursor:
        cursor.execute("SELECT video_id, speakerfunction_id FROM Ze4fg_video_speaker")
        links = cursor.fetchall()

    created, skipped, contribution_errors = _migrate_contributions(
        self, links, function_mapping, video_mapping
    )

    self.stdout.write(
        self.style.SUCCESS(
            f"Terminé — {created_contributors} contributors, "
            f"{created} contributions créées, "
            f"{skipped} ignorées, "
            f"{contributor_errors + contribution_errors} erreurs"
        )
    )
