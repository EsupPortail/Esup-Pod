""" This module handles video encoding with CPU or GPU. """

from __future__ import absolute_import, division, print_function
import json
import time
import os

# from unidecode import unidecode # third party package to remove accent
# import unicodedata

__author__ = "Nicolas CAN <nicolas.can@univ-lille.fr>"
__license__ = "LGPL v3"

from .models import EncodingVideo
from .models import EncodingAudio
from .models import PlaylistVideo
from .models import Video
from .utils import change_encoding_step, check_file, add_encoding_log, send_email
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


class Encoding_video:
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
                self.list_video_track[stream.get("index")] = {
                    "width": stream.get("width", 0),
                    "height": stream.get("height", 0)
                }
        if codec_type == "subtitle":
            self.list_subtitle_track[stream.get("index")] = {}

    def remove_old_data(self):
        """Remove old data."""
        video_to_encode = Video.objects.get(id=self.id)
        video_to_encode.thumbnail = None
        if video_to_encode.overview:
            image_overview = os.path.join(
                os.path.dirname(video_to_encode.overview.path), "overview.png"
            )
            if os.path.isfile(image_overview):
                os.remove(image_overview)
            video_to_encode.overview.delete()
        video_to_encode.overview = None
        video_to_encode.save()

        encoding_log_msg = ""
        encoding_log_msg += self.remove_previous_encoding_video(video_to_encode)
        encoding_log_msg += self.remove_previous_encoding_audio(video_to_encode)
        encoding_log_msg += self.remove_previous_encoding_playlist(video_to_encode)
        self.encoding_log += encoding_log_msg

    def remove_previous_encoding_video(self, video_to_encode):
        """Remove previously encoded video."""
        msg = "\n"
        previous_encoding_video = EncodingVideo.objects.filter(video=video_to_encode)
        if len(previous_encoding_video) > 0:
            msg += "\nDELETE PREVIOUS ENCODING VIDEO"
            # previous_encoding.delete()
            for encoding in previous_encoding_video:
                encoding.delete()
        else:
            msg += "Video: Nothing to delete"
        return msg

    def remove_previous_encoding_audio(self, video_to_encode):
        """Remove previously encoded audio."""
        msg = "\n"
        previous_encoding_audio = EncodingAudio.objects.filter(video=video_to_encode)
        if len(previous_encoding_audio) > 0:
            msg += "\nDELETE PREVIOUS ENCODING AUDIO"
            # previous_encoding.delete()
            for encoding in previous_encoding_audio:
                encoding.delete()
        else:
            msg += "Audio: Nothing to delete"
        return msg

    def remove_previous_encoding_playlist(self, video_to_encode):
        """Remove previously encoded playlist."""
        msg = "\n"
        previous_playlist = PlaylistVideo.objects.filter(video=video_to_encode)
        if len(previous_playlist) > 0:
            msg += "DELETE PREVIOUS PLAYLIST M3U8"
            # previous_encoding.delete()
            for encoding in previous_playlist:
                encoding.delete()
        else:
            msg += "Playlist: Nothing to delete"
        return msg

    def create_output_dir(self):
        dirname = os.path.dirname(self.video_file)
        output_dir = os.path.join(dirname, "%04d" % self.id)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.output_dir = output_dir


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

    encoding_video = Encoding_video(video_id, video_to_encode.video.path)
    encoding_video.encoding_log += start
    change_encoding_step(video_id, 1, "get video data")
    encoding_video.get_video_data()
    change_encoding_step(video_id, 2, "remove old data")
    encoding_video.remove_old_data()
    # create video dir
    change_encoding_step(video_id, 3, "create output dir")
    encoding_video.create_output_dir()
    # encode HLS
    # encode MP4
    # encode MP3
    # encode M4A


"""
remote encode ???

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Running encoding video.")
    parser.add_argument("--id", required=True, help="the ID of the video")
    parser.add_argument("--input", required=True, help="name of input file to encode")
    args = parser.parse_args()
"""
