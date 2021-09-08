# -*- coding: utf-8 -*-
u"""Script supprimant des fichiers vidéos devenus inutiles."""

from django.core.management.base import BaseCommand
from pod.video.models import Video
from django.conf import settings
from os import listdir, remove
from os.path import isfile, join


class Command(BaseCommand):
    """Delete useless video files."""

    help = 'Delete useless video files (not associated with a video Object)'

    def handle(self, *args, **options):
        """Handle the clean_video_files command call."""
        list_dir = listdir(join(settings.MEDIA_ROOT, "videos"))
        print("Start cleaning useless video files, please wait...")
        for video_dir in list_dir:
            mypath = join(settings.MEDIA_ROOT, "videos", video_dir)
            onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
            for myfile in onlyfiles:
                try:
                    Video.objects.get(video="videos/%s/%s" % (video_dir, myfile))
                except Video.DoesNotExist :
                    vid_path = join(settings.MEDIA_ROOT, "videos", video_dir, myfile)
                    print(vid_path)
                    remove(vid_path)
        print("Useless video files cleaning done. Have a nice day ;)")
