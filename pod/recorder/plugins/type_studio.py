# type_studio.py

import threading
import logging
import datetime
import os
from xml.dom import minidom

from django.conf import settings

from ..utils import add_comment, studio_clean_old_files
from ..models import Recording
from pod.video.models import Video, get_storage_path_video
from pod.video import encode
from django.template.defaultfilters import slugify

DEFAULT_RECORDER_TYPE_ID = getattr(settings, "DEFAULT_RECORDER_TYPE_ID", 1)
ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")
ENCODE_STUDIO = getattr(settings, "ENCODE_STUDIO", "start_encode_studio")
MEDIA_URL = getattr(settings, "MEDIA_URL", "/media/")
OPENCAST_FILES_DIR = getattr(settings, "OPENCAST_FILES_DIR", "opencast-files")
# Possible value are "mid", "piph" or "pipb"
OPENCAST_DEFAULT_PRESENTER = getattr(settings, "OPENCAST_DEFAULT_PRESENTER", "mid")

log = logging.getLogger(__name__)


def process(recording):
    log.info("START PROCESS OF RECORDING %s" % recording)
    t = threading.Thread(target=encode_recording, args=[recording])
    t.setDaemon(True)
    t.start()


def save_basic_video(recording, video_src):
    # Save & encode one video corresponding to the recording without cut
    # We don't generate an intermediate video
    recorder = recording.recorder
    video = Video()
    # Video title corresponds to recording title
    video.title = recording.title
    video.owner = recording.user
    # Video type
    video.type = recorder.type
    # Video management
    storage_path = get_storage_path_video(video, os.path.basename(video_src))
    dt = str(datetime.datetime.now()).replace(":", "-")
    name, ext = os.path.splitext(os.path.basename(video_src))
    ext = ext.lower()
    video.video = os.path.join(
        os.path.dirname(storage_path), slugify(name) + "_" + dt.replace(" ", "_") + ext
    )
    # Move source file to destination
    os.makedirs(os.path.dirname(video.video.path), exist_ok=True)
    os.rename(video_src, video.video.path)
    video.save()

    # Add any additional owners
    video.additional_owners.add(*recorder.additional_users.all())
    # Private access (draft mode)
    video.is_draft = recorder.is_draft
    # Restricted access (possibly to groups or by password)
    video.is_restricted = recorder.is_restricted
    video.restrict_access_to_groups.add(*recorder.restrict_access_to_groups.all())
    video.password = recorder.password
    # Add the possible channels
    video.channel.add(*recorder.channel.all())
    # Add the possible themes
    video.theme.add(*recorder.theme.all())
    # Add any disciplines
    video.discipline.add(*recorder.discipline.all())
    # Language choice
    video.main_lang = recorder.main_lang
    # Cursus
    video.cursus = recorder.cursus
    # Tags
    video.tags = recorder.tags
    # Transcription
    if getattr(settings, "USE_TRANSCRIPTION", False):
        video.transcript = recorder.transcript
    # Licence
    video.licence = recorder.licence
    # Allow downloading
    video.allow_downloading = recorder.allow_downloading
    # Is 360
    video.is_360 = recorder.is_360
    # Disable comments
    video.disable_comment = recorder.disable_comment
    # Add sites
    video.sites.add(*recorder.sites.all())
    # Finally save
    video.save()

    # Rename the XML file
    # os.rename(recording.source_file, recording.source_file + "_treated")

    studio_clean_old_files()

    return video


def generate_intermediate_video(recording, videos, clip_begin, clip_end, presenter):
    # Video file output : at the same directory than the XML file
    # And with the same name .mp4
    video_output = recording.source_file.replace(".xml", ".mp4")
    subtime = get_subtime(clip_begin, clip_end)
    encode_studio = getattr(encode, ENCODE_STUDIO)
    encode_studio(recording.id, video_output, videos, subtime, presenter)


def get_subtime(clip_begin, clip_end):
    subtime = ""
    if clip_begin:
        subtime += "-ss %s " % str(clip_begin)
    if clip_end:
        subtime += "-to %s " % str(clip_end)
    return subtime


def encode_recording_id(recording_id):
    recording = Recording.objects.get(id=recording_id)
    encode_recording(recording)


# flake ignore complexity with noqa: C901
def encode_recording(recording):
    recording.comment = ""
    recording.save()
    add_comment(recording.id, "Start at %s\n--\n" % datetime.datetime.now())

    try:
        xmldoc = minidom.parse(recording.source_file)
    except KeyError as e:
        add_comment(recording.id, "Error : %s" % e)
        return -1
    videos = getElementsByName(xmldoc, "track")
    catalogs = getElementsByName(xmldoc, "catalog")
    title = ""
    clip_begin = None
    clip_end = None
    att_presenter = getAttributeByName(xmldoc, "mediapackage", "presenter")
    presenter = (
        att_presenter
        if (att_presenter in ["mid", "piph", "pipb"])
        else OPENCAST_DEFAULT_PRESENTER
    )
    for catalog in catalogs:
        xmldoc = minidom.parse(catalog.get("src"))
        if catalog.get("type") == "dublincore/episode":
            title = getElementValueByName(xmldoc, "dcterms:title")
            change_title(recording, title)
        if catalog.get("type") == "smil/cutting":
            beginDefault = getAttributeByName(xmldoc, "video", "clipBegin")
            endDefault = getAttributeByName(xmldoc, "video", "clipEnd")
            clip_begin = (
                str(round(float(beginDefault.replace("s", "")), 2))
                if (beginDefault)
                else None
            )
            clip_end = (
                str(round(float(endDefault.replace("s", "")), 2))
                if (endDefault)
                else None
            )
    if clip_begin or clip_end or len(videos) > 1:
        msg = "*** generate_intermediate_video (%s) %s ***" % (
            videos[0].get("type"),
            videos[0].get("src"),
        )
        add_comment(recording.id, msg)
        generate_intermediate_video(recording, videos, clip_begin, clip_end, presenter)
    else:
        msg = "*** Management of basic video file (%s) %s ***" % (
            videos[0].get("type"),
            videos[0].get("src"),
        )
        add_comment(recording.id, msg)
        video = save_basic_video(
            recording,
            os.path.join(settings.MEDIA_ROOT, OPENCAST_FILES_DIR, videos[0].get("src")),
        )
        # encode video
        encode_video = getattr(encode, ENCODE_VIDEO)
        encode_video(video.id)


def change_title(recording, title):
    if title != "":
        recording.title = title
        recording.save()


def getAttributeByName(xmldoc, tagName, attribute):
    elements = xmldoc.getElementsByTagName(tagName)
    if elements and len(elements) > 0:
        attr = elements[0].getAttribute(attribute)
        if attr and "e" not in attr:
            return attr
    return None


def getElementsByName(xmldoc, name):
    elements = []
    for element in xmldoc.getElementsByTagName(name):
        urlElement = element.getElementsByTagName("url")[0]
        if urlElement.firstChild and urlElement.firstChild.data != "":
            element_path = urlElement.firstChild.data[
                urlElement.firstChild.data.index(MEDIA_URL) + len(MEDIA_URL) :
            ]
            src = os.path.join(settings.MEDIA_ROOT, element_path)
            if os.path.isfile(src):
                elements.append(
                    {
                        "type": element.getAttribute("type"),
                        "src": src,
                    }
                )
    return elements


def getElementValueByName(xmldoc, name):
    element = xmldoc.getElementsByTagName(name)[0]
    if element.firstChild and element.firstChild.data != "":
        return element.firstChild.data
    return ""
