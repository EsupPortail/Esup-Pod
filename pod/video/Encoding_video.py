from __future__ import absolute_import, division, print_function
import json
import os
import argparse
import time
from encoding_utils import (
    get_info_from_video,
    get_list_rendition,
    launch_cmd,
)

# from unidecode import unidecode # third party package to remove accent
# import unicodedata

__author__ = "Nicolas CAN <nicolas.can@univ-lille.fr>"
__license__ = "LGPL v3"

image_codec = ["jpeg", "gif", "png", "bmp", "jpg"]

"""
 - Get video source
 - get alls track from video source
 - encode tracks in HLS and mp4
 - save it
"""
# https://trac.ffmpeg.org/wiki/Encode/H.264
FFMPEG_CMD = "ffmpeg"
FFMPEG_CRF = 20  # -crf 20 -maxrate 3M -bufsize 6M
FFMPEG_PRESET = "slow"
FFMPEG_PROFILE = "high"
FFMPEG_LEVEL = 3
FFMPEG_HLS_TIME = 2
# ffmpeg -hide_banner -i test5.mkv \
# -c:v libx264  -vf "scale=-2:360" -preset slow -profile:v high -pix_fmt yuv420p -level 3 -crf 20 -maxrate 1M -bufsize 2M -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -c:a aac -ar 48000 -b:a 96k -movflags faststart  -y -vsync 0 360p.mp4 \
# -c:v libx264  -vf "scale=-2:720" -preset slow -profile:v high -pix_fmt yuv420p -level 3 -crf 20 -maxrate 3M -bufsize 6M -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -c:a aac -ar 48000 -b:a 128k -movflags faststart  -y -vsync 0 720p.mp4 \
# -c:v libx264  -vf "scale=-2:1080" -preset slow -profile:v high -pix_fmt yuv420p -level 3 -crf 20 -maxrate 4M -bufsize 8M -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -c:a aac -ar 48000 -b:a 192k -movflags faststart  -y -vsync 0 1080p.mp4


FFMPEG_INPUT = "-hide_banner -threads %(nb_threads)s -i %(input)s "
FFMPEG_LIBX = "libx264"
FFMPEG_MP4_ENCODE = (
    '-c:v %(libx)s  -vf "scale=-2:%(height)s" -preset %(preset)s -profile:v %(profile)s '
    + '-pix_fmt yuv420p -level %(level)s -crf %(crf)s -maxrate %(maxrate)s -bufsize %(bufsize)s '
    + '-sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 '
    + '-c:a aac -ar 48000 -b:a %(ba)s -movflags faststart  -y -vsync 0 "%(output)s" '
)
# https://gist.github.com/Andrey2G/78d42b5c87850f8fbadd0b670b0e6924
FFMPEG_HLS_ENCODE = (
    "-map 0:v:0 -map 0:a:0 -c:v %(libx)s  "
    + '-vf "scale=-2:%(height)s" -preset %(preset)s -profile:v %(profile)s '
    + '-pix_fmt yuv420p -level %(level)s -crf %(crf)s -maxrate %(maxrate)s -bufsize %(bufsize)s '
    + '-sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 '
    + '-c:a aac -ar 48000 -b:a %(ba)s -hls_playlist_type vod -hls_time %(hls_time)s -hls_flags single_file '
    + '-master_pl_name "livestream.m3u8" -y -vsync 0 "%(output)s" '
)
FFMPEG_MP3_ENCODE = (
    '-vn -b:a %(audio_bitrate)s -vn -f mp3 "%(output)s" '
)
FFMPEG_M4A_ENCODE = (
    '-vn -c:a aac -b:a %(audio_bitrate)s "%(output)s" '
)
FFMPEG_NB_THREADS = 0
AUDIO_BITRATE = "192k"


