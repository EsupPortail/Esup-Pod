# type_studio.py

import threading
import logging
import datetime
import os
from xml.dom import minidom

from django.conf import settings
from ..utils import add_comment
from pod.video.models import Video, get_storage_path_video
from pod.video import encode
from django.template.defaultfilters import slugify

DEFAULT_RECORDER_TYPE_ID = getattr(settings, "DEFAULT_RECORDER_TYPE_ID", 1)

ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")

log = logging.getLogger(__name__)


def process(recording):
    log.info("START PROCESS OF RECORDING %s" % recording)
    t = threading.Thread(target=encode_recording, args=[recording])
    t.setDaemon(True)
    t.start()


def save_one_video(recording, video_src):
    # Save & encode a video corresponding to the recording
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
    nom, ext = os.path.splitext(os.path.basename(video_src))
    ext = ext.lower()
    video.video = os.path.join(
        os.path.dirname(storage_path), slugify(nom) + "_" + dt.replace(" ", "_") + ext
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

    encode_video = getattr(encode, ENCODE_VIDEO)
    encode_video(video.id)


def save_two_videos(recording, video_src_1, video_src_2):
    print("TODO in encode.py and task.py?")


def encode_recording(recording):
    recording.comment = ""
    recording.save()
    add_comment(recording.id, "Start at %s\n--\n" % datetime.datetime.now())

    try:
        # Read the Pod SMIL file
        file_smil = open(recording.source_file, "r")
        text_smil = file_smil.read()
        # XML result to parse
        xmldoc = minidom.parseString(text_smil)
    except KeyError as e:
        add_comment(recording.id, "Error : %s" % e)
        return -1

    # Get informations from SMIL file
    if xmldoc.getElementsByTagName("video")[0].firstChild:
        video_presenter_src = xmldoc.getElementsByTagName("video")[0].firstChild.data
    else:
        video_presenter_src = ""
    if xmldoc.getElementsByTagName("video")[1].firstChild:
        video_presentation_src = xmldoc.getElementsByTagName("video")[1].firstChild.data
    else:
        video_presentation_src = ""
    # clip_begin = xmldoc.getElementsByTagName("cut")[0].getAttribute("clipBegin")
    # clip_end = xmldoc.getElementsByTagName("cut")[0].getAttribute("clipEnd")

    # Management of the differents cases
    if video_presenter_src and video_presentation_src == "":
        # Save & encode presenter video
        video_src = os.path.join(
            settings.MEDIA_ROOT, 'opencast-files', video_presenter_src
        )
        add_comment(recording.id, "> video file (presenter) %s" % video_src)
        save_one_video(recording, video_src)
    elif video_presentation_src and video_presenter_src == "":
        # Save & encode presentation video
        video_src = os.path.join(
            settings.MEDIA_ROOT, 'opencast-files', video_presentation_src
        )
        add_comment(recording.id, "> video file (presentation) %s" % video_src)
        save_one_video(recording, video_src)
    elif video_presenter_src and video_presentation_src:
        # Save & encode the 2 videos in only one
        video_src_1 = os.path.join(
            settings.MEDIA_ROOT, 'opencast-files', video_presenter_src
        )
        video_src_2 = os.path.join(
            settings.MEDIA_ROOT, 'opencast-files', video_presentation_src
        )
        add_comment(recording.id, "> video files (presenter and presentation) %s %s" % video_src_1 % video_src_2)
        save_two_videos(recording, video_src_1, video_src_2)
    else:
        # No video found
        add_comment(recording.id, "Error : No video source found")
        return -1
    add_comment(recording.id, "End processing SMIL file")
    os.rename(recording.source_file, recording.source_file + "_treated")
