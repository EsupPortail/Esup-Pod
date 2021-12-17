import os
import subprocess
import time
import threading
import logging
from xml.dom import minidom

from django.conf import settings
from pod.main.tasks import task_start_studio_encode
from pod.recorder.models import Recording
from pod.recorder.utils import add_comment

# Use of OpenCast Studio
USE_OPENCAST_STUDIO = getattr(settings, "USE_OPENCAST_STUDIO", False)
# Tools
FFMPEG = getattr(settings, "FFMPEG", "ffmpeg")
FFPROBE = getattr(settings, "FFPROBE", "ffprobe")
# Debug mode
DEBUG = getattr(settings, "DEBUG", False)
# Use of Celery to encode
CELERY_TO_ENCODE = getattr(settings, "CELERY_TO_ENCODE", False)

# Logger (not Log4j :) )
log = logging.getLogger(__name__)


def start_studio_encode(id):
    if CELERY_TO_ENCODE:
        task_start_studio_encode.delay(id)
    else:
        log.info("START STUDIO ENCODE VIDEOS FROM RECORDING %s" % (id))
        t = threading.Thread(
            target=studio_encode_videos, args=[id]
        )
        t.setDaemon(False)
        t.start()


def studio_encode_videos(id):
    # noqa: max-complexity=12
    # Merge two videos, and sound, in only one
    # Cut the result video if necessary

    msg = ""

    # Get the recording
    recording = Recording.objects.get(id=id)

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
    # Video 1
    if xmldoc.getElementsByTagName("video")[0].firstChild:
        video_presenter_src = xmldoc.getElementsByTagName("video")[0].firstChild.data
        # Add base Opencast-files directory
        video_src_1 = os.path.join(
            settings.MEDIA_ROOT, 'opencast-files', video_presenter_src
        )
    # Video 2
    if xmldoc.getElementsByTagName("video")[1].firstChild:
        video_presentation_src = xmldoc.getElementsByTagName("video")[1].firstChild.data
        # Add base Opencast-files directory
        video_src_2 = os.path.join(
            settings.MEDIA_ROOT, 'opencast-files', video_presentation_src
        )
    # Start
    clip_begin = xmldoc.getElementsByTagName("cut")[0].getAttribute("clipBegin")
    # End
    clip_end = xmldoc.getElementsByTagName("cut")[0].getAttribute("clipEnd")

    # Error management
    if not video_src_1 and not video_src_2:
        add_comment(recording.id, "Error : video_src_1 and video_src_2 are not defined !")
        return -1

    # Video file output : at the same directory than the SMIL file
    # And with the same name .mp4
    videoOuput = recording.source_file.replace(".smil", ".mp4")

    # Global size
    width = "1920"
    height = "1080"
    # Video 1 width
    video1width = "960"
    # Video 2 width
    video2width = "960"
    leftmargin = "0"
    # ffmpeg command to merge the 2 videos
    command = FFMPEG + " "
    # Cutting begin options (before -i).
    if clip_begin:
        # Bad format by default, conversion seems necessary
        number_seconds_begin = round(float(clip_begin.replace("s", "")))
        # Cut the beginning
        command += "-ss " + str(number_seconds_begin) + " "
    # Input : the 2 videos
    command += " -i \"" + video_src_1 + "\" -i \"" + video_src_2 + "\" "
    # Filter
    command += "-filter_complex \""
    # Filter for left video (1)
    command += "[0]scale=" + video1width + ":-1"
    command += ":force_original_aspect_ratio=decrease, pad=" + width
    command += ":" + height + ":" + leftmargin + ":(" + height + "-ih)/2 [LEFT];"
    # Filter for right video (2)
    command += "[1] scale=" + video2width + ":-1"
    command += ":force_original_aspect_ratio=decrease [RIGHT]; "
    command += "[LEFT][RIGHT] overlay=" + video1width + ":(main_h/2)-(overlay_h/2)\" "
    # Options
    command += "-r 25 -ac 1 -crf 22 -preset fast -threads 0 "
    command += "-s " + width + "x" + height + " "
    # Cutting end options (before output).
    if clip_end:
        # When e appears, seems the end of file
        if "e" not in clip_end:
            # Bad format by default, conversion seems necessary
            number_seconds_end = round(float(clip_end.replace("s", "")))
            if number_seconds_begin:
                number_seconds_end = number_seconds_end - number_seconds_begin
            # Cut the end
            command += "-to " + str(number_seconds_end) + " "
    # Output
    command += videoOuput

    msg = "\nStudioEncodeCommand :\n%s" % command
    msg += "\n- Encoding : %s" % time.ctime()

    # Execute the process
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    msg += "\n- recording id : %s" % id
    msg += "\n- video_src_1 : %s" % video_src_1
    msg += "\n- video_src_2 : %s" % video_src_2
    msg += "\n- clip_begin : %s" % clip_begin
    msg += "\n- clip_end : %s" % clip_end
    msg += "\n- End Encoding : %s" % time.ctime()

    add_comment(recording.id, msg)

    # Rename the SMIL file
    os.rename(recording.source_file, recording.source_file + "_treated")
