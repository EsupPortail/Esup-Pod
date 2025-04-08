# type_audiovideocast.py

import threading
import logging
import datetime
import zipfile
import os
from defusedxml import minidom

from django.conf import settings
from django.template.defaultfilters import slugify
from django.core.files.base import ContentFile
from pod.video.models import Video
from pod.video_encode_transcript import encode
from pod.enrichment.models import Enrichment
from ..utils import add_comment

DEFAULT_RECORDER_TYPE_ID = getattr(settings, "DEFAULT_RECORDER_TYPE_ID", 1)

ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")

RECORDER_SKIP_FIRST_IMAGE = getattr(settings, "RECORDER_SKIP_FIRST_IMAGE", False)

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder

    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel

log = logging.getLogger(__name__)


def process(recording) -> None:
    log.info("START PROCESS OF RECORDING %s" % recording)
    t = threading.Thread(target=encode_recording, args=[recording])
    t.daemon = True
    t.start()


def save_video(recording, video_data, video_src) -> Video:
    recorder = recording.recorder
    video = Video()
    video.owner = recording.user
    video.type = recorder.type
    nom, ext = os.path.splitext(video_src)
    ext = ext.lower()
    video.video.save(
        "record_" + slugify(recording.title) + ext,
        ContentFile(video_data),
        save=False,
    )
    # on recupere le nom du fichier sur le serveur
    video.title = recording.title
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
    return video


def save_slide(data, filename, video, enrichment, recording) -> None:
    if len(data):
        slide_name, ext = os.path.splitext(os.path.basename(filename))
        if FILEPICKER:
            homedir, created = UserFolder.objects.get_or_create(
                name="home", owner=video.owner
            )
            video_folder = video.get_or_create_video_folder()
            previousImage = CustomImageModel.objects.filter(
                name__startswith=slugify(video.title + "_" + slide_name),
                folder=video_folder,
                created_by=video.owner,
            )
            for img in previousImage:
                img.delete()
            image = CustomImageModel(folder=video_folder, created_by=video.owner)
            image.file.save(
                slugify(video.title + "_" + slide_name) + ext,
                ContentFile(data),
                save=True,
            )
            image.save()
        else:
            image = CustomImageModel()
            image.file.save(
                slugify(video.title + "_" + slide_name) + ext,
                ContentFile(data),
                save=True,
            )
            image.save()
        enrichment.type = "image"
        enrichment.image = image
        enrichment.save()
    else:
        add_comment(recording.id, "file %s is empty" % filename)


def save_enrichment(video, list_node_img, recording, media_name, zip) -> None:
    previousEnrichment = None
    i = 0
    Enrichment.objects.filter(video=video).delete()
    start_img = 1 if RECORDER_SKIP_FIRST_IMAGE else 0
    for item in list_node_img[start_img:]:  # skip the first
        i += 1
        add_comment(recording.id, ">> ITEM %s: %s" % (i, item.getAttribute("src")))
        filename = media_name + "/%s" % item.getAttribute("src")
        timecode = float("%s" % item.getAttribute("begin"))
        timecode = int(round(timecode))
        add_comment(recording.id, ">> timecode %s" % timecode)
        # Enrichment
        enrichment = Enrichment.objects.create(
            video=video,
            title="slide %s" % i,
            start=timecode,
            end=timecode + 1,
            stop_video=False,
        )
        # Enrichment Image
        data = zip.read(filename)
        save_slide(data, filename, video, enrichment, recording)
        if previousEnrichment is not None:
            previousEnrichment.end = (
                timecode - 1 if (timecode - 1 > 0) else previousEnrichment.end
            )
            previousEnrichment.save()
        previousEnrichment = enrichment

    video = Video.objects.get(id=video.id)
    if previousEnrichment is not None and video.duration and video.duration > 0:
        previousEnrichment.end = video.duration
        previousEnrichment.save()


def get_video_source(xmldoc):
    if xmldoc.getElementsByTagName("audio"):
        return xmldoc.getElementsByTagName("audio").item(0).getAttribute("src")
    if xmldoc.getElementsByTagName("video"):
        return xmldoc.getElementsByTagName("video").item(0).getAttribute("src")
    return None


def open_zipfile(recording):
    try:
        zip = zipfile.ZipFile(recording.source_file)
        return zip
    except FileNotFoundError as e:
        add_comment(recording.id, "Error: %s" % e)
        return -1
    except zipfile.BadZipFile as e:
        add_comment(recording.id, "Error: %s" % e)
        return -1


def encode_recording(recording):
    recording.comment = ""
    recording.save()
    add_comment(recording.id, "Start at %s\n--\n" % datetime.datetime.now())
    zip = open_zipfile(recording)
    if zip == -1:
        return -1

    media_name, ext = os.path.splitext(os.path.basename(recording.source_file))
    add_comment(recording.id, "> media name %s" % media_name)
    try:
        smil = zip.open(media_name + "/cours.smil")
        xmldoc = minidom.parse(smil)
        smil.close()
    except KeyError as e:
        add_comment(recording.id, "Error: %s" % e)
        zip.close()
        return -1

    video_src = get_video_source(xmldoc)

    if video_src:
        add_comment(recording.id, "> video file %s" % video_src)
        video_data = zip.read(media_name + "/%s" % video_src)
        video = save_video(recording, video_data, video_src)
        list_node_img = xmldoc.getElementsByTagName("img")
        add_comment(recording.id, "> slides found %s" % len(list_node_img))
        if len(list_node_img):
            save_enrichment(video, list_node_img, recording, media_name, zip)
        else:
            add_comment(recording.id, "No slides node found")
            zip.close()
            return -1
    else:
        add_comment(recording.id, "Error: No video source found")
        zip.close()
        return -1
    zip.close()
    add_comment(recording.id, "End processing zip file")
    os.rename(recording.source_file, recording.source_file + "_treated")
