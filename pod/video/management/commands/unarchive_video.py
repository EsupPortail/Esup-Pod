"""Esup-Pod command to unarchive a video.

*  run with 'python manage.py unarchive_video vid_id [--user_id=userid]'
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from django.utils.translation import activate

from pod.video.management.commands.create_archive_package import read_archived_csv
from pod.video.models import Video, default_date_delete

ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", "fr")
ARCHIVE_CSV = "%s/archived.csv" % settings.LOG_DIRECTORY


class Command(BaseCommand):
    """unarchive_video command class."""

    help = "Unarchive a video"

    def add_arguments(self, parser) -> None:
        """Add possible args to the command."""
        # Video ID is required
        parser.add_argument("video_id", type=int, help="Video id")

        # Optional arguments
        parser.add_argument("--user_id", type=int, help="User id")

    def get_previous_owner(self, options: dict[str], video_id: int) -> User:
        """Get previous owner of an archived video."""
        owner = None
        if options["user_id"]:
            try:
                owner = User.objects.get(id=options["user_id"])
            except ObjectDoesNotExist:
                self.stdout.write(
                    self.style.ERROR('User not found by id "%s"' % options["user_id"])
                )
        else:
            # Get user from ARCHIVE_CSV
            csv_data = read_archived_csv()
            csv_entry = csv_data.get(str(video_id))
            if csv_entry:
                user_name = csv_entry["User name"].split("(")
                # extract username from "Fullname (username)" string
                user_name = user_name[-1][:-1]
                try:
                    owner = User.objects.get(username=user_name)
                except ObjectDoesNotExist:
                    self.stdout.write(
                        self.style.ERROR('User not found by name "%s"' % user_name)
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        "Video not found in %s. You must specify user_id manually."
                        % ARCHIVE_CSV
                    )
                )

        return owner

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

        user = self.get_previous_owner(options, video.id)
        if user:
            video.owner = user
            video.title = video.title[to_remove:]
            video.date_delete = default_date_delete()
            video.save()
            self.stdout.write(
                self.style.SUCCESS(
                    'Video "%s" has been unarchived and assigned to %s' % (video.id, user)
                )
            )
