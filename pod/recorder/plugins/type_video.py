# video type process
import threading
import logging
import datetime
import os
import shutil

from django.conf import settings
from pod.video.models import Video, get_storage_path_video
from pod.video_encode_transcript import encode

DEFAULT_RECORDER_TYPE_ID = getattr(settings, "DEFAULT_RECORDER_TYPE_ID", 1)
ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")
log = logging.getLogger(__name__)


def process(recording):
    log.info("START PROCESS OF RECORDING %s" % recording)
    t = threading.Thread(target=encode_recording, args=[recording])
    t.daemon = True
    t.start()


def encode_recording(recording) -> None:
    recorder = recording.recorder
    video = Video()
    video.title = recording.title
    video.owner = recording.user
    video.type = recorder.type
    # gestion de la video
    storage_path = get_storage_path_video(video, os.path.basename(recording.source_file))
    dt = str(datetime.datetime.now()).replace(":", "-")
    nom, ext = os.path.splitext(os.path.basename(recording.source_file))
    ext = ext.lower()
    video.video = os.path.join(
        os.path.dirname(storage_path), nom + "_" + dt.replace(" ", "_") + ext
    )
    # deplacement du fichier source vers destination
    os.makedirs(os.path.dirname(video.video.path), exist_ok=True)
    shutil.move(recording.source_file, video.video.path)
    video.save()
    # on ajoute d'eventuels propriétaires additionnels
    video.additional_owners.add(*recorder.additional_users.all())
    # acces privé (mode brouillon)
    video.is_draft = recorder.is_draft
    # Accès restreint (eventuellement à des groupes ou par mot de passe)
    video.is_restricted = recorder.is_restricted
    video.restrict_access_to_groups.add(*recorder.restrict_access_to_groups.all())
    video.password = recorder.password
    # on ajoute les eventuelles chaines
    video.channel.add(*recorder.channel.all())
    # on ajoute les eventuels theme
    video.theme.add(*recorder.theme.all())
    # on ajoute les eventuelles disciplines
    video.discipline.add(*recorder.discipline.all())
    # Choix de la langue
    video.main_lang = recorder.main_lang
    # Choix des cursus
    video.cursus = recorder.cursus
    # mot clefs
    video.tags = recorder.tags.get_tag_list()
    # transcript
    if getattr(settings, "USE_TRANSCRIPTION", False):
        video.transcript = recorder.transcript
    # Licence
    video.licence = recorder.licence
    # Allow downloading
    video.allow_downloading = recorder.allow_downloading
    # Is_360
    video.is_360 = recorder.is_360
    # Désactiver les commentaires
    video.disable_comment = recorder.disable_comment
    # add sites
    video.sites.add(*recorder.sites.all())
    video.save()

    encode_video = getattr(encode, ENCODE_VIDEO)
    encode_video(video.id)
