from django.conf import settings
from django.core.files import File


import time
import json
import logging
import subprocess
import shlex
import os
import datetime as dt
from datetime import timedelta

from .models import Video, EncodingLog

from .utils import change_encoding_step, add_encoding_log, check_file
from .utils import send_email, create_outputdir, send_email_transcript

from pod.completion.models import Track

from webvtt import WebVTT, Caption
from tempfile import NamedTemporaryFile

log = logging.getLogger(__name__)

DEBUG = getattr(settings, "DEBUG", True)

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder

    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel

SSH_TRANSCRIPT_REMOTE_USER = getattr(settings, "SSH_TRANSCRIPT_REMOTE_USER", "")
SSH_TRANSCRIPT_REMOTE_HOST = getattr(settings, "SSH_TRANSCRIPT_REMOTE_HOST", "")
SSH_TRANSCRIPT_REMOTE_KEY = getattr(settings, "SSH_TRANSCRIPT_REMOTE_KEY", "")
SSH_TRANSCRIPT_REMOTE_CMD = getattr(settings, "SSH_TRANSCRIPT_REMOTE_CMD", "")

SENTENCE_MAX_LENGTH = getattr(settings, "SENTENCE_MAX_LENGTH", 3)

EMAIL_ON_TRANSCRIPTING_COMPLETION = getattr(
    settings, "EMAIL_ON_TRANSCRIPTING_COMPLETION", True
)

# ##########################################################################
# REMOTE TRANSCRIPT VIDEO : MAIN FUNCTION
# ##########################################################################


def remote_transcript_video(video_id):
    start = "Start transcript at : %s" % time.ctime()
    msg = ""
    change_encoding_step(video_id, 5, "transcripting audio")

    video_to_encode = Video.objects.get(id=video_id)

    encoding_log, created = EncodingLog.objects.get_or_create(video=video_to_encode)
    encoding_log.log = "%s\n%s" % (encoding_log.log, start)
    encoding_log.save()

    mp3file = (
        video_to_encode.get_video_mp3().source_file
        if video_to_encode.get_video_mp3()
        else None
    )

    if mp3file and check_file(mp3file.path):
        # launch remote transcoding
        cmd = "{remote_cmd} \
            -n transcoding-{video_id} -i {video_input} \
            -v {video_id} -u {user_hashkey} -d {debug}".format(
            remote_cmd=SSH_TRANSCRIPT_REMOTE_CMD,
            video_id=video_id,
            video_input=os.path.basename(mp3file.name),
            user_hashkey=video_to_encode.owner.owner.hashkey,
            debug=DEBUG,
        )

        key = (
            " -i %s " % SSH_TRANSCRIPT_REMOTE_KEY
            if (SSH_TRANSCRIPT_REMOTE_KEY != "")
            else ""
        )

        remote_cmd = 'ssh {key} {user}@{host} "{cmd}"'.format(
            key=key,
            user=SSH_TRANSCRIPT_REMOTE_USER,
            host=SSH_TRANSCRIPT_REMOTE_HOST,
            cmd=cmd,
        )

        # launch remote encode
        change_encoding_step(video_id, 5, "process remote transcipt")
        add_encoding_log(video_id, "process remote transcipt : %s" % remote_cmd)
        process_cmd(remote_cmd, video_id)

    else:
        msg += "Wrong mp3 file or path : " + "\n%s" % mp3file.path
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)


def process_cmd(remote_cmd, video_id):
    msg = ""
    try:
        output = subprocess.run(
            shlex.split(remote_cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        add_encoding_log(video_id, "slurm output : %s" % output.stdout)
        if DEBUG:
            print(output.stdout)
        if output.returncode != 0:
            msg += 20 * "////" + "\n"
            msg += "ERROR RETURN CODE: {0}\n".format(output.returncode)
            msg += output
            add_encoding_log(video_id, msg)
            change_encoding_step(video_id, -1, msg)
            send_email(msg, video_id)
    except subprocess.CalledProcessError as e:
        # raise RuntimeError('ffprobe returned non-zero status: {}'.format(
        # e.stderr))
        msg += 20 * "////" + "\n"
        msg += "Runtime Error: {0}\n".format(e)
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)
    except OSError as err:
        # raise OSError(e.errno, 'ffprobe not found: {}'.format(e.strerror)
        msg += 20 * "////" + "\n"
        msg += "OS error: {0}\n".format(err)
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)


