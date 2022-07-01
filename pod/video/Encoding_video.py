from __future__ import absolute_import, division, print_function
import json
import os
import argparse
import time
from encoding_utils import get_info_from_video, get_list_rendition  # launch_cmd

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


FFMPEG_INPUT = "-hide_banner -i %(input)s "
FFMPEG_MP4_ENCODE = (
    "-c:v libx264  -vf \"scale=-2:%(height)s\" -preset %(preset)s -profile:v %(profile)s "
    + "-pix_fmt yuv420p -level %(level)s -crf %(crf)s -maxrate %(maxrate)s -bufsize %(bufsize)s "
    + "-sc_threshold 0 -force_key_frames \"expr:gte(t,n_forced*1)\" -max_muxing_queue_size 4000 "
    + "-c:a aac -ar 48000 -b:a %(ba)s -movflags faststart  -y -vsync 0 %(height)sp.mp4 ")
FFMPEG_HLS_ENCODE = (
    "-c:v libx264  -vf \"scale=-2:%(height)s\" -preset %(preset)s -profile:v %(profile)s "
    + "-pix_fmt yuv420p -level %(level)s -crf %(crf)s -maxrate %(maxrate)s -bufsize %(bufsize)s "
    + "-sc_threshold 0 -force_key_frames \"expr:gte(t,n_forced*1)\" -max_muxing_queue_size 4000 "
    + "-c:a aac -ar 48000 -b:a %(ba)s -hls_playlist_type vod -hls_time %(hls_time)s -hls_flags single_file "
    + "-master_pl_name \"livestream.m3u8\" -y -vsync 0 %(height)sp.m3u8 ")


class Encoding_video():
    id = 0
    video_file = ""
    duration = 0
    list_video_track = {}
    list_audio_track = {}
    list_subtitle_track = {}
    list_image_track = {}
    encoding_log = ""
    output_dir = ""
    start = 0
    stop = 0

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
                    -print_format json -i {}".format(self.video_file)
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
                    "height": stream.get("height", 0)
                }
            else:
                self.list_video_track["%s" % stream.get("index")] = {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0)
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
        mp4_command += FFMPEG_INPUT % {"input" : self.video_file}
        mp4_command += FFMPEG_MP4_ENCODE % {
            "height" : first_item[0],
            "preset": FFMPEG_PRESET,
            "profile": FFMPEG_PROFILE,
            "level": FFMPEG_LEVEL,
            "crf": FFMPEG_CRF,
            "maxrate": first_item[1]["maxrate"],
            "bufsize": first_item[1]["maxrate"],
            "ba": first_item[1]["audio_bitrate"]
        }
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
                mp4_command += FFMPEG_MP4_ENCODE % {
                    "height" : rend,
                    "preset": FFMPEG_PRESET,
                    "profile": FFMPEG_PROFILE,
                    "level": FFMPEG_LEVEL,
                    "crf": FFMPEG_CRF,
                    "maxrate": list_rendition[rend]["maxrate"],
                    "bufsize": list_rendition[rend]["maxrate"],
                    "ba": list_rendition[rend]["audio_bitrate"]
                }
        return mp4_command

    def get_hls_command(self):
        hls_command = "%s " % FFMPEG_CMD
        list_rendition = get_list_rendition()
        first_item = list_rendition.popitem(last=False)
        print("attention, il faut préciser dans la commande le fait qu'on ne prend que le flux audio et video !!!")
        hls_command += FFMPEG_INPUT % {"input" : self.video_file}
        hls_command += FFMPEG_HLS_ENCODE % {
            "height" : first_item[0],
            "preset": FFMPEG_PRESET,
            "profile": FFMPEG_PROFILE,
            "level": FFMPEG_LEVEL,
            "crf": FFMPEG_CRF,
            "maxrate": first_item[1]["maxrate"],
            "bufsize": first_item[1]["maxrate"],
            "ba": first_item[1]["audio_bitrate"],
            "hls_time": FFMPEG_HLS_TIME
        }
        in_height = list(self.list_video_track.items())[0][1]["height"]
        for rend in list_rendition:
            if in_height >= rend:
                hls_command += FFMPEG_HLS_ENCODE % {
                    "height" : rend,
                    "preset": FFMPEG_PRESET,
                    "profile": FFMPEG_PROFILE,
                    "level": FFMPEG_LEVEL,
                    "crf": FFMPEG_CRF,
                    "maxrate": list_rendition[rend]["maxrate"],
                    "bufsize": list_rendition[rend]["maxrate"],
                    "ba": list_rendition[rend]["audio_bitrate"],
                    "hls_time": FFMPEG_HLS_TIME
                }
        return hls_command


"""
  remote encode ???
"""
if __name__ == "__main__":
    start = "Start at: %s" % time.ctime()
    parser = argparse.ArgumentParser(description="Running encoding video.")
    parser.add_argument("--id", required=True, help="the ID of the video")
    parser.add_argument("--input", required=True, help="name of input file to encode")
    args = parser.parse_args()
    encoding_video = Encoding_video(args.id, args.input)
    encoding_video.encoding_log += start
    encoding_video.get_video_data()
    print(encoding_video.id, encoding_video.video_file, encoding_video.duration)
    # print(encoding_video.list_video_track)
    # print(encoding_video.list_audio_track)
    # print(encoding_video.list_subtitle_track)
    # print(encoding_video.list_image_track)
    # print(encoding_video.encoding_log)
    if encoding_video.is_video():
        mp4_command = encoding_video.get_mp4_command()
        print(mp4_command)
        # return_value, return_msg = launch_cmd(mp4_command)
        # encoding_video.encoding_log += return_msg
        print("TODO encode HLS")
        hls_command = encoding_video.get_hls_command()
        print('hls_command : %s' % hls_command)
        # if len(encoding_video.list_image_track) == 0 :
        #     print("create and save thumbnails")
    if len(encoding_video.list_audio_track) > 0 :
        if not encoding_video.is_video():
            print("TODO encode M4V")
        print("TODO encode MP3")
    if len(encoding_video.list_image_track) > 0 :
        print("save image track")
    if len(encoding_video.list_subtitle_track) > 0 :
        print("save subrip files")
