"""This module handles video encoding with CPU."""

from django.conf import settings
from .models import EncodingVideo
from .models import EncodingAudio
from .models import PlaylistVideo
from .models import Video
from .utils import send_email_recording
from .utils import change_encoding_step, check_file, add_encoding_log, send_email
from .Encoding_video_model import Encoding_video_model

# from pod.main.context_processors import TEMPLATE_VISIBLE_SETTINGS
from pod.main.tasks import task_start_encode, task_start_encode_studio

# from fractions import Fraction # use for keyframe
import logging
import os
import time
import subprocess
import threading
import json

__license__ = "LGPL v3"

TRANSCRIPT = getattr(settings, "USE_TRANSCRIPTION", False)

if TRANSCRIPT:
    from . import transcript

    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")

ENCODE_SHELL = getattr(settings, "ENCODE_SHELL", "/bin/sh")

USE_ESTABLISHMENT = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)

SPLIT_ENCODE_CMD = getattr(settings, "SPLIT_ENCODE_CMD", False)

FFMPEG = getattr(settings, "FFMPEG", "ffmpeg")
FFPROBE = getattr(settings, "FFPROBE", "ffprobe")
DEBUG = getattr(settings, "DEBUG", True)

log = logging.getLogger(__name__)

# try to create a new segment every X seconds
SEGMENT_TARGET_DURATION = getattr(settings, "SEGMENT_TARGET_DURATION", 2)
# maximum accepted bitrate fluctuations
# MAX_BITRATE_RATIO = getattr(settings, 'MAX_BITRATE_RATIO', 1.07)
# maximum buffer size between bitrate conformance checks
RATE_MONITOR_BUFFER_RATIO = getattr(settings, "RATE_MONITOR_BUFFER_RATIO", 2)
# maximum threads use by ffmpeg
FFMPEG_NB_THREADS = getattr(settings, "FFMPEG_NB_THREADS", 0)

GET_INFO_VIDEO = getattr(
    settings,
    "GET_INFO_VIDEO",
    "%(ffprobe)s -v quiet -show_format -show_streams -select_streams v:0 "
    + "-print_format json -i %(source)s",
)

GET_INFO_AUDIO = getattr(
    settings,
    "GET_INFO_AUDIO",
    "%(ffprobe)s -v quiet -show_format -show_streams -select_streams a:0 "
    + "-print_format json -i %(source)s",
)

FFMPEG_STATIC_PARAMS = getattr(
    settings,
    "FFMPEG_STATIC_PARAMS",
    " -c:a aac -ar 48000 -c:v h264 -profile:v high -pix_fmt yuv420p -crf %(crf)s "
    + '-sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" '
    + "-max_muxing_queue_size 4000 "
    + "-deinterlace -threads %(nb_threads)s ",
)

FFMPEG_CRF = getattr(settings, "FFMPEG_CRF", 22)
# + "-deinterlace -threads %(nb_threads)s -g %(key_frames_interval)s "
# + "-keyint_min %(key_frames_interval)s ")

FFMPEG_MISC_PARAMS = getattr(settings, "FFMPEG_MISC_PARAMS", " -hide_banner -y -vsync 0 ")
# to use in GPU, specify for example
# -y -vsync 0 -hwaccel_device {hwaccel_device} \
# -hwaccel cuvid -c:v {codec}_cuvid

FFMPEG_SCALE = getattr(settings, "FFMPEG_SCALE", ' -vf "scale=-2:{height}" ')
# to use in GPU, specify ' -vf "scale_npp=-2:{height}:interp_algo=super" '

AUDIO_BITRATE = getattr(settings, "AUDIO_BITRATE", "192k")

ENCODING_M4A = getattr(
    settings,
    "ENCODING_M4A",
    "%(ffmpeg)s -i %(source)s %(misc_params)s -c:a aac -b:a %(audio_bitrate)s "
    + "-vn -threads %(nb_threads)s "
    + '"%(output_dir)s/audio_%(audio_bitrate)s.m4a"',
)

ENCODE_MP3_CMD = getattr(
    settings,
    "ENCODE_MP3_CMD",
    "%(ffmpeg)s -i %(source)s %(misc_params)s -vn -b:a %(audio_bitrate)s "
    + "-vn -f mp3 -threads %(nb_threads)s "
    + '"%(output_dir)s/audio_%(audio_bitrate)s.mp3"',
)

