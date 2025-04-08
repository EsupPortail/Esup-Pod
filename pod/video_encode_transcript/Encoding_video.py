"""Esup-Pod video encoding."""

import argparse
import json
import logging
import os
import time
import unicodedata
from webvtt import WebVTT, Caption

if __name__ == "__main__":
    from encoding_utils import (
        get_dressing_position_value,
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
        FFMPEG_CREATE_OVERVIEW,
        FFMPEG_EXTRACT_SUBTITLE,
        FFMPEG_DRESSING_INPUT,
        FFMPEG_DRESSING_OUTPUT,
        FFMPEG_DRESSING_WATERMARK,
        FFMPEG_DRESSING_FILTER_COMPLEX,
        FFMPEG_DRESSING_SCALE,
        FFMPEG_DRESSING_CONCAT,
        FFMPEG_DRESSING_SILENT,
        FFMPEG_DRESSING_AUDIO,
    )
else:
    from .encoding_utils import (
        get_dressing_position_value,
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
        FFMPEG_CREATE_OVERVIEW,
        FFMPEG_EXTRACT_SUBTITLE,
        FFMPEG_DRESSING_INPUT,
        FFMPEG_DRESSING_OUTPUT,
        FFMPEG_DRESSING_WATERMARK,
        FFMPEG_DRESSING_FILTER_COMPLEX,
        FFMPEG_DRESSING_SCALE,
        FFMPEG_DRESSING_CONCAT,
        FFMPEG_DRESSING_SILENT,
        FFMPEG_DRESSING_AUDIO,
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
    FFMPEG_DRESSING_SILENT = getattr(
        settings, "FFMPEG_DRESSING_SILENT", FFMPEG_DRESSING_SILENT
    )
    FFMPEG_DRESSING_AUDIO = getattr(
        settings, "FFMPEG_DRESSING_AUDIO", FFMPEG_DRESSING_AUDIO
    )
    DEBUG = getattr(settings, "DEBUG", True)
except ImportError:  # pragma: no cover
    DEBUG = True
    pass

logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)


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
    json_dressing = None
    dressing_input = ""

    def __init__(
        self, id=0, video_file="", start=0, stop=0, json_dressing=None, dressing_input=""
    ) -> None:
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
        self.json_dressing = json_dressing
        self.dressing_input = dressing_input

    def is_video(self) -> bool:
        """Check if current encoding correspond to a video."""
        return len(self.list_video_track) > 0

    def get_subtime(self, clip_begin, clip_end) -> str:
        subtime = ""
        if clip_begin != 0 or clip_end != 0:
            subtime += "-ss %s " % str(clip_begin) + "-to %s " % str(clip_end)
        return subtime

    def get_video_data(self) -> None:
        """Get alls tracks from video source and put it in object passed in parameter."""
        msg = "--> get_info_video\n"
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

    def fix_duration(self, input_file) -> None:
        msg = "--> get_info_video\n"
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

    def get_output_dir(self) -> str:
        dirname = os.path.dirname(self.video_file)
        return os.path.join(dirname, "%04d" % int(self.id))

    def create_output_dir(self) -> None:
        output_dir = self.get_output_dir()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = output_dir

    def get_mp4_command(self) -> str:
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

    def get_hls_command(self) -> str:
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

    def get_dressing_file(self) -> str:
        """Create or replace the dressed video file."""
        dirname = os.path.dirname(self.video_file)
        filename, ext = os.path.splitext(os.path.basename(self.video_file))
        output_file = os.path.join(dirname, filename + "_dressing" + ext)
        return output_file

    def get_dressing_command(self) -> str:
        """
        Generate the FFMPEG command based on the dressing object parameters.

        Returns:
            A string representing the complete FFMPEG command.
        """
        height = str(list(self.list_video_track.items())[0][1]["height"])
        dressing_command = f"{FFMPEG_CMD} "
        dressing_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS,
        }

        dressing_command += self.dressing_input

        # Handle opening and ending credits
        dressing_command += self.handle_dressing_credits()

        # Apply filters
        dressing_command_filter, dressing_command_params = self.build_dressing_filters(
            height
        )

        dressing_command += FFMPEG_DRESSING_FILTER_COMPLEX % {
            "filter": ";".join(dressing_command_filter),
        }

        if self.json_dressing.get("opening_credits") or self.json_dressing.get(
            "ending_credits"
        ):
            dressing_command += " -map '[v]' -map '[a]' "

        output_file = self.get_dressing_file()
        dressing_command += FFMPEG_DRESSING_OUTPUT % {"output": output_file}

        return dressing_command

    def handle_dressing_credits(self) -> str:
        """
        Handle the addition of opening and ending credits to the command.

        Returns:
            A string with the FFMPEG commands for silent credits if required.
        """
        command = ""
        for credit_type in ["opening_credits", "ending_credits"]:
            if self.json_dressing.get(credit_type):
                has_audio_key = f"{credit_type}_video_hasaudio"
                duration_key = f"{credit_type}_video_duration"

                if not self.json_dressing.get(has_audio_key, True):
                    duration = self.json_dressing.get(duration_key)

                    try:
                        duration = int(duration) if duration and int(duration) > 0 else 1
                    except (ValueError, TypeError):
                        duration = 1

                    command += FFMPEG_DRESSING_SILENT % {"duration": duration}

        return command

    def build_dressing_filters(self, height: str):
        """
        Build the filters for video processing.

        Args:
            height: The height of the video for scaling purposes.

        Returns:
            A tuple containing the list of filters and the filter parameters.
        """
        filters = []
        params = ""
        order = 0
        interval_silent = 0
        concat_number = 1

        # Base video track
        filters.append(
            FFMPEG_DRESSING_SCALE % {"number": "0", "height": height, "name": "vid"}
        )
        params = "[vid][0:a]"
        order = order + 1

        # Watermark if present
        if self.json_dressing.get("watermark"):
            filters.append(self.apply_dressing_watermark(height))
            params = "[video][0:a]"
            order = order + 1

        interval_silent = order
        # Opening credits
        if self.json_dressing.get("opening_credits"):
            if self.json_dressing.get("ending_credits"):
                interval_silent = interval_silent + 1
            filters, params, interval_silent = self.add_dressing_credits(
                filters,
                params,
                height,
                "opening_credits",
                "debut",
                order,
                interval_silent,
            )
            order = order + 1
            concat_number = concat_number + 1

        # Ending credits
        if self.json_dressing.get("ending_credits"):
            filters, params, interval_silent = self.add_dressing_credits(
                filters, params, height, "ending_credits", "fin", order, interval_silent
            )
            concat_number = concat_number + 1

        # Concatenate if needed
        if self.json_dressing.get("opening_credits") or self.json_dressing.get(
            "ending_credits"
        ):
            filters.append(
                FFMPEG_DRESSING_CONCAT % {"params": params, "number": concat_number}
            )

        return filters, params

    def apply_dressing_watermark(self, height: str) -> str:
        """
        Apply the watermark to the video.

        Args:
            height: The height of the video to position the watermark correctly.

        Returns:
            A string representing the FFMPEG command for applying the watermark.
        """
        opacity = self.json_dressing["opacity"] / 100.0
        position = get_dressing_position_value(
            self.json_dressing["position_orig"], height
        )
        name_out = (
            "[video]"
            if self.json_dressing.get("opening_credits")
            or self.json_dressing.get("ending_credits")
            else ""
        )

        return FFMPEG_DRESSING_WATERMARK % {
            "opacity": opacity,
            "position": position,
            "name_out": name_out,
        }

    def add_dressing_credits(
        self,
        filters: list,
        params: str,
        height: str,
        credit_type: str,
        name: str,
        order: str,
        interval_silent: str,
    ):
        """
        Add opening or ending credits to the FFmpeg command by updating the filters and parameters.

        Args:
            filters (list): A list of existing FFmpeg filters to which new filters will be appended.
            params (str): The current filter parameters string that will be updated to include the credits.
            height (str): The height of the video used for scaling the credit overlay.
            credit_type (str): Specifies the type of credits to add, either 'opening_credits' or 'ending_credits'.
            name (str): The identifier for the credit video or overlay to be used in the FFmpeg filter graph.
            order (str): The position identifier for the audio stream, used to sync audio with the credits.
            interval_silent (str): Counter indicating the number of silent audio intervals inserted, used when adding silent audio tracks.

        Returns:
            tuple:
                - Updated list of filters with the added credit filters.
                - Updated filter parameter string reflecting the new credit positioning.
                - Updated interval_silent value if a silent audio track was added.
        """
        audio_out = f"{order}:a"

        if not self.json_dressing.get(f"{credit_type}_video_hasaudio"):
            audio_out = f"a{order}"
            filters.append(
                FFMPEG_DRESSING_AUDIO
                % {
                    "param_in": f"{interval_silent + 1}:a",
                    "param_out": audio_out,
                }
            )
            interval_silent = interval_silent + 1

        if credit_type == "opening_credits":
            params = f"[{name}][{audio_out}]{params}"
        else:
            params = f"{params}[{name}][{audio_out}]"

        filters.append(
            FFMPEG_DRESSING_SCALE % {"number": str(order), "height": height, "name": name}
        )

        return filters, params, interval_silent

    def encode_video_dressing(self) -> None:
        """Encode the dressed video."""
        dressing_command = self.get_dressing_command()
        return_value, return_msg = launch_cmd(dressing_command)
        self.add_encoding_log(
            "dressing_command", dressing_command, return_value, return_msg
        )
        self.video_file = self.get_dressing_file()

    def encode_video_part(self) -> None:
        """Encode the video part of a file."""
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

    def create_main_livestream(self) -> None:
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

    def get_mp3_command(self) -> str:
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

    def get_m4a_command(self) -> str:
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

    def encode_audio_part(self) -> None:
        """Encode the audio part of a video."""
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

    def get_extract_thumbnail_command(self) -> str:
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

    def get_create_thumbnail_command(self) -> str:
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
        """Get the first mp4 render from setting."""
        list_rendition = get_list_rendition()
        for rend in list_rendition.copy():
            if list_rendition[rend]["encode_mp4"] is False:
                list_rendition.pop(rend)
        if len(list_rendition) == 0:
            return None
        else:
            return list_rendition.popitem(last=False)

    def create_overview(self) -> None:
        first_item = self.get_first_item()
        # overview combine for 160x90
        in_height = list(self.list_video_track.items())[0][1]["height"]
        in_width = list(self.list_video_track.items())[0][1]["width"]
        image_height = 90
        coef = in_height / image_height
        image_width = int(in_width / coef)
        input_file = self.list_mp4_files[first_item[0]]
        nb_img = 100 if self.duration >= 100 else 10

        overviewimagefilename = os.path.join(self.output_dir, "overview.png")
        overview_image_command = (
            FFMPEG_CMD
            + " "
            + FFMPEG_INPUT
            % {
                "input": input_file,
                "nb_threads": FFMPEG_NB_THREADS,
            }
            + FFMPEG_CREATE_OVERVIEW
            % {
                "duration": self.duration,
                "image_count": nb_img,
                "width": image_width,
                "height": image_height,
                "output": overviewimagefilename,
            }
        )
        return_value, output_message = launch_cmd(overview_image_command)
        if not return_value or not check_file(overviewimagefilename):
            logger.error(f"FFmpeg failed with output: {output_message}")

        overviewfilename = os.path.join(self.output_dir, "overview.vtt")
        image_url = os.path.basename(overviewimagefilename)
        webvtt = WebVTT()
        for i in range(0, nb_img):
            start = format(float(self.duration * i / nb_img), ".3f")
            end = format(float(self.duration * (i + 1) / nb_img), ".3f")
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
                % (image_url, image_width * i, 0, image_width, image_height),
            )
            webvtt.captions.append(caption)
        webvtt.save(overviewfilename)
        if check_file(overviewfilename) and check_file(overviewimagefilename):
            self.list_overview_files["0"] = overviewimagefilename
            self.list_overview_files["1"] = overviewfilename
            # self.encoding_log += "\n- overviewfilename:\n%s" % overviewfilename
        else:
            self.add_encoding_log("create_overview", "", False, "")

    def encode_image_part(self) -> None:
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

    def get_extract_subtitle_command(self) -> str:
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

    def get_subtitle_part(self) -> None:
        if len(self.list_subtitle_track) > 0:
            subtitle_command = self.get_extract_subtitle_command()
            return_value, return_msg = launch_cmd(subtitle_command)
            self.add_encoding_log(
                "subtitle_command", subtitle_command, return_value, return_msg
            )

    def export_to_json(self) -> None:
        data_to_dump = {}
        for attribute, value in self.__dict__.items():
            data_to_dump[attribute] = value
        with open(self.output_dir + "/info_video.json", "w") as outfile:
            json.dump(data_to_dump, outfile, indent=2)

    def add_encoding_log(self, title, command, result, msg) -> None:
        """Add Encoding step to the encoding_log dict."""
        self.encoding_log[title] = {"command": command, "result": result, "msg": msg}
        if result is False and self.error_encoding is False:
            self.error_encoding = True

    def start_encode(self) -> None:
        self.start = time.ctime()
        self.create_output_dir()
        self.get_video_data()
        if self.json_dressing is not None:
            self.encode_video_dressing()
        logger.info(
            "start_encode {id: %s, file: %s, duration: %s}"
            % (self.id, self.video_file, self.duration)
        )
        if self.is_video():
            logger.debug("* encode_video_part")
            self.encode_video_part()
        if len(self.list_audio_track) > 0:
            logger.debug("* encode_audio_part")
            self.encode_audio_part()
        logger.debug("* encode_image_part")
        self.encode_image_part()
        if len(self.list_subtitle_track) > 0:
            logger.debug("* get_subtitle_part")
            self.get_subtitle_part()
        self.stop = time.ctime()
        self.export_to_json()


def fix_input(input) -> str:
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
        logger.info("Encoding file {} \n".format(filename))
    return filename


"""
  remote encode???
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
    logger.debug(args.start)
    filename = fix_input(args.input)
    encoding_video = Encoding_video(
        args.id, filename, args.start, args.stop, args.dressing
    )
    # error if uncommented
    # encoding_video.encoding_log += start
    # AttributeError: 'NoneType' object has no attribute 'get'
    encoding_video.start_encode()
