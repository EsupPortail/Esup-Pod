""" This module handles video encoding with CPU or GPU. """

from __future__ import absolute_import, division, print_function
import time

from .Encoding_video_model import Encoding_video_model

# from unidecode import unidecode # third party package to remove accent
# import unicodedata

__author__ = "Nicolas CAN <nicolas.can@univ-lille.fr>"
__license__ = "LGPL v3"

from .models import Video
from .utils import change_encoding_step, check_file, add_encoding_log, send_email


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
        return

    change_encoding_step(video_id, 0, "start")

    encoding_video = Encoding_video_model(video_id, video_to_encode.video.path)
    encoding_video.encoding_log += start
    change_encoding_step(video_id, 1, "get video data")
    encoding_video.get_video_data()
    change_encoding_step(video_id, 2, "remove old data")
    encoding_video.remove_old_data()
    # create video dir
    change_encoding_step(video_id, 3, "create output dir")
    encoding_video.create_output_dir()

    encoding_video.start_encode()

    # encode HLS
    # encode MP4
    # encode MP3
    # encode M4A