EMAIL_ON_ENCODING_COMPLETION = getattr(settings, "EMAIL_ON_ENCODING_COMPLETION", True)

FILE_UPLOAD_TEMP_DIR = getattr(settings, "FILE_UPLOAD_TEMP_DIR", "/tmp")

##
# Settings exposed in templates
#
TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "TITLE_ETB": "University name",
        "LOGO_SITE": "img/logoPod.svg",
        "LOGO_ETB": "img/logo_etb.svg",
        "LOGO_PLAYER": "img/logoPod.svg",
        "LINK_PLAYER": "",
        "FOOTER_TEXT": ("",),
        "FAVICON": "img/logoPod.svg",
        "CSS_OVERRIDE": "",
        "PRE_HEADER_TEMPLATE": "",
        "POST_FOOTER_TEMPLATE": "",
        "TRACKING_TEMPLATE": "",
    },
)

TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, "TITLE_SITE", "Pod")

DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")

CELERY_TO_ENCODE = getattr(settings, "CELERY_TO_ENCODE", False)

MANAGERS = getattr(settings, "MANAGERS", {})

OPENCAST_FILES_DIR = getattr(settings, "OPENCAST_FILES_DIR", "opencast-files")

# ##########################################################################
# ENCODE VIDEO: THREAD TO LAUNCH ENCODE
# ##########################################################################

# Disable for the moment, will be reactivated in future version
"""
def start_remote_encode(video_id):
    # load module here to prevent circular import
    from .remote_encode import remote_encode_video

    log.info("START ENCODE VIDEO ID %s" % video_id)
    t = threading.Thread(target=remote_encode_video, args=[video_id])
    t.setDaemon(True)
    t.start()
"""


def start_encode(video_id):
    """Start local encoding."""
    if CELERY_TO_ENCODE:
        task_start_encode.delay(video_id)
    else:
        log.info("START ENCODE VIDEO ID %s" % video_id)
        t = threading.Thread(target=encode_video, args=[video_id])
        t.setDaemon(True)
        t.start()


def start_encode_studio(recording_id, video_output, videos, subtime, presenter):
    """Start local encoding."""
    if CELERY_TO_ENCODE:
        task_start_encode_studio.delay(
            recording_id, video_output, videos, subtime, presenter
        )
    else:
        log.info("START ENCODE VIDEO ID %s" % recording_id)
        t = threading.Thread(
            target=encode_video_studio,
            args=[recording_id, video_output, videos, subtime, presenter],
        )
        t.setDaemon(True)
        t.start()


def start_studio_remote_encode(recording_id, video_output, videos, subtime, presenter):
    """Start Remote encoding."""
    # load module here to prevent circular import
    from .remote_encode import remote_encode_studio

    log.info("START ENCODE RECORDING ID %s" % recording_id)
    t = threading.Thread(
        target=remote_encode_studio,
        args=[recording_id, video_output, videos, subtime, presenter],
    )
    t.setDaemon(True)
    t.start()


# ##########################################################################
# ENCODE VIDEO: MAIN FUNCTION
# ##########################################################################


def encode_video(video_id):
    start = "Start at: %s" % time.ctime()

    video_to_encode = Video.objects.get(id=video_id)
    video_to_encode.encoding_in_progress = True
    video_to_encode.save()

    if not check_file(video_to_encode.video.path):
        msg = "Wrong file or path:" + "\n%s" % video_to_encode.video.path
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)
        return

    change_encoding_step(video_id, 0, "start")

    encoding_video = Encoding_video_model(video_id, video_to_encode.video.path)
    # TODO add true log
    # encoding_video.encoding_log += start
    change_encoding_step(video_id, 1, "get video data")
    encoding_video.get_video_data()
    change_encoding_step(video_id, 2, "remove old data")
    encoding_video.remove_old_data()
    # create video dir
    change_encoding_step(video_id, 3, "create output dir")
    encoding_video.create_output_dir()

    encoding_video.start_encode()

    # encode HLS
    # encode MP4
    # encode MP3
    # encode M4A


def transcript_video(video_id):
    """Transcript video audio to text."""
    video = Video.objects.get(id=video_id)
    if TRANSCRIPT and video.transcript:
        start_transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
        start_transcript_video(video_id, False)