class Encoding_video:
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
    encoding_log = ""
    output_dir = ""
    start = 0
    stop = 0
    error_encoding = False

    def __init__(self, id, video_file):
        self.id = id
        self.video_file = video_file
        self.encoding_log = ""

    def is_video(self):
        return len(self.list_video_track) > 0

    def get_video_data(self):
        """
        get alls tracks from video source and put it in object passed in parameter
        """
        msg = "--> get_info_video" + "\n"
        probe_cmd = "ffprobe -v quiet -show_format -show_streams \
                    -print_format json -i {}".format(
            self.video_file
        )
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
        self.duration = duration
        streams = info.get("streams", [])
        for stream in streams:
            self.add_stream(stream)
        self.encoding_log += msg

    def add_stream(self, stream):
        codec_type = stream.get("codec_type", "unknown")
        # https://ffmpeg.org/doxygen/3.2/group__lavu__misc.html#ga9a84bba4713dfced21a1a56163be1f48
        if codec_type == "audio":
            codec = stream.get("codec_name", "unknown")
            print(codec)
            self.list_audio_track["%s" % stream.get("index")] = {
                "sample_rate": stream.get("sample_rate", 0),
                "channels": stream.get("channels", 0),
            }
        if codec_type == "video":
            codec = stream.get("codec_name", "unknown")
            print(codec)
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
            print(codec)
            language = stream.get("language", stream.get("language", ""))
            self.list_subtitle_track["%s" % stream.get("index")] = {
                "language": language
            }

    def create_output_dir(self):
        dirname = os.path.dirname(self.video_file)
        output_dir = os.path.join(dirname, "%04d" % self.id)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = output_dir

    def get_mp4_command(self):
        mp4_command = "%s " % FFMPEG_CMD
        list_rendition = get_list_rendition()
        first_item = list_rendition.popitem(last=False)
        mp4_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        output_file = os.path.join(self.output_dir, "%sp.mp4" % first_item[0])
        mp4_command += FFMPEG_MP4_ENCODE % {
            "libx": FFMPEG_LIBX,
            "height": first_item[0],
            "preset": FFMPEG_PRESET,
            "profile": FFMPEG_PROFILE,
            "level": FFMPEG_LEVEL,
            "crf": FFMPEG_CRF,
            "maxrate": first_item[1]["maxrate"],
            "bufsize": first_item[1]["maxrate"],
            "ba": first_item[1]["audio_bitrate"],
            "output": output_file
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
            if in_height >= rend:
                output_file = os.path.join(self.output_dir, "%sp.mp4" % rend)
                mp4_command += FFMPEG_MP4_ENCODE % {
                    "libx": FFMPEG_LIBX,
                    "height": rend,
                    "preset": FFMPEG_PRESET,
                    "profile": FFMPEG_PROFILE,
                    "level": FFMPEG_LEVEL,
                    "crf": FFMPEG_CRF,
                    "maxrate": list_rendition[rend]["maxrate"],
                    "bufsize": list_rendition[rend]["maxrate"],
                    "ba": list_rendition[rend]["audio_bitrate"],
                    "output": output_file
                }
                self.list_mp4_files[first_item[0]] = output_file
        return mp4_command

    def get_hls_command(self):
        hls_command = "%s " % FFMPEG_CMD
        list_rendition = get_list_rendition()
        first_item = list_rendition.popitem(last=False)
        hls_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        output_file = os.path.join(self.output_dir, "%sp.m3u8" % first_item[0])
        hls_command += FFMPEG_HLS_ENCODE % {
            "libx": FFMPEG_LIBX,
            "height": first_item[0],
            "preset": FFMPEG_PRESET,
            "profile": FFMPEG_PROFILE,
            "level": FFMPEG_LEVEL,
            "crf": FFMPEG_CRF,
            "maxrate": first_item[1]["maxrate"],
            "bufsize": first_item[1]["maxrate"],
            "ba": first_item[1]["audio_bitrate"],
            "hls_time": FFMPEG_HLS_TIME,
            "output": output_file
        }
        self.list_hls_files[first_item[0]] = output_file
        in_height = list(self.list_video_track.items())[0][1]["height"]
        for rend in list_rendition:
            if in_height >= rend:
                output_file = os.path.join(self.output_dir, "%sp.m3u8" % rend)
                hls_command += FFMPEG_HLS_ENCODE % {
                    "libx": FFMPEG_LIBX,
                    "height": rend,
                    "preset": FFMPEG_PRESET,
                    "profile": FFMPEG_PROFILE,
                    "level": FFMPEG_LEVEL,
                    "crf": FFMPEG_CRF,
                    "maxrate": list_rendition[rend]["maxrate"],
                    "bufsize": list_rendition[rend]["maxrate"],
                    "ba": list_rendition[rend]["audio_bitrate"],
                    "hls_time": FFMPEG_HLS_TIME,
                    "output": output_file
                }
                self.list_hls_files[first_item[0]] = output_file
        return hls_command

    def encode_video_part(self):
        mp4_command = self.get_mp4_command()
        print("mp4_command : %s" % mp4_command)
        return_value, return_msg = launch_cmd(mp4_command)
        self.encoding_log += return_msg
        if not return_value:
            self.error_encoding = True
        hls_command = self.get_hls_command()
        print("hls_command : %s" % hls_command)
        return_value, return_msg = launch_cmd(hls_command)
        self.encoding_log += return_msg
        if not return_value:
            self.error_encoding = True

    def get_mp3_command(self):
        mp3_command = "%s " % FFMPEG_CMD
        mp3_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        output_file = os.path.join(self.output_dir, "audio_%s.mp3" % AUDIO_BITRATE)
        mp3_command += FFMPEG_MP3_ENCODE % {
            "output": output_file,
        }
        self.list_mp3_files[AUDIO_BITRATE] = output_file
        return mp3_command

    def get_m4a_command(self):
        m4a_command = "%s " % FFMPEG_CMD
        m4a_command += FFMPEG_INPUT % {
            "input": self.video_file,
            "nb_threads": FFMPEG_NB_THREADS
        }
        output_file = os.path.join(self.output_dir, "audio_%s.m4a" % AUDIO_BITRATE)
        m4a_command += FFMPEG_MP3_ENCODE % {
            "output": output_file,
        }
        self.list_m4a_files[AUDIO_BITRATE] = output_file
        return m4a_command

    def encode_audio_part(self):
        mp3_command = self.get_mp3_command()
        print("mp3_command : %s" % mp3_command)
        return_value, return_msg = launch_cmd(mp3_command)
        self.encoding_log += return_msg
        print("To improve...")
        if not return_value:
            self.error_encoding = True
        if not encoding_video.is_video():
            m4a_command = self.get_m4a_command()
            print("m4a_command : %s" % m4a_command)
            return_value, return_msg = launch_cmd(m4a_command)
            self.encoding_log += return_msg


"""
  remote encode ???
"""
if __name__ == "__main__":
    start = "Start at: %s" % time.ctime()
    parser = argparse.ArgumentParser(description="Running encoding video.")
    parser.add_argument("--id", required=True, help="the ID of the video")
    parser.add_argument(
        "--input", required=True, help="name of input file to encode"
    )
    args = parser.parse_args()
    encoding_video = Encoding_video(args.id, args.input)
    encoding_video.encoding_log += start
    encoding_video.get_video_data()
    print(
        encoding_video.id, encoding_video.video_file, encoding_video.duration
    )
    if encoding_video.is_video():
        encoding_video.encode_video_part()

    if len(encoding_video.list_audio_track) > 0:
        encoding_video.encode_audio_part()

    if len(encoding_video.list_image_track) > 0:
        print("save image track")
    if len(encoding_video.list_subtitle_track) > 0:
        print("save subrip files")