def store_remote_transcripting_video(video_id):
    #
    msg = ""
    video_to_encode = Video.objects.get(id=video_id)
    output_dir = create_outputdir(video_id, video_to_encode.video.path)
    info_video = {}

    if check_file(output_dir + "/transcript.json"):
        with open(output_dir + "/transcript.json") as json_file:
            info_video = json.load(json_file)

        print_if_debug(output_dir)
        print_if_debug(json.dumps(info_video, indent=2))

        webvtt = WebVTT()
        # They're sorted by confidence. First one is highest confidence result.
        words = info_video["transcripts"][0]["words"]
        """
        for transcript in info_video["transcripts"]:
            for word in transcript["words"]:
                words.append(word)
        """
        text_caption = []
        start_caption = None
        duration = 0
        for word in words:
            text_caption.append(word["word"])
            if start_caption is None:
                start_caption = word["start_time"]
            if duration + word["duration"] > SENTENCE_MAX_LENGTH:
                caption = Caption(
                    format_time_caption(start_caption),
                    format_time_caption(start_caption + duration + word["duration"]),
                    " ".join(text_caption),
                )
                webvtt.captions.append(caption)
                text_caption = []
                start_caption = None
                duration = 0
            else:
                duration += word["duration"]
        print_if_debug(webvtt)
        msg += saveVTT(video_to_encode, webvtt)
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, 0, "done")
        # envois mail fin transcription
        if EMAIL_ON_TRANSCRIPTING_COMPLETION:
            send_email_transcript(video_to_encode)

    else:
        msg += "Wrong file or path : " + "\n%s" % video_to_encode.video.path
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)


def print_if_debug(msg):
    if DEBUG:
        print(msg)


def format_time_caption(time_caption):
    return (
        dt.datetime.utcfromtimestamp(0) + timedelta(seconds=float(time_caption))
    ).strftime("%H:%M:%S.%f")[:-3]


def saveVTT(video, webvtt):
    msg = "\nSAVE TRANSCRIPT WEBVTT : %s" % time.ctime()
    lang = video.main_lang
    temp_vtt_file = NamedTemporaryFile(suffix=".vtt")
    webvtt.save(temp_vtt_file.name)
    if webvtt.captions:
        msg += "\nstore vtt file in bdd with CustomFileModel model file field"
        if FILEPICKER:
            videodir, created = UserFolder.objects.get_or_create(
                name="%s" % video.slug, owner=video.owner
            )
            """
            previousSubtitleFile = CustomFileModel.objects.filter(
                name__startswith="subtitle_%s" % lang,
                folder=videodir,
                created_by=video.owner
            )
            """
            # for subt in previousSubtitleFile:
            #     subt.delete()
            subtitleFile, created = CustomFileModel.objects.get_or_create(
                name="subtitle_%s_%s" % (lang, time.strftime("%Y%m%d-%H%M%S")),
                folder=videodir,
                created_by=video.owner,
            )
            if subtitleFile.file and os.path.isfile(subtitleFile.file.path):
                os.remove(subtitleFile.file.path)
        else:
            subtitleFile, created = CustomFileModel.objects.get_or_create()

        subtitleFile.file.save(
            "subtitle_%s_%s.vtt" % (lang, time.strftime("%Y%m%d-%H%M%S")),
            File(temp_vtt_file),
        )
        msg += "\nstore vtt file in bdd with Track model src field"

        subtitleVtt, created = Track.objects.get_or_create(video=video, lang=lang)
        subtitleVtt.src = subtitleFile
        subtitleVtt.lang = lang
        subtitleVtt.save()
    else:
        msg += "\nERROR SUBTITLES Output size is 0"
    return msg