###############################################################
# REMOVE ENCODING
###############################################################

def remove_previous_overview(overviewfilename, overviewimagefilename):
    """Remove previous overview."""
    if os.path.isfile(overviewimagefilename):
        os.remove(overviewimagefilename)
    if os.path.isfile(overviewfilename):
        os.remove(overviewfilename)


def remove_old_data(video_id):
    """Remove old data."""
    video_to_encode = Video.objects.get(id=video_id)
    video_to_encode.thumbnail = None
    if video_to_encode.overview:
        image_overview = os.path.join(
            os.path.dirname(video_to_encode.overview.path), "overview.png"
        )
        if os.path.isfile(image_overview):
            os.remove(image_overview)
        video_to_encode.overview.delete()
    video_to_encode.overview = None
    video_to_encode.save()

    encoding_log_msg = ""
    encoding_log_msg += remove_previous_encoding_video(video_to_encode)
    encoding_log_msg += remove_previous_encoding_audio(video_to_encode)
    encoding_log_msg += remove_previous_encoding_playlist(video_to_encode)
    return encoding_log_msg


def remove_previous_encoding_video(video_to_encode):
    """Remove previously encoded video."""
    msg = "\n"
    previous_encoding_video = EncodingVideo.objects.filter(video=video_to_encode)
    if len(previous_encoding_video) > 0:
        msg += "\nDELETE PREVIOUS ENCODING VIDEO"
        # previous_encoding.delete()
        for encoding in previous_encoding_video:
            encoding.delete()
    else:
        msg += "Video: Nothing to delete"
    return msg


def remove_previous_encoding_audio(video_to_encode):
    """Remove previously encoded audio."""
    msg = "\n"
    previous_encoding_audio = EncodingAudio.objects.filter(video=video_to_encode)
    if len(previous_encoding_audio) > 0:
        msg += "\nDELETE PREVIOUS ENCODING AUDIO"
        # previous_encoding.delete()
        for encoding in previous_encoding_audio:
            encoding.delete()
    else:
        msg += "Audio: Nothing to delete"
    return msg


def remove_previous_encoding_playlist(video_to_encode):
    """Remove previously encoded playlist."""
    msg = "\n"
    previous_playlist = PlaylistVideo.objects.filter(video=video_to_encode)
    if len(previous_playlist) > 0:
        msg += "DELETE PREVIOUS PLAYLIST M3U8"
        # previous_encoding.delete()
        for encoding in previous_playlist:
            encoding.delete()
    else:
        msg += "Playlist: Nothing to delete"
    return msg


# ##########################################################################
# ENCODE VIDEO STUDIO: MAIN ENCODE
# ##########################################################################

# Temporary re putting that for studio
def get_video_info(command):
    ffproberesult = subprocess.run(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return json.loads(ffproberesult.stdout.decode("utf-8"))


def encode_video_studio(recording_id, video_output, videos, subtime, presenter):
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
        command = GET_INFO_VIDEO % {
            "ffprobe": FFPROBE,
            "source": '"' + presentation_source + '" ',
        }
        info_presentation_video = get_video_info(command)
        command = GET_INFO_VIDEO % {
            "ffprobe": FFPROBE,
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
    static_params = FFMPEG_STATIC_PARAMS % {
        "nb_threads": FFMPEG_NB_THREADS,
        "crf": FFMPEG_CRF,
    }
    msg = launch_encode_video_studio(
        input_video, subtime + static_params + subcmd, video_output
    )
    from pod.recorder.models import Recording

    recording = Recording.objects.get(id=recording_id)
    recording.comment += msg
    recording.save()
    if check_file(video_output):
        from pod.recorder.plugins.type_studio import save_basic_video

        video = save_basic_video(recording, video_output)
        encode_video(video.id)
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
    in_height = 0
    if len(info["streams"]) > 0 and info["streams"][0].get("height"):
        in_height = info["streams"][0]["height"]
    return in_height


def launch_encode_video_studio(input_video, subcmd, video_output):
    """Encode video for studio."""

    msg = ""
    ffmpegStudioCommand = "%s %s %s %s %s" % (
        FFMPEG,
        FFMPEG_MISC_PARAMS,
        input_video,
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
