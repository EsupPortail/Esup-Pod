import os
import time
import datetime

from django.conf import settings
from django.core.files import File
from django.apps import apps
from django.utils import timezone
from webvtt import WebVTT, Caption
from pod.chapter.models import Chapter
if apps.is_installed('pod.authentication'):
    from pod.authentication.models import Owner
    AUTH = True
if apps.is_installed('pod.filepicker'):
    FILEPICKER = True
    from pod.filepicker.models import CustomFileModel
    from pod.filepicker.models import UserDirectory

def vtt_to_chapter(vtt, video):
    Chapter.objects.filter(video=video).delete()
    if FILEPICKER:
        webvtt = WebVTT().read(vtt.file.path)
    else:
        webvtt = WebVTT().read(vtt.path)
    for caption in webvtt:
        time_start = time.strptime(caption.start.split('.')[0], '%H:%M:%S')
        time_start = datetime.timedelta(
            hours=time_start.tm_hour,
            minutes=time_start.tm_min,
            seconds=time_start.tm_sec).total_seconds()

        if time_start > video.duration or time_start < 0:
            return 'The VTT file contains a chapter started at an ' + \
                   'incorrect time in the video : {0}'.format(caption.text)
        
        new = Chapter()
        new.title = caption.text
        new.time_start = time_start
        new.video = video
        new.save()