from __future__ import absolute_import, division, print_function
import json
import os
import argparse
import time

# from unidecode import unidecode # third party package to remove accent
# import unicodedata

__author__ = "Nicolas CAN <nicolas.can@univ-lille.fr>"
__license__ = "LGPL v3"

from encoding_utils import get_info_from_video

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
FFMPEG_PRESET = "medium"
FFMPEG_PROFILE = "baseline"
FFMPEG_LEVEL = 3


class Encoding_video():
    id = 0
    video_file = ""
    duration = 0
    list_video_track = []
    list_audio_track = []
    list_subtitle_track = []
    list_image_track = []
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
            self.list_audio_track[stream.get("index")] = {
                "sample_rate": stream.get("sample_rate", 0),
                "channels": stream.get("channels", 0),
            }
        if codec_type == "video":
            codec = stream.get("codec_name", "unknown")
            if any(ext in codec.lower() for ext in image_codec):
                self.list_image_track[stream.get("index")] = {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0)
                }
            else:
                print(stream)
                self.list_video_track[stream.get("index")] = {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0)
                }
        if codec_type == "subtitle":
            self.list_subtitle_track[stream.get("index")] = {}

    def create_output_dir(self):
        dirname = os.path.dirname(self.video_file)
        output_dir = os.path.join(dirname, "%04d" % self.id)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = output_dir


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
    print(encoding_video.list_video_track)
    print(encoding_video.list_audio_track)
    print(encoding_video.list_subtitle_track)
    print(encoding_video.list_image_track)
