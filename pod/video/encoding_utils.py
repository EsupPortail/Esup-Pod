import subprocess
import shlex
import json
from collections import OrderedDict
from timeit import default_timer as timer

# from django.core import serializers
# serializers.serialize("json", VideoRendition.objects.all())
video_rendition = [
    {"resolution": "640x360", "minrate": "500k", "video_bitrate": "750k", "maxrate": "1000k", "audio_bitrate": "96k", "encode_mp4": True, "sites": [1]},
    {"resolution": "1280x720", "minrate": "1000k", "video_bitrate": "2000k", "maxrate": "3000k", "audio_bitrate": "128k", "encode_mp4": True, "sites": [1]},
    {"resolution": "1920x1080", "minrate": "2000k", "video_bitrate": "3000k", "maxrate": "4500k", "audio_bitrate": "192k", "encode_mp4": False, "sites": [1]},
]


def get_list_rendition():
    list_rendition = {}
    for rend in video_rendition:
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
