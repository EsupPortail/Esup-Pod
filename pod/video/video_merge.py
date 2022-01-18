import subprocess
import time
import threading
import logging

from django.conf import settings
from pod.main.tasks import task_start_video_merge
# from pod.recorder.utils import add_comment

# Tools
FFMPEG = getattr(settings, "FFMPEG", "ffmpeg")
FFPROBE = getattr(settings, "FFPROBE", "ffprobe")
# Debug mode
DEBUG = getattr(settings, "DEBUG", False)
# Use of Celery to encode
CELERY_TO_ENCODE = getattr(settings, "CELERY_TO_ENCODE", False)

# Logger (not Log4j :) )
log = logging.getLogger(__name__)


def start_video_merge(video_1, video_2, video_output, clip_begin, clip_end):
    if CELERY_TO_ENCODE:
        task_start_video_merge.delay(video_1, video_2, video_output)
    else:
        log.info("START VIDEO MERGE FROM %s and %s" % (video_1, video_2))
        t = threading.Thread(
            target=studio_encode_videos, args=[video_1, video_2, video_output]
        )
        t.setDaemon(False)
        t.start()


def merge_videos(video_1, video_2, video_output, clip_begin, clip_end): # noqa: max-complexity: 13
    # Generate an intermediate video for a Studio session
    # This happens when we need to merge 2 videos or to cut at least one video

    msg = ""

    # TODO : START AND FINISH
    # Start
    # clip_begin = 0  # xmldoc.getElementsByTagName("cut")[0].getAttribute("clipBegin")
    # End
    # clip_end = 0  # xmldoc.getElementsByTagName("cut")[0].getAttribute("clipEnd")

    # Error management
    if not video_1 and not video_2:
        # TODO : find solution for logger
        # add_comment(recording.id, "Error : video_1 and video_2 are not defined !")
        return -1

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
        number_seconds_begin = round(float(clip_begin))
        # Cut the beginning
        command += "-ss " + str(clip_begin) + " "

    # Management to merge 2 videos
    if video_1 and video_2:
        # Input : the 2 videos
        command += "-i \"" + video_1 + "\" -i \"" + video_2 + "\" "
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
        command += "-r 25 -ac 1 -crf 20 -preset fast -threads 0 "
        command += "-s " + width + "x" + height + " "
    elif video_1:
        # Input : only one, the presenter
        command += "-i \"" + video_1 + "\" "
        # Transcode to mp4
        command += "-r 25 -ac 1 -crf 20 -preset fast -threads 0 "
    elif video_2:
        # Input : only one, the presentation
        command += "-i \"" + video_2 + "\" "
        # Transcode to mp4
        command += "-r 25 -ac 1 -crf 20 -preset fast -threads 0 "

    # Cutting end options (before output)
    if clip_end:
        # When e appears, seems the end of file
        if "e" not in clip_end:
            # Calculate
            number_seconds_end = round(float(clip_end))
            if number_seconds_begin:
                number_seconds_end = number_seconds_end - number_seconds_begin
            # Cut the end
            command += "-to " + str(number_seconds_end) + " "
    # Output
    command += video_output

    msg = "\n - Generate intermediate video with this command :\n%s\n" % command
    msg += "\n   Parameters"
    msg += "\n   + recording id : %s" % id
    msg += "\n   + video_1 : %s" % video_1
    msg += "\n   + video_2 : %s" % video_2
    msg += "\n   + clip_begin : %s" % clip_begin
    msg += "\n   + clip_end : %s" % clip_end

    msg += "\n   + Encoding : %s" % time.ctime()

    # Execute the process
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    msg += "\n   + End Encoding : %s" % time.ctime()
    # TODO : same
    # add_comment(recording.id, msg)
