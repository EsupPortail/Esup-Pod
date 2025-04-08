"""Esup-Pod previous instance video download command."""

from django.core.management.base import BaseCommand, CommandError
import wget
import os
import urllib.request
from django.conf import settings
from pod.video.models import Video

FROM_URL = getattr(settings, "FROM_URL", "https://pod.univ.fr/media/")


class Command(BaseCommand):
    """Download the specified video source file from a previous instance."""

    help = "Download the specified video source file from previous instance"

    def add_arguments(self, parser):
        parser.add_argument("video_id", nargs="+", type=int)

    def download(self, vid, video_id, source_url, dest_file):
        try:
            self.stdout.write(
                "\n - download %s: from %s to %s\n" % (video_id, source_url, dest_file)
            )
            new_file = wget.download(source_url, dest_file)
            self.stdout.write("\n")
            vid.video = new_file.replace(os.path.join(settings.MEDIA_ROOT, ""), "")
            vid.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully download video "%s"' % video_id)
            )
        except ValueError as e:
            raise CommandError('ValueError "%s"' % e)
        except FileNotFoundError as f:
            raise CommandError('FileNotFoundError "%s"' % f)
        except urllib.error.HTTPError as err:
            raise CommandError('HTTPError "%s"' % err)

    def handle(self, *args, **options):
        for video_id in options["video_id"]:
            vid = None
            try:
                vid = Video.objects.get(pk=video_id)
            except Video.DoesNotExist:
                raise CommandError('Video "%s" does not exist' % video_id)
            source_url = FROM_URL + vid.video.name if FROM_URL != "" else ""
            if source_url != "":
                dest_file = os.path.join(
                    settings.MEDIA_ROOT,
                    "videos",
                    vid.owner.owner.hashkey,
                    os.path.basename(vid.video.name),
                )
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                self.download(vid, video_id, source_url, dest_file)
            else:
                raise CommandError("source url is empty")
