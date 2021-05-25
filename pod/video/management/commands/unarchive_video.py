from django.core.management.base import BaseCommand
from pod.video.models import Video, default_date_delete
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _
from django.conf import settings
from django.utils.translation import activate

ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", "fr")


class Command(BaseCommand):
    help = "Unarchive a video"

    def add_arguments(self, parser):
        parser.add_argument("video_id", type=int, help="Video id")
        parser.add_argument("user_id", type=int, help="User id")

    def handle(self, *args, **options):
        activate(LANGUAGE_CODE)
        video = 1
        user = 1
        to_remove = len(_("Archived") + " 0000-00-00 ")

        try:
            video = Video.objects.get(id=options["video_id"])
            if video.owner.username != ARCHIVE_OWNER_USERNAME:
                self.stdout.write(
                    self.style.ERROR(
                        'Error : Video not archived "%s"' % options["video_id"]
                    )
                )
                return
        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR('Video not found "%s"' % options["video_id"])
            )
            return
        try:
            user = User.objects.get(id=options["user_id"])
        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR('User not found "%s"' % options["user_id"])
            )
            return

        video.owner = user
        video.title = video.title[to_remove:]
        video.date_delete = default_date_delete()
        video.save()
        self.stdout.write(self.style.SUCCESS('Video "%s" has been unarchived' % video.id))
