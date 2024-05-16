"""Esup-Pod Chapter utilities."""

import time
import datetime

from webvtt import WebVTT
from pod.chapter.models import Chapter


def vtt_to_chapter(vtt, video):  # -> str | None:
    """Convert a vtt file to Pod chapters."""
    Chapter.objects.filter(video=video).delete()
    webvtt = WebVTT().read(vtt.file.path)
    for caption in webvtt:
        time_start = time.strptime(caption.start.split(".")[0], "%H:%M:%S")
        time_start = datetime.timedelta(
            hours=time_start.tm_hour,
            minutes=time_start.tm_min,
            seconds=time_start.tm_sec,
        ).total_seconds()

        if time_start > video.duration or time_start < 0:
            return (
                "The VTT file contains a chapter started at an "
                + "incorrect time in the video: {0}".format(caption.text)
            )

        new = Chapter()
        new.title = caption.text
        new.time_start = time_start
        new.video = video
        new.save()
