"""Encoding video."""
import json
import os
import time
from webvtt import WebVTT, Caption
import argparse
import unicodedata
from pod.dressing.utils import get_position_value, get_dressing_input

if __name__ == "__main__":
    from encoding_utils import (
        get_info_from_video,
        get_list_rendition,
        launch_cmd,
        check_file,
    )
    from encoding_settings import (
        FFMPEG_CMD,
        FFPROBE_CMD,
        FFPROBE_GET_INFO,
        FFMPEG_CRF,
        FFMPEG_PRESET,
        FFMPEG_PROFILE,
        FFMPEG_LEVEL,
        FFMPEG_HLS_TIME,
        FFMPEG_INPUT,
        FFMPEG_LIBX,
        FFMPEG_MP4_ENCODE,
        FFMPEG_HLS_COMMON_PARAMS,
        FFMPEG_HLS_ENCODE_PARAMS,
        FFMPEG_MP3_ENCODE,
        FFMPEG_M4A_ENCODE,
        FFMPEG_NB_THREADS,
        FFMPEG_AUDIO_BITRATE,
        FFMPEG_EXTRACT_THUMBNAIL,
        FFMPEG_NB_THUMBNAIL,
        FFMPEG_CREATE_THUMBNAIL,
        FFMPEG_EXTRACT_SUBTITLE,
        FFMPEG_DRESSING_INPUT,
        FFMPEG_DRESSING_OUTPUT,
        FFMPEG_DRESSING_WATERMARK,
        FFMPEG_DRESSING_FILTER_COMPLEX,
        FFMPEG_DRESSING_SCALE,
        FFMPEG_DRESSING_CONCAT,
    )
else:
    from .encoding_utils import (
        get_info_from_video,
        get_list_rendition,
        launch_cmd,
        check_file,
    )
    from .encoding_settings import (
        FFMPEG_CMD,
        FFPROBE_CMD,
        FFPROBE_GET_INFO,
        FFMPEG_CRF,
        FFMPEG_PRESET,
        FFMPEG_PROFILE,
        FFMPEG_LEVEL,
        FFMPEG_HLS_TIME,
        FFMPEG_INPUT,
        FFMPEG_LIBX,
        FFMPEG_MP4_ENCODE,
        FFMPEG_HLS_COMMON_PARAMS,
        FFMPEG_HLS_ENCODE_PARAMS,
        FFMPEG_MP3_ENCODE,
        FFMPEG_M4A_ENCODE,
        FFMPEG_NB_THREADS,
        FFMPEG_AUDIO_BITRATE,
        FFMPEG_EXTRACT_THUMBNAIL,
        FFMPEG_NB_THUMBNAIL,
        FFMPEG_CREATE_THUMBNAIL,
        FFMPEG_EXTRACT_SUBTITLE,
        FFMPEG_DRESSING_INPUT,
        FFMPEG_DRESSING_OUTPUT,
        FFMPEG_DRESSING_WATERMARK,
        FFMPEG_DRESSING_FILTER_COMPLEX,
        FFMPEG_DRESSING_SCALE,
        FFMPEG_DRESSING_CONCAT,
    )


__author__ = "Nicolas CAN <nicolas.can@univ-lille.fr>"
__license__ = "LGPL v3"

image_codec = ["jpeg", "gif", "png", "bmp", "jpg"]

"""
 - Get video source
 - get alls track from video source
 - encode tracks in HLS and mp4
 - save it
"""

