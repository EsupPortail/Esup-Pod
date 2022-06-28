""" This module handles video encoding with CPU or GPU. """

from __future__ import absolute_import, division, print_function
import argparse
import subprocess
import shlex
import json
import time

from timeit import default_timer as timer

# from unidecode import unidecode # third party package to remove accent
# import unicodedata

__author__ = "Nicolas CAN <nicolas.can@univ-lille.fr>"
__license__ = "LGPL v3"

from .models import Video
from .utils import change_encoding_step, check_file, add_encoding_log, send_email

image_codec = ["jpeg", "gif", "png", "bmp", "jpg"]

"""
 - Get video source
 - get alls track from video source
 - encode tracks in HLS and mp4
 - save it
"""


class Encoding_video:
    id = 0
    video_file = ""
    duration = 0
    list_video_track = []
    list_audio_track = []
    list_subtitle_track = []
    list_image_track = []
    encoding_log = ""

    def is_video(self):
        return len(self.list_video_track) > 0


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

    change_encoding_step(video_id, 0, "start")

    encoding_video = Encoding_video()
    encoding_video.id = video_id
    encoding_video.video_file = video_to_encode.video.path
    encoding_video.encoding_log += start

    get_video_data(encoding_video)


def get_video_data(encoding_video):
    """
    get alls tracks from video source and put it in object passed in parameter
    """
    msg = "--> get_info_video" + "\n"
    probe_cmd = "ffprobe -v quiet -show_format -show_streams \
                -print_format json -i {}".format(encoding_video.video_file)
    msg += probe_cmd + "\n"
    duration = 0
    info, return_msg = get_info_from_video(probe_cmd)
    msg += json.dumps(info, indent=2)
    msg += " \n"
    msg += return_msg + "\n"
    try:
        duration = int(float("%s" % info["format"]["duration"]))
    except (RuntimeError, KeyError, AttributeError, ValueError) as err:
        msg += "\nUnexpected error: {0}".format(err)
    encoding_video.duration = duration
    streams = info.get("streams", [])
    for stream in streams:
        add_stream(stream, encoding_video)


def add_stream(stream, encoding_video):
    codec_type = stream.get("codec_type", "unknown")
    # https://ffmpeg.org/doxygen/3.2/group__lavu__misc.html#ga9a84bba4713dfced21a1a56163be1f48
    if codec_type == "audio":
        encoding_video.list_audio_track[stream.get("index")] = {
            "sample_rate": stream.get("sample_rate", 0),
            "channels": stream.get("channels", 0),
        }
    if codec_type == "video":
        codec = stream.get("codec_name", "unknown")
        if any(ext in codec.lower() for ext in image_codec):
            encoding_video.list_image_track[stream.get("index")] = {
                "width": stream.get("width", 0),
                "height": stream.get("height", 0)
            }
        else:
            encoding_video.list_video_track[stream.get("index")] = {
                "width": stream.get("width", 0),
                "height": stream.get("height", 0)
            }
    if codec_type == "subtitle":
        encoding_video.list_subtitle_track[stream.get("index")] = {}


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
            msg += "ERROR RETURN CODE %s for command %s" % (
                output.returncode,
                cmd
            )
        else:
            return_value = True
    except subprocess.CalledProcessError as e:
        # raise RuntimeError('ffmpeg returned non-zero status: {}'.format(
        # e.stderr))
        msg += 20 * "////" + "\n"
        msg += "Runtime Error: {0}\n".format(e)

    except OSError as err:
        # raise OSError(e.errno, 'ffmpeg not found: {}'.format(e.strerror))
        msg += 20 * "////" + "\n"
        msg += "OS error: {0}\n".format(err)
    return return_value, msg


"""
remote encode ???
"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Running encoding video.")
    parser.add_argument("--id", required=True, help="the ID of the video")
    parser.add_argument("--input", required=True, help="name of input file to encode")
    args = parser.parse_args()
