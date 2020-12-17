from django.conf import settings
from django.core.files import File

import time
import logging
import threading
import subprocess
import shlex
import os
import json
import re

from .models import Video

from .utils import change_encoding_step, add_encoding_log, check_file
from .utils import create_outputdir, send_email, send_email_encoding

if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel

log = logging.getLogger(__name__)

DEBUG = getattr(settings, 'DEBUG', True)

SSH_TRANSCRIPT_REMOTE_USER = getattr(
    settings, 'SSH_TRANSCRIPT_REMOTE_USER', "")
SSH_TRANSCRIPT_REMOTE_HOST = getattr(
    settings, 'SSH_TRANSCRIPT_REMOTE_HOST', "")
SSH_TRANSCRIPT_REMOTE_KEY = getattr(
    settings, 'SSH_TRANSCRIPT_REMOTE_KEY', "")
SSH_TRANSCRIPT_REMOTE_CMD = getattr(
    settings, 'SSH_TRANSCRIPT_REMOTE_CMD', "")


# ##########################################################################
# REMOTE TRANSCRIPT VIDEO : MAIN FUNCTION
# ##########################################################################


def remote_transcript_video(video_id):
    start = "Start transcript at : %s" % time.ctime()
    msg = ""
    change_encoding_step(
        video_id, 5,
        "transcripting audio")

    video_to_encode = Video.objects.get(id=video_id)

    encoding_log, created = EncodingLog.objects.get_or_create(
        video=video_to_encode)
    encoding_log.log = "%s\n%s" % (encoding_log.log, start)
    encoding_log.save()

    mp3file = video_to_encode.get_video_mp3(
        ).source_file if video_to_encode.get_video_mp3() else None

    if mp3file and check_file(mp3file.path):

        # launch remote encoding
        cmd = "{remote_cmd} \
            -n encoding-{video_id} -i {video_input} \
            -v {video_id} -u {user_hashkey} -d {debug}".format(
            remote_cmd=SSH_TRANSCRIPT_REMOTE_CMD,
            video_id=video_id,
            video_input=os.path.basename(video_to_encode.video.name),
            user_hashkey=video_to_encode.owner.owner.hashkey,
            debug=DEBUG
        )

        key = " -i %s " % SSH_TRANSCRIPT_REMOTE_KEY if SSH_TRANSCRIPT_REMOTE_KEY != "" else ""

        remote_cmd = "ssh {key} {user}@{host} \"{cmd}\"".format(
            key=key, user=SSH_TRANSCRIPT_REMOTE_USER, host=SSH_TRANSCRIPT_REMOTE_HOST, cmd=cmd)

        # launch remote encode
        change_encoding_step(video_id, 5, "process remote transcipt")
        add_encoding_log(video_id, "process remote transcipt : %s" % remote_cmd)
        process_cmd(remote_cmd, video_id)

    else:
        msg += "Wrong mp3 file or path : "\
            + "\n%s" % mp3file.path
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)


def process_cmd(remote_cmd, video_id):
    msg = ""
    try:
        output = subprocess.run(
            shlex.split(remote_cmd), stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        add_encoding_log(video_id, "slurm output : %s" % output.stdout)
        if DEBUG:
            print(output.stdout)
        if output.returncode != 0:
            msg += 20*"////" + "\n"
            msg += "ERROR RETURN CODE: {0}\n".format(output.returncode)
            msg += output
            add_encoding_log(video_id, msg)
            change_encoding_step(video_id, -1, msg)
            send_email(msg, video_id)
    except subprocess.CalledProcessError as e:
        # raise RuntimeError('ffprobe returned non-zero status: {}'.format(
        # e.stderr))
        msg += 20*"////" + "\n"
        msg += "Runtime Error: {0}\n".format(e)
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)
    except OSError as err:
        # raise OSError(e.errno, 'ffprobe not found: {}'.format(e.strerror)
        msg += 20*"////" + "\n"
        msg += "OS error: {0}\n".format(err)
        add_encoding_log(video_id, msg)
        change_encoding_step(video_id, -1, msg)
        send_email(msg, video_id)