try:
    from django.conf import settings

    FFMPEG_CMD = getattr(settings, "FFMPEG_CMD", FFMPEG_CMD)
    FFPROBE_CMD = getattr(settings, "FFPROBE_CMD", FFPROBE_CMD)
    FFPROBE_GET_INFO = getattr(settings, "FFPROBE_GET_INFO", FFPROBE_GET_INFO)
    FFMPEG_CRF = getattr(settings, "FFMPEG_CRF", FFMPEG_CRF)
    FFMPEG_PRESET = getattr(settings, "FFMPEG_PRESET", FFMPEG_PRESET)
    FFMPEG_PROFILE = getattr(settings, "FFMPEG_PROFILE", FFMPEG_PROFILE)
    FFMPEG_LEVEL = getattr(settings, "FFMPEG_LEVEL", FFMPEG_LEVEL)
    FFMPEG_HLS_TIME = getattr(settings, "FFMPEG_HLS_TIME", FFMPEG_HLS_TIME)
    FFMPEG_INPUT = getattr(settings, "FFMPEG_INPUT", FFMPEG_INPUT)
    FFMPEG_LIBX = getattr(settings, "FFMPEG_LIBX", FFMPEG_LIBX)
    FFMPEG_MP4_ENCODE = getattr(settings, "FFMPEG_MP4_ENCODE", FFMPEG_MP4_ENCODE)
    FFMPEG_HLS_COMMON_PARAMS = getattr(
        settings, "FFMPEG_HLS_COMMON_PARAMS", FFMPEG_HLS_COMMON_PARAMS
    )
    FFMPEG_HLS_ENCODE_PARAMS = getattr(
        settings, "FFMPEG_HLS_ENCODE_PARAMS", FFMPEG_HLS_ENCODE_PARAMS
    )
    FFMPEG_MP3_ENCODE = getattr(settings, "FFMPEG_MP3_ENCODE", FFMPEG_MP3_ENCODE)
    FFMPEG_M4A_ENCODE = getattr(settings, "FFMPEG_M4A_ENCODE", FFMPEG_M4A_ENCODE)
    FFMPEG_NB_THREADS = getattr(settings, "FFMPEG_NB_THREADS", FFMPEG_NB_THREADS)
    FFMPEG_AUDIO_BITRATE = getattr(settings, "FFMPEG_AUDIO_BITRATE", FFMPEG_AUDIO_BITRATE)
    FFMPEG_EXTRACT_THUMBNAIL = getattr(
        settings, "FFMPEG_EXTRACT_THUMBNAIL", FFMPEG_EXTRACT_THUMBNAIL
    )
    FFMPEG_NB_THUMBNAIL = getattr(settings, "FFMPEG_NB_THUMBNAIL", FFMPEG_NB_THUMBNAIL)
    FFMPEG_CREATE_THUMBNAIL = getattr(
        settings, "FFMPEG_CREATE_THUMBNAIL", FFMPEG_CREATE_THUMBNAIL
    )
    FFMPEG_EXTRACT_SUBTITLE = getattr(
        settings, "FFMPEG_EXTRACT_SUBTITLE", FFMPEG_EXTRACT_SUBTITLE
    )
    FFMPEG_DRESSING_INPUT = getattr(
        settings, "FFMPEG_DRESSING_INPUT", FFMPEG_DRESSING_INPUT
    )
    FFMPEG_DRESSING_OUTPUT = getattr(
        settings, "FFMPEG_DRESSING_OUTPUT", FFMPEG_DRESSING_OUTPUT
    )
    FFMPEG_DRESSING_WATERMARK = getattr(
        settings, "FFMPEG_DRESSING_WATERMARK", FFMPEG_DRESSING_WATERMARK
    )
    FFMPEG_DRESSING_FILTER_COMPLEX = getattr(
        settings, "FFMPEG_DRESSING_FILTER_COMPLEX", FFMPEG_DRESSING_FILTER_COMPLEX
    )
    FFMPEG_DRESSING_SCALE = getattr(
        settings, "FFMPEG_DRESSING_SCALE", FFMPEG_DRESSING_SCALE
    )
    FFMPEG_DRESSING_CONCAT = getattr(
        settings, "FFMPEG_DRESSING_CONCAT", FFMPEG_DRESSING_CONCAT
    )
except ImportError:  # pragma: no cover
    pass


