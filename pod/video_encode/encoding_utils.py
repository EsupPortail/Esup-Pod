import subprocess
import shlex
import json
from collections import OrderedDict
from timeit import default_timer as timer
import os

try:
    from .encoding_settings import VIDEO_RENDITIONS
except (ImportError, ValueError):
    from encoding_settings import VIDEO_RENDITIONS


def get_renditions():
    try:
        from pod.video.models import VideoRendition
        from django.core import serializers

        renditions = json.loads(
            serializers.serialize("json", VideoRendition.objects.all())
        )
        video_rendition = []
        for rend in renditions:
            video_rendition.append(rend["fields"])
        return video_rendition
    except ImportError:
        return VIDEO_RENDITIONS


def check_file(path_file):
    if os.access(path_file, os.F_OK) and os.stat(path_file).st_size > 0:
        return True
    return False


def get_list_rendition():
    list_rendition = {}
    renditions = get_renditions()
    for rend in renditions:
        list_rendition[int(rend["resolution"].split("x")[1])] = rend
    list_rendition = OrderedDict(sorted(list_rendition.items(), key=lambda t: t[0]))
    return list_rendition


def get_info_from_video(probe_cmd):
    info = None
    msg = ""
    try:
        output = subprocess.check_output(shlex.split(probe_cmd), stderr=subprocess.PIPE)
        info = json.loads(output)
    except subprocess.CalledProcessError as e:
        # raise RuntimeError('ffprobe returned non-zero status: {}'.format(
        # e.stderr))
        msg += 20 * "////" + "\n"
        msg += "Runtime Error: {0}\n".format(e)
    except OSError as err:
        # raise OSError(e.errno, 'ffprobe not found: {}'.format(e.strerror))
        msg += 20 * "////" + "\n"
        msg += "OS error: {0}\n".format(err)
    return info, msg


def launch_cmd(cmd):
    if cmd == "":
        return False, "No cmd to launch"
    msg = ""
    encode_start = timer()
    return_value = False
    try:
        output = subprocess.run(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        encode_end = timer() - encode_start
        msg += cmd + "\n"
        msg += "Encode file in {:.3}s.\n".format(encode_end)
        # msg += "\n".join(output.stdout.decode().split('\n'))
        try:
            msg += output.stdout.decode("utf-8")
        except UnicodeDecodeError:
            pass
        msg += "\n"
        if output.returncode != 0:
            msg += "ERROR RETURN CODE %s for command %s" % (output.returncode, cmd)
        else:
            return_value = True
    except (subprocess.CalledProcessError, OSError) as e:
        # raise RuntimeError('ffmpeg returned non-zero status: {}'.format(
        # e.stderr))
        msg += 20 * "////" + "\n"
        msg += "Runtime or OsError Error: {0}\n".format(e)
    return return_value, msg
