"""This module handles studio encoding with CPU."""
from django.conf import settings
from .utils import check_file, send_email_recording
from . import encode

import time
import subprocess
import json

from .encoding_settings import (
    FFMPEG_CMD,
    FFPROBE_CMD,
    FFMPEG_CRF,
    FFMPEG_NB_THREADS,
    FFPROBE_GET_INFO,
    FFMPEG_STUDIO_COMMAND,
)

FFMPEG_CMD = getattr(settings, "FFMPEG_CMD", FFMPEG_CMD)
FFPROBE_CMD = getattr(settings, "FFPROBE_CMD", FFPROBE_CMD)
FFMPEG_CRF = getattr(settings, "FFMPEG_CRF", FFMPEG_CRF)
FFMPEG_NB_THREADS = getattr(settings, "FFMPEG_NB_THREADS", FFMPEG_NB_THREADS)
FFPROBE_GET_INFO = getattr(settings, "FFPROBE_GET_INFO", FFPROBE_GET_INFO)
FFMPEG_STUDIO_COMMAND = getattr(settings, "FFMPEG_STUDIO_COMMAND", FFMPEG_STUDIO_COMMAND)

DEBUG = getattr(settings, "DEBUG", True)

ENCODE_VIDEO = getattr(settings, "ENCODE_VIDEO", "start_encode")

# ##########################################################################
# ENCODE VIDEO STUDIO: MAIN ENCODE
# ##########################################################################


def get_video_info(command):
    """Get ffprobe video info."""
    ffproberesult = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return json.loads(ffproberesult.stdout.decode("utf-8"))


def encode_video_studio(recording_id, video_output, videos, subtime, presenter):
    """Encode video from studio."""
    presenter_source = None
    presentation_source = None
    input_video = ""
    for video in videos:
        if video.get("type") == "presenter/source":
            presenter_source = video.get("src")
            input_video = '-i "' + presenter_source + '" '
        if video.get("type") == "presentation/source":
            presentation_source = video.get("src")
            input_video = '-i "' + presentation_source + '" '
    info_presenter_video = {}
    info_presentation_video = {}
    if presenter_source and presentation_source:
        # to put it in the right order
        input_video = '-i "' + presentation_source + '" -i "' + presenter_source + '" '
        command = FFPROBE_GET_INFO % {
            "ffprobe": FFPROBE_CMD,
            "select_streams": "-select_streams v:0 ",
            "source": '"' + presentation_source + '" ',
        }
        info_presentation_video = get_video_info(command)
        command = FFPROBE_GET_INFO % {
            "ffprobe": FFPROBE_CMD,
            "select_streams": "-select_streams v:0 ",
            "source": '"' + presenter_source + '" ',
        }
        info_presenter_video = get_video_info(command)
        subcmd = get_sub_cmd(
            get_height(info_presentation_video),
            get_height(info_presenter_video),
            presenter,
        )

    else:
        subcmd = " -vsync 0 "
    subcmd += " -movflags +faststart -f mp4 "

    msg = launch_encode_video_studio(input_video, subtime, subcmd, video_output)
    from pod.recorder.models import Recording

    recording = Recording.objects.get(id=recording_id)
    recording.comment += msg
    recording.save()
    if check_file(video_output):
        from pod.recorder.plugins.type_studio import save_basic_video

        video = save_basic_video(recording, video_output)
        encode_video = getattr(encode, ENCODE_VIDEO)
        encode_video(video.id, False)
    else:
        msg = "Wrong file or path:" + "\n%s" % video_output
        send_email_recording(msg, recording_id)


def get_sub_cmd(height_presentation_video, height_presenter_video, presenter):
    min_height = min([height_presentation_video, height_presenter_video])
    subcmd = ""
    if presenter == "pipb":
        # trouver la bonne hauteur en fonction de la video de presentation
        height = (
            height_presentation_video
            if (height_presentation_video % 2) == 0
            else height_presentation_video + 1
        )
        # ffmpeg -y -i presentation_source.webm -i presenter_source.webm \
        # -c:v libx264 -filter_complex "[0:v]scale=-2:720[pres];[1:v]scale=-2:180[pip];\
        # [pres][pip]overlay=W-w-10:H-h-10:shortest=1" \
        # -vsync 0 outputVideo.mp4
        subcmd = (
            " -filter_complex "
            + '"[0:v]scale=-2:%(height)s[pres];[1:v]scale=-2:%(sh)s[pip];'
            % {"height": height, "sh": height / 4}
            + '[pres][pip]overlay=W-w-10:H-h-10:shortest=1" -vsync 0 '
        )
    if presenter == "piph":
        # trouver la bonne hauteur en fonction de la video de presentation
        height = (
            height_presentation_video
            if (height_presentation_video % 2) == 0
            else height_presentation_video + 1
        )
        # ffmpeg -y -i presentation_source.webm -i presenter_source.webm \
        # -c:v libx264 -filter_complex "[0:v]scale=-2:720[pres];[1:v]scale=-2:180[pip];\
        # [pres][pip]overlay=W-w-10:H-h-10:shortest=1" \
        # -vsync 0 outputVideo.mp4
        subcmd = (
            " -filter_complex "
            + '"[0:v]scale=-2:%(height)s[pres];[1:v]scale=-2:%(sh)s[pip];'
            % {"height": height, "sh": height / 4}
            + '[pres][pip]overlay=W-w-10:10:shortest=1" -vsync 0 '
        )
    if presenter == "mid":
        height = min_height if (min_height % 2) == 0 else min_height + 1
        # ffmpeg -i presentation.webm -i presenter.webm \
        # -c:v libx264 -filter_complex "[0:v]scale=-2:720[left];[left][1:v]hstack" \
        # outputVideo.mp4
        subcmd = (
            " -filter_complex "
            + '"[0:v]scale=-2:%(height)s[left];[1:v]scale=-2:%(height)s[right];'
            % {"height": height}
            + '[left][right]hstack" -vsync 0 '
        )

    return subcmd


def get_height(info):
    """Get the height value from the given video information dictionary."""
    in_height = 0
    if len(info["streams"]) > 0 and info["streams"][0].get("height"):
        in_height = info["streams"][0]["height"]
    return in_height


def launch_encode_video_studio(input_video, subtime, subcmd, video_output):
    """Encode video for studio."""
    msg = ""
    partial_command = FFMPEG_STUDIO_COMMAND % {
        "nb_threads": FFMPEG_NB_THREADS,
        "input": input_video,
        "subtime": subtime,
        "crf": FFMPEG_CRF,
    }
    ffmpegStudioCommand = "%s %s %s %s" % (
        FFMPEG_CMD,
        partial_command,
        subcmd,
        video_output,
    )
    msg += "- %s\n" % ffmpegStudioCommand
    logfile = video_output.replace(".mp4", ".log")
    ffmpegstudio = subprocess.run(
        ffmpegStudioCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    with open(logfile, "ab") as f:
        f.write(b"\n\ffmpegstudio:\n\n")
        f.write(ffmpegstudio.stdout)
    msg += "\n- Encoding Mp4: %s" % time.ctime()
    if DEBUG:
        print(msg)
        print(ffmpegstudio.stdout)
        print(ffmpegstudio.stderr)
    return msg
