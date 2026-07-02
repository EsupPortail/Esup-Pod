from django.db import connections, transaction
from html import unescape
from src.apps.video.models.Speaker import Speaker, Job, JobVideo #A CHANGER 
from src.apps.migration.models import VideoMapping, SpeakerMapping


def speakerMigrate(self, *args, **kwargs):
    limit = kwargs.get("limit", 0)

    video_mapping = {m.old_id: m.new_id for m in VideoMapping.objects.all()}
    self.stdout.write(f"Vidéos mappées: {len(video_mapping)}")

    # Migration des speakers
    with connections["webtv"].cursor() as cursor:
        query = "SELECT id, firstname, lastname FROM Ze4fg_speaker"
        if limit > 0:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        speakers = cursor.fetchall()

    self.stdout.write(f"{len(speakers)} speakers à migrer")

    #Mapping
    speaker_mapping = {}
    created_speakers = 0
    error_count = 0

    for old_id, firstname, lastname in speakers:
        try:
            with transaction.atomic():
                speaker = Speaker.objects.create(
                    firstname=firstname or "",
                    lastname=lastname or "",
                )
                speaker_mapping[old_id] = speaker.id
                SpeakerMapping.objects.create(
                    old_id=old_id,
                    new_id=speaker.id,
                )
                created_speakers += 1
        except Exception as e:
            error_count += 1
            self.stdout.write(self.style.ERROR(f"Erreur speaker {old_id}: {e}"))

    # Migration des speakers jobs
    with connections["webtv"].cursor() as cursor:
        cursor.execute("SELECT id, description, speaker_id FROM Ze4fg_speakerfunction")
        functions = cursor.fetchall()

    # Mapping old_function_id → new_job_id
    job_mapping = {}
    created_jobs = 0

    for old_id, description, old_speaker_id in functions:
        new_speaker_id = speaker_mapping.get(old_speaker_id)
        if not new_speaker_id:
            continue
        try:
            with transaction.atomic():
                job = Job.objects.create(
                    title=unescape(description or ""),
                    speaker_id=new_speaker_id,
                )
                job_mapping[old_id] = job.id
                created_jobs += 1
        except Exception as e:
            error_count += 1
            self.stdout.write(self.style.ERROR(f"Erreur job {old_id}: {e}"))

    # Lien des speakers avec les vidéos grace a JobVideo
    with connections["webtv"].cursor() as cursor:
        cursor.execute("SELECT video_id, speakerfunction_id FROM Ze4fg_video_speaker")
        video_speakers = cursor.fetchall()

    created_jobvideos = 0
    skipped_count = 0

    for old_video_id, old_function_id in video_speakers:
        new_video_id = video_mapping.get(old_video_id)
        new_job_id = job_mapping.get(old_function_id)

        if not new_video_id or not new_job_id:
            skipped_count += 1
            continue
        try:
            JobVideo.objects.get_or_create(
                job_id=new_job_id,
                video_id=new_video_id,
            )
            created_jobvideos += 1
        except Exception as e:
            error_count += 1
            self.stdout.write(self.style.ERROR(f"Erreur JobVideo {old_video_id}: {e}"))

    self.stdout.write(
        self.style.SUCCESS(
            f"Terminé — {created_speakers} speakers, "
            f"{created_jobs} jobs, "
            f"{created_jobvideos} liaisons, "
            f"{skipped_count} skippés, "
            f"{error_count} erreurs"
        )
    )