class Encoding_video:
    """Encoding video object."""

    id = 0
    video_file = ""
    duration = 0
    list_video_track = {}
    list_audio_track = {}
    list_subtitle_track = {}
    list_image_track = {}
    list_mp4_files = {}
    list_hls_files = {}
    list_mp3_files = {}
    list_m4a_files = {}
    list_thumbnail_files = {}
    list_overview_files = {}
    list_subtitle_files = {}
    encoding_log = {}
    output_dir = ""
    start = 0
    stop = 0
    error_encoding = False
    cutting_start = 0
    cutting_stop = 0
    dressing = None

    def __init__(self, id=0, video_file="", start=0, stop=0, dressing=None):
        """Initialize a new Encoding_video object."""
        self.id = id
        self.video_file = video_file
        self.duration = 0
        self.list_video_track = {}
        self.list_audio_track = {}
        self.list_subtitle_track = {}
        self.list_image_track = {}
        self.list_mp4_files = {}
        self.list_hls_files = {}
        self.list_mp3_files = {}
        self.list_m4a_files = {}
        self.list_thumbnail_files = {}
        self.list_overview_files = {}
        self.encoding_log = {}
        self.list_subtitle_files = {}
        self.output_dir = ""
        self.start = 0
        self.stop = 0
        self.error_encoding = False
        self.cutting_start = start or 0
        self.cutting_stop = stop or 0
        self.dressing = dressing or None

    def is_video(self):
        """Check if current encoding correspond to a video."""
        return len(self.list_video_track) > 0

    def get_subtime(self, clip_begin, clip_end):
        subtime = ""
        if clip_begin != 0 or clip_end != 0:
            subtime += "-ss %s " % str(clip_begin) + "-to %s " % str(clip_end)
        return subtime

    def get_video_data(self):
        """Get alls tracks from video source and put it in object passed in parameter."""
        msg = "--> get_info_video" + "\n"
        probe_cmd = FFPROBE_GET_INFO % {
            "ffprobe": FFPROBE_CMD,
            "select_streams": "",
            "source": '"' + self.video_file + '" ',
        }
        msg += probe_cmd + "\n"
        duration = 0
        info, return_msg = get_info_from_video(probe_cmd)
        msg += json.dumps(info, indent=2)
        msg += " \n"
        msg += return_msg + "\n"
        self.add_encoding_log("probe_cmd", probe_cmd, True, msg)
        try:
            duration = int(float("%s" % info["format"]["duration"]))
        except (RuntimeError, KeyError, AttributeError, ValueError, TypeError) as err:
            msg = "\nUnexpected error: {0}".format(err)
            self.add_encoding_log("duration", "", True, msg)
        if self.cutting_start != 0 or self.cutting_stop != 0:
            duration = self.cutting_stop - self.cutting_start
        self.duration = duration
        streams = info.get("streams", [])
        for stream in streams:
            self.add_stream(stream)

    def fix_duration(self, input_file):
        msg = "--> get_info_video" + "\n"
        probe_cmd = 'ffprobe -v quiet -show_entries format=duration -hide_banner  \
                    -of default=noprint_wrappers=1:nokey=1 -print_format json -i \
                    "{}"'.format(
            input_file
        )
        info, return_msg = get_info_from_video(probe_cmd)
        msg += json.dumps(info, indent=2)
        msg += " \n"
        msg += return_msg + "\n"
        duration = 0
        try:
            duration = int(float("%s" % info["format"]["duration"]))
        except (RuntimeError, KeyError, AttributeError, ValueError, TypeError) as err:
            msg += "\nUnexpected error: {0}".format(err)
        self.add_encoding_log("fix_duration", "", True, msg)
        if self.cutting_start != 0 or self.cutting_stop != 0:
            duration = self.cutting_stop - self.cutting_start
        self.duration = duration

    def add_stream(self, stream):
        codec_type = stream.get("codec_type", "unknown")
        # https://ffmpeg.org/doxygen/3.2/group__lavu__misc.html#ga9a84bba4713dfced21a1a56163be1f48
        if codec_type == "audio":
            codec = stream.get("codec_name", "unknown")
            self.list_audio_track["%s" % stream.get("index")] = {
                "sample_rate": stream.get("sample_rate", 0),
                "channels": stream.get("channels", 0),
            }
        if codec_type == "video":
            codec = stream.get("codec_name", "unknown")
            if any(ext in codec.lower() for ext in image_codec):
                self.list_image_track["%s" % stream.get("index")] = {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0),
                }
            else:
                self.list_video_track["%s" % stream.get("index")] = {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0),
                }
        if codec_type == "subtitle":
            codec = stream.get("codec_name", "unknown")
            language = ""
            if stream.get("tags"):
                language = stream.get("tags").get("language", "")
            self.list_subtitle_track["%s" % stream.get("index")] = {"language": language}

    def get_output_dir(self):
        dirname = os.path.dirname(self.video_file)
        return os.path.join(dirname, "%04d" % int(self.id))

    def create_output_dir(self):
        output_dir = self.get_output_dir()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = output_dir

    def get_mp4_command(self):
        mp4_command = "%s " % FFMPEG_CMD
        list_rendition = get_list_rendition()
        # remove rendition if encode_mp4 == False
        for rend in list_rendition.copy():
            if list_rendition[rend]["encode_mp4"] is False:
                list_rendition.pop(rend)
        if len(list_rendition) == 0:
            return ""
        first_item = list_rendition.popitem(last=False)
        mp4_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS,
        }
        output_file = os.path.join(self.output_dir, "%sp.mp4" % first_item[0])
        mp4_command += FFMPEG_MP4_ENCODE % {
            "cut": self.get_subtime(self.cutting_start, self.cutting_stop),
            "map_audio": "-map 0:a:0" if len(self.list_audio_track) > 0 else "",
            "libx": FFMPEG_LIBX,
            "height": first_item[0],
            "preset": FFMPEG_PRESET,
            "profile": FFMPEG_PROFILE,
            "level": FFMPEG_LEVEL,
            "crf": FFMPEG_CRF,
            "maxrate": first_item[1]["maxrate"],
            "bufsize": first_item[1]["maxrate"],
            "ba": first_item[1]["audio_bitrate"],
            "output": output_file,
        }
        self.list_mp4_files[first_item[0]] = output_file
        """
        il est possible de faire ainsi :
        mp4_command += FFMPEG_MP4_ENCODE.format(
            height=first_item[0],
            [...]
        )
        """
        in_height = list(self.list_video_track.items())[0][1]["height"]
        for rend in list_rendition:
            resolution_threshold = rend - rend * (
                list_rendition[rend]["encoding_resolution_threshold"] / 100
            )
            if in_height >= resolution_threshold:
                output_file = os.path.join(self.output_dir, "%sp.mp4" % rend)
                mp4_command += FFMPEG_MP4_ENCODE % {
                    "cut": self.get_subtime(self.cutting_start, self.cutting_stop),
                    "map_audio": "-map 0:a:0" if len(self.list_audio_track) > 0 else "",
                    "libx": FFMPEG_LIBX,
                    "height": min(rend, in_height),
                    "preset": FFMPEG_PRESET,
                    "profile": FFMPEG_PROFILE,
                    "level": FFMPEG_LEVEL,
                    "crf": FFMPEG_CRF,
                    "maxrate": list_rendition[rend]["maxrate"],
                    "bufsize": list_rendition[rend]["maxrate"],
                    "ba": list_rendition[rend]["audio_bitrate"],
                    "output": output_file,
                }
                self.list_mp4_files[rend] = output_file
        return mp4_command

    def get_hls_command(self):
        hls_command = "%s " % FFMPEG_CMD
        list_rendition = get_list_rendition()
        hls_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS,
        }
        hls_common_params = FFMPEG_HLS_COMMON_PARAMS % {
            "cut": self.get_subtime(self.cutting_start, self.cutting_stop),
            "libx": FFMPEG_LIBX,
            "preset": FFMPEG_PRESET,
            "profile": FFMPEG_PROFILE,
            "level": FFMPEG_LEVEL,
            "crf": FFMPEG_CRF,
        }
        hls_command += hls_common_params
        in_height = list(self.list_video_track.items())[0][1]["height"]
        for index, rend in enumerate(list_rendition):
            resolution_threshold = rend - rend * (
                list_rendition[rend]["encoding_resolution_threshold"] / 100
            )
            if in_height >= resolution_threshold or index == 0:
                output_file = os.path.join(self.output_dir, "%sp.m3u8" % rend)
                hls_command += hls_common_params
                hls_command += FFMPEG_HLS_ENCODE_PARAMS % {
                    "height": min(rend, in_height),
                    "maxrate": list_rendition[rend]["maxrate"],
                    "bufsize": list_rendition[rend]["maxrate"],
                    "ba": list_rendition[rend]["audio_bitrate"],
                    "hls_time": FFMPEG_HLS_TIME,
                    "output": output_file,
                }
                self.list_hls_files[rend] = output_file
        return hls_command

    def get_dressing_file(self):
        dirname = os.path.dirname(self.video_file)
        filename, ext = os.path.splitext(os.path.basename(self.video_file))
        output_file = os.path.join(dirname, filename + "_dressing" + ext)
        return output_file

    def get_dressing_command(self):
        height = str(list(self.list_video_track.items())[0][1]["height"])
        order_opening_credits = 0
        dressing_command_params = '[vid][0:a]'
        number_concat = 1
        dressing_command = "%s " % FFMPEG_CMD
        dressing_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS,
        }

        dressing_command += get_dressing_input(self.dressing, FFMPEG_DRESSING_INPUT)
        dressing_command_filter = []
        dressing_command_filter.append(FFMPEG_DRESSING_SCALE % {
            "number": "0",
            "height": height,
            "name": "vid",
        })
        if self.dressing.watermark:
            dressing_command_params = '[video][0:a]'
            order_opening_credits = order_opening_credits + 1
            dressing_command_filter.append(FFMPEG_DRESSING_WATERMARK % {
                "opacity": self.dressing.opacity / 100.0,
                "position": get_position_value(self.dressing.position, height)
            })
        if self.dressing.opening_credits:
            order_opening_credits = order_opening_credits + 1
            number_concat = number_concat + 1
            dressing_command_params = ('[debut][' + str(order_opening_credits)
                                       + ':a]' + dressing_command_params)
            dressing_command_filter.append(FFMPEG_DRESSING_SCALE % {
                "number": str(order_opening_credits),
                "height": height,
                "name": "debut",
            })
        if self.dressing.ending_credits:
            number_concat = number_concat + 1
            dressing_command_params = (dressing_command_params + '[fin]['
                                       + str(order_opening_credits + 1) + ':a]')
            dressing_command_filter.append(FFMPEG_DRESSING_SCALE % {
                "number": str(order_opening_credits + 1),
                "height": str(list(self.list_video_track.items())[0][1]["height"]),
                "name": "fin",
            })
        if self.dressing.opening_credits or self.dressing.ending_credits:
            dressing_command_filter.append(FFMPEG_DRESSING_CONCAT % {
                "params": dressing_command_params,
                "number": number_concat,
            })

        dressing_command += FFMPEG_DRESSING_FILTER_COMPLEX % {
            "filter": ';'.join(dressing_command_filter),
        }

        if self.dressing.opening_credits or self.dressing.ending_credits:
            dressing_command += " -map '[v]' -map '[a]' "

        output_file = self.get_dressing_file()
        dressing_command += FFMPEG_DRESSING_OUTPUT % {
            "output": output_file,
        }
        return dressing_command

    def encode_video_dressing(self):
        dressing_command = self.get_dressing_command()
        return_value, return_msg = launch_cmd(dressing_command)
        self.add_encoding_log("dressing_command", dressing_command, return_value,
                              return_msg)
        self.video_file = self.get_dressing_file()

    def encode_video_part(self):
        mp4_command = self.get_mp4_command()
        return_value, return_msg = launch_cmd(mp4_command)
        self.add_encoding_log("mp4_command", mp4_command, return_value, return_msg)
        if not return_value:
            self.error_encoding = True
        if self.duration == 0:
            list_rendition = get_list_rendition()
            first_item = list_rendition.popitem(last=False)
            self.fix_duration(self.list_mp4_files[first_item[0]])
        hls_command = self.get_hls_command()
        return_value, return_msg = launch_cmd(hls_command)
        if return_value:
            self.create_main_livestream()
        self.add_encoding_log("hls_command", hls_command, return_value, return_msg)

    def create_main_livestream(self):
        list_rendition = get_list_rendition()
        livestream_content = ""
        for index, rend in enumerate(list_rendition):
            rend_livestream = os.path.join(
                self.get_output_dir(), "livestream%s.m3u8" % rend
            )
            if os.path.exists(rend_livestream):
                with open(rend_livestream, "r") as file:
                    data = file.read()
                if index == 0:
                    livestream_content += data
                else:
                    livestream_content += "\n".join(data.split("\n")[2:])
                os.remove(rend_livestream)
        livestream_file = open(
            os.path.join(self.get_output_dir(), "livestream.m3u8"), "w"
        )
        livestream_file.write(livestream_content.replace("\n\n", "\n"))
        livestream_file.close()

    def get_mp3_command(self):
        mp3_command = "%s " % FFMPEG_CMD
        mp3_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS,
        }
        output_file = os.path.join(self.output_dir, "audio_%s.mp3" % FFMPEG_AUDIO_BITRATE)
        mp3_command += FFMPEG_MP3_ENCODE % {
            # "audio_bitrate": AUDIO_BITRATE,
            "cut": self.get_subtime(self.cutting_start, self.cutting_stop),
            "output": output_file,
        }
        self.list_mp3_files[FFMPEG_AUDIO_BITRATE] = output_file
        return mp3_command

    def get_m4a_command(self):
        m4a_command = "%s " % FFMPEG_CMD
        m4a_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS,
        }
        output_file = os.path.join(self.output_dir, "audio_%s.m4a" % FFMPEG_AUDIO_BITRATE)
        m4a_command += FFMPEG_M4A_ENCODE % {
            "cut": self.get_subtime(self.cutting_start, self.cutting_stop),
            "audio_bitrate": FFMPEG_AUDIO_BITRATE,
            "output": output_file,
        }
        self.list_m4a_files[FFMPEG_AUDIO_BITRATE] = output_file
        return m4a_command

    def encode_audio_part(self):
        mp3_command = self.get_mp3_command()
        return_value, return_msg = launch_cmd(mp3_command)
        self.add_encoding_log("mp3_command", mp3_command, return_value, return_msg)
        if self.duration == 0:
            new_k = list(self.list_mp3_files)[0]
            self.fix_duration(self.list_mp3_files[new_k])
        if not self.is_video():
            m4a_command = self.get_m4a_command()
            return_value, return_msg = launch_cmd(m4a_command)
            self.add_encoding_log("m4a_command", m4a_command, return_value, return_msg)

    def get_extract_thumbnail_command(self):
        thumbnail_command = "%s " % FFMPEG_CMD
        thumbnail_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS,
        }
        for img in self.list_image_track:
            output_file = os.path.join(self.output_dir, "thumbnail_%s.png" % img)
            thumbnail_command += FFMPEG_EXTRACT_THUMBNAIL % {
                "index": img,
                "output": output_file,
            }
            self.list_thumbnail_files[img] = output_file
        return thumbnail_command

    def get_create_thumbnail_command(self):
        thumbnail_command = "%s " % FFMPEG_CMD
        first_item = self.get_first_item()
        input_file = self.list_mp4_files[first_item[0]]
        thumbnail_command += FFMPEG_INPUT % {
            "input": input_file,
            "nb_threads": FFMPEG_NB_THREADS,
        }
        output_file = os.path.join(self.output_dir, "thumbnail")
        thumbnail_command += FFMPEG_CREATE_THUMBNAIL % {
            "duration": self.duration,
            "nb_thumbnail": FFMPEG_NB_THUMBNAIL,
            "output": output_file,
        }
        for nb in range(0, FFMPEG_NB_THUMBNAIL):
            num_thumb = str(nb + 1)
            self.list_thumbnail_files[num_thumb] = "%s_000%s.png" % (
                output_file,
                num_thumb,
            )
        return thumbnail_command

    def get_first_item(self):
        """get the first mp4 render from setting"""
        list_rendition = get_list_rendition()
        for rend in list_rendition.copy():
            if list_rendition[rend]["encode_mp4"] is False:
                list_rendition.pop(rend)
        if len(list_rendition) == 0:
            return None
        else:
            return list_rendition.popitem(last=False)

    def create_overview(self):
        first_item = self.get_first_item()
        # overview combine for 160x90
        in_height = list(self.list_video_track.items())[0][1]["height"]
        in_width = list(self.list_video_track.items())[0][1]["width"]
        image_height = 75  # decrease to 75 px instead of 90 due to montage overflow
        coef = in_height / image_height
        image_width = int(in_width / coef)
        input_file = self.list_mp4_files[first_item[0]]
        nb_img = 100
        step = 1
        if self.duration < 100:
            # nb_img = int(self.duration * 10 / 100)
            step = 10  # on ne fait que 10 images si la video dure moins de 100 sec.
        overviewimagefilename = os.path.join(self.output_dir, "overview.png")
        image_url = os.path.basename(overviewimagefilename)
        overviewfilename = os.path.join(self.output_dir, "overview.vtt")
        webvtt = WebVTT()
        for i in range(0, nb_img, step):
            # create overviewimagefilename for first pass
            output_file = (
                os.path.join(self.output_dir, "thumbnail_%s.png" % i)
                if i > 0
                else overviewimagefilename
            )
            cmd_ffmpegthumbnailer = (
                'ffmpegthumbnailer -t "%(stamp)s" '
                + '-s "%(image_width)s" -i %(source)s -c png '
                + "-o %(output_file)s "
            ) % {
                "stamp": str(i) + "%",
                "source": input_file,
                "output_file": output_file,
                "image_width": image_width,
            }
            return_value, return_msg = launch_cmd(cmd_ffmpegthumbnailer)
            # self.add_encoding_log(
            # "ffmpegthumbnailer_%s" % i, cmd_ffmpegthumbnailer, return_value, return_msg)
            if return_value and check_file(output_file) and i > 0:
                # print("MONTAGE")
                cmd_montage = (
                    "montage -geometry +0+0 %(overviewimagefilename)s \
                    %(output_file)s  %(overviewimagefilename)s"
                    % {
                        "overviewimagefilename": overviewimagefilename,
                        "output_file": output_file,
                    }
                )
                return_value, return_msg = launch_cmd(cmd_montage)
                if not return_value:
                    print("cmd_montage_%s" % i, cmd_montage, return_value, return_msg)
                # self.add_encoding_log
                # ("cmd_montage_%s" % i, cmd_montage, return_value, return_msg)
                os.remove(output_file)
            start = format(float(self.duration * i / 100), ".3f")
            end = format(float(self.duration * (i + step) / 100), ".3f")
            start_time = time.strftime(
                "%H:%M:%S", time.gmtime(int(str(start).split(".")[0]))
            )
            start_time += ".%s" % (str(start).split(".")[1])
            end_time = time.strftime(
                "%H:%M:%S", time.gmtime(int(str(end).split(".")[0]))
            ) + ".%s" % (str(end).split(".")[1])
            caption = Caption(
                "%s" % start_time,
                "%s" % end_time,
                "%s#xywh=%d,%d,%d,%d"
                % (image_url, image_width * (i / step), 0, image_width, image_height),
            )
            webvtt.captions.append(caption)
        webvtt.save(overviewfilename)
        if check_file(overviewfilename) and check_file(overviewimagefilename):
            self.list_overview_files["0"] = overviewimagefilename
            self.list_overview_files["1"] = overviewfilename
            # self.encoding_log += "\n- overviewfilename:\n%s" % overviewfilename
        else:
            self.add_encoding_log("create_overview", "", False, "")

    def encode_image_part(self):
        if len(self.list_image_track) > 0:
            thumbnail_command = self.get_extract_thumbnail_command()
            return_value, return_msg = launch_cmd(thumbnail_command)
            self.add_encoding_log(
                "extract_thumbnail_command", thumbnail_command, return_value, return_msg
            )
        elif self.is_video():
            thumbnail_command = self.get_create_thumbnail_command()
            return_value, return_msg = launch_cmd(thumbnail_command)
            self.add_encoding_log(
                "create_thumbnail_command", thumbnail_command, return_value, return_msg
            )
        # on ne fait pas d'overview pour les videos de moins de 10 secondes
        # (laisser les 10sec inclus pour laisser les tests passer) --> OK
        if self.is_video() and self.duration >= 10:
            self.create_overview()

    def get_extract_subtitle_command(self):
        subtitle_command = "%s " % FFMPEG_CMD
        subtitle_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS,
        }
        for sub in self.list_subtitle_track:
            lang = self.list_subtitle_track[sub]["language"]
            output_file = os.path.join(self.output_dir, "subtitle_%s.vtt" % lang)
            subtitle_command += FFMPEG_EXTRACT_SUBTITLE % {
                "index": sub,
                "output": output_file,
            }
            self.list_subtitle_files[sub] = [lang, output_file]
        return subtitle_command

    def get_subtitle_part(self):
        if len(self.list_subtitle_track) > 0:
            subtitle_command = self.get_extract_subtitle_command()
            return_value, return_msg = launch_cmd(subtitle_command)
            self.add_encoding_log(
                "subtitle_command", subtitle_command, return_value, return_msg
            )

    def export_to_json(self):
        data_to_dump = {}
        for attribute, value in self.__dict__.items():
            if attribute == 'dressing' and value is not None:
                data_to_dump[attribute] = value.to_json()
            else:
                data_to_dump[attribute] = value
        with open(self.output_dir + "/info_video.json", "w") as outfile:
            json.dump(data_to_dump, outfile, indent=2)

    def add_encoding_log(self, title, command, result, msg):
        self.encoding_log[title] = {"command": command, "result": result, "msg": msg}
        if result is False and self.error_encoding is False:
            self.error_encoding = True

    def start_encode(self):
        self.start = time.ctime()
        self.create_output_dir()
        self.get_video_data()
        if self.dressing is not None:
            self.encode_video_dressing()
        print(self.id, self.video_file, self.duration)
        if self.is_video():
            self.encode_video_part()
        if len(self.list_audio_track) > 0:
            self.encode_audio_part()
        self.encode_image_part()
        if len(self.list_subtitle_track) > 0:
            self.get_subtitle_part()
        self.stop = time.ctime()
        self.export_to_json()


