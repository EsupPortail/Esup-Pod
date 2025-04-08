from collections import OrderedDict
from timeit import default_timer as timer

import json
import os
import shlex
import subprocess
import logging

try:
    from .encoding_settings import VIDEO_RENDITIONS
except (ImportError, ValueError):
    from encoding_settings import VIDEO_RENDITIONS

try:
    from django.conf import settings

    VIDEO_RENDITIONS = getattr(settings, "VIDEO_RENDITIONS", VIDEO_RENDITIONS)
    DEBUG = getattr(settings, "DEBUG", True)
except ImportError:  # pragma: no cover
    DEBUG = True
    pass

logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)


def sec_to_timestamp(total_seconds) -> str:
    """Format time for webvtt caption."""
    hours = int(total_seconds / 3600)
    minutes = int(total_seconds / 60 - hours * 60)
    seconds = total_seconds - hours * 3600 - minutes * 60
    return "{:02d}:{:02d}:{:06.3f}".format(hours, minutes, seconds)


def get_dressing_position_value(position: str, height: str) -> str:
    """
    Obtain dimensions proportional to the video format.

    Args:
        position (str): property "position" of the dressing object.
        height (str): height of the source video.

    Returns:
        str: params for the ffmpeg command.
    """
    height = str(float(height) * 0.05)
    if position == "top_right":
        return "overlay=main_w-overlay_w-" + height + ":" + height
    elif position == "top_left":
        return "overlay=" + height + ":" + height
    elif position == "bottom_right":
        return "overlay=main_w-overlay_w-" + height + ":main_h-overlay_h-" + height
    elif position == "bottom_left":
        return "overlay=" + height + ":main_h-overlay_h-" + height


def get_renditions():
    try:
        from .models import VideoRendition
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


def check_file(path_file) -> bool:
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
        msg = "No cmd to launch"
        logger.warning(msg)
        return False, msg
    msg = ""
    encode_start = timer()
    return_value = False
    try:
        logger.debug("launch_cmd: %s" % cmd)
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
        err_msg = "Runtime or OS Error: {0}\n".format(e)
        msg += err_msg
        logger.error(err_msg)
    return return_value, msg
