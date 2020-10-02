# video type process
import threading
import logging
import datetime
import os

from django.conf import settings
from pod.video.models import Video, Type, get_storage_path_video
from pod.video.encode import start_encode

USE_ADVANCED_RECORDER = getattr(settings, 'USE_ADVANCED_RECORDER', False)

DEFAULT_RECORDER_TYPE_ID = getattr(
    settings, 'DEFAULT_RECORDER_TYPE_ID',
    1
)
ENCODE_VIDEO = getattr(settings,
                       'ENCODE_VIDEO',
                       start_encode)

log = logging.getLogger(__name__)


def process(recording):
    log.info("START PROCESS OF RECORDING %s" % recording)
    t = threading.Thread(target=encode_recording,
                         args=[recording])
    t.setDaemon(True)
    t.start()


def encode_recording(recording):
    video = Video()
    video.title = recording.title
    video.owner = recording.user
    video.type = Type.objects.get(id=DEFAULT_RECORDER_TYPE_ID)
    # gestion de la video
    storage_path = get_storage_path_video(
        video, os.path.basename(recording.source_file))
    dt = str(datetime.datetime.now()).replace(":", "-")
    nom, ext = os.path.splitext(os.path.basename(recording.source_file))
    ext = ext.lower()
    video.video = os.path.join(
        os.path.dirname(storage_path), nom + "_" + dt.replace(" ", "_") + ext)
    # deplacement du fichier source vers destination
    os.makedirs(os.path.dirname(video.video.path), exist_ok=True)
    os.rename(recording.source_file, video.video.path)
    video.save()
    # on ajoute d'eventuels propriétaires additionnels
    if recording.recorder.additional_users.count() > 0:
        for usr in recording.recorder.additional_users.all():
            video.additional_owners.add(usr)
    # acces privé (mode brouillon)
    video.is_draft=recording.recorder.is_draft
    # Accès restreint (eventuellement à des groupe ou par mot de passe)
    video.is_restricted=recording.recorder.is_restricted
    if recording.recorder.restrict_access_to_groups.count() > 0:
        for g in recording.recorder.restrict_access_to_groups.all():
            video.restrict_access_to_groups.add(g)
    video.password = recording.recorder.password

    if USE_ADVANCED_RECORDER:
        TRANSCRIPT = getattr(settings, 'USE_TRANSCRIPTION', False)
        # on ajoute les eventuelles chaines
        if recording.recorder.channel.count() > 0:
            for c in recording.recorder.channel.all():
                video.channel.add(c)
        # on ajoute les eventuels theme
        if recording.recorder.theme.count() > 0:
            for t in recording.recorder.theme.all():
                video.theme.add(t)
        # on ajoute les eventuelles disciplines
        if recording.recorder.discipline.count() > 0:
            for d in recording.recorder.discipline.all():
                video.discipline.add(d)
        # Choix de la langue
        if recording.recorder.main_lang:
            video.main_lang = recording.recorder.main_lang
        # Choix des cursus
        video.cursus = recording.recorder.cursus
        # mot clefs
        video.tags = recording.recorder.tags
        # transcript
        if TRANSCRIPT:
            video.transcript = recording.recorder.transcript
        # Licence
        video.licence = recording.recorder.licence
        # Allow allow_downloading
        video.allow_downloading = recording.recorder.allow_downloading
        # Is_360
        video.is_360 = recording.recorder.is_360
        # Désactiver les commentaires
        video.disable_comment = recording.recorder.disable_comment
    video.save()
    ENCODE_VIDEO(video.id)