def fix_input(input):
    filename = ""
    if args.input.startswith("/"):
        path_file = args.input
    else:
        path_file = os.path.join(os.getcwd(), args.input)
    if os.access(path_file, os.F_OK) and os.stat(path_file).st_size > 0:
        # remove accent and space
        filename = "".join(
            (
                c
                for c in unicodedata.normalize("NFD", path_file)
                if unicodedata.category(c) != "Mn"
            )
        )
        filename = filename.replace(" ", "_")
        os.rename(
            path_file,
            filename,
        )
        print("Encoding file {} \n".format(filename))
    return filename


"""
  remote encode ???
"""
if __name__ == "__main__":
    start = "Start at: %s" % time.ctime()
    parser = argparse.ArgumentParser(description="Running encoding video.")
    parser.add_argument("--id", required=True, help="the ID of the video")
    parser.add_argument("--start", required=False, help="Start cut")
    parser.add_argument("--stop", required=False, help="Stop cut")
    parser.add_argument("--input", required=True, help="name of input file to encode")
    parser.add_argument("--dressing", required=False, help="Dressing for the video")

    args = parser.parse_args()
    print(args.start)
    filename = fix_input(args.input)
    encoding_video = Encoding_video(args.id, filename, args.start, args.stop,
                                    args.dressing)
    # error if uncommented
    # encoding_video.encoding_log += start
    # AttributeError: 'NoneType' object has no attribute 'get'
    encoding_video.start_encode()
