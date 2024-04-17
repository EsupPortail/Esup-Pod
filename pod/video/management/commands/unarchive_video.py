"""Unarchive a video."""

from django.core.management.base import BaseCommand
from pod.video.models import Video, default_date_delete
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _
from django.conf import settings
from django.utils.translation import activate

from create_archive_package import read_archived_csv

ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", "fr")
ARCHIVE_CSV = "%s/archived.csv" % settings.LOG_DIRECTORY


class Command(BaseCommand):
    """unarchive_video command class."""

    help = "Unarchive a video"

    def add_arguments(self, parser) -> None:
        """Add possible args to the command."""
        parser.add_argument("video_id", type=int, help="Video id")
        parser.add_argument("user_id", type=int, help="User id")

    def handle(self, *args, **options) -> None:
        """Handle the unarchive_video command call."""
        activate(LANGUAGE_CODE)
        user = 1
        to_remove = len(_("Archived") + " 0000-00-00 ")

        try:
            video = Video.objects.get(id=options["video_id"])
            if video.owner.username != ARCHIVE_OWNER_USERNAME:
                self.stdout.write(
                    self.style.ERROR(
                        'Error: Video not archived "%s"' % options["video_id"]
                    )
                )
                return
        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR('Video not found "%s"' % options["video_id"])
            )
            return

        user_id = options["user_id"]
        # Get user_id from ARCHIVE_CSV
        if user_id is None:
            csv_data = read_archived_csv()
            csv_entry = csv_data.get(str(video.id))
            if csv_entry:
                user_id = csv_entry["User name"]
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "Video not found in %s. You must specify user_id manually." % ARCHIVE_CSV)
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
