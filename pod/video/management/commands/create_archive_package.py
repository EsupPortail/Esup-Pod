"""Esup-Pod - Export packages of archived videos and delete originals.

*  run with 'python manage.py create_archive_package [--dry]'
"""

import os

from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import mail_managers
from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify, striptags
from django.utils.translation import activate
from django.utils.translation import gettext as _

from pod.video.models import Video
from pod.main.utils import sizeof_fmt
from pod.video.utils import archive_pack, read_archived_csv

"""CUSTOM PARAMETERS."""
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", "fr")
ARCHIVE_ROOT = getattr(settings, "ARCHIVE_ROOT", "/video_archiving")
ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")
ARCHIVE_CSV = "%s/archived.csv" % settings.LOG_DIRECTORY
# Delay before an archived video is moved to archive_ROOT
ARCHIVE_HOW_MANY_DAYS = getattr(settings, "ARCHIVE_HOW_MANY_DAYS", 365)

__TITLE_SITE__ = (
    settings.TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (settings.TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
)


class Command(BaseCommand):
    """Move old archived videos from disk to ARCHIVE_ROOT."""

    help = "Move old archived videos to ARCHIVE_ROOT."
    dry_mode = False

    def add_arguments(self, parser) -> None:
        """Add possible args to the command."""
        parser.add_argument(
            "--dry",
            help="Simulate what would be done.",
            action="store_true",
            default=False,
        )

    def get_list_video_html(self, list_video: list) -> str:
        """Generate an html version of list_video."""
        msg_html = ["<ol>"]
        for vid in list_video:
            msg_html.append("<li>%s</li>" % vid)
        msg_html.append("</ol>")
        return "\n".join(msg_html)

    def handle(self, *args, **options) -> None:
        """Handle a command call."""
        activate(LANGUAGE_CODE)
        total_duration = 0
        total_processed = 0
        total_weight = 0
        list_video = []
        ignored_video = []

        if options["dry"]:
            self.dry_mode = True
            print("Simulation mode ('dry'). Nothing will be deleted.")

        # Get data from ARCHIVE_CSV
        csv_data = read_archived_csv()

        # Get videos
        vids = Video.objects.filter(
            owner__username=ARCHIVE_OWNER_USERNAME,
            date_delete__lte=datetime.now() - timedelta(days=ARCHIVE_HOW_MANY_DAYS),
        )

        print(
            "%s videos archived since more than %s days found."
            % (len(vids), ARCHIVE_HOW_MANY_DAYS)
        )
        for vid in vids:
            # vid = Video.objects.get(id=video_id)
            print("- Video slug: %s -" % vid.slug)

            if vid.recentViewcount > 0:
                # Do not archive a video with recent views.
                # (if video has been shared with a token, it can still be viewed)
                print("  * IGNORED (%s recent views)" % vid.recentViewcount)
                ignored_video.append(str(vid))
                continue

            # Recover original video slug
            csv_entry = csv_data.get(str(vid.id))
            to_remove = len(_("Archived") + " 0000-00-00 ")
            video_dir_name = "%04d-%s" % (vid.id, slugify(vid.title[to_remove:]))
            # Get username from CSV
            user_name = csv_entry["User name"]
            user_name = user_name.split("(")
            # extract username from "Fullname (username)" string
            user_name = user_name[-1][:-1]

            media_package_dir = os.path.join(ARCHIVE_ROOT, user_name, video_dir_name)

            if csv_entry:
                total_duration += vid.duration
                total_processed += 1
                if os.access(vid.video.path, os.F_OK):
                    total_weight += os.path.getsize(vid.video.path)
                list_video.append(str(vid))
                archive_pack(
                    media_package_dir,
                    user_name,
                    vid,
                    only_copy=False,
                    dry_mode=self.dry_mode,
                )
            else:
                print("  * Video %s not present in archived file" % vid.id)
            print("---")
        # Convert seconds in human readable time
        total_duration = str(timedelta(seconds=total_duration))
        total_msg = _(
            "Package archiving done. %(amount)s video(s) packaged (%(weight)s - [%(duration)s])"
            " - %(nb_ignored)s video(s) ignored."
        ) % {
            "amount": total_processed,
            "weight": sizeof_fmt(total_weight),
            "duration": total_duration,
            "nb_ignored": len(ignored_video),
        }

        print(total_msg)
        if total_processed > 0:
            self.inform_managers(list_video, ignored_video, total_msg, total_processed)

    def inform_managers(
        self, list_video: list, ignored_video: list, total_msg: str, total_processed: int
    ) -> None:
        """Inform site managers of packaged archives."""
        msg_html = [_("Hello manager(s) of  %s,") % __TITLE_SITE__]
        msg_html.append("<br>")
        if self.dry_mode:
            msg = (
                _(
                    "For your information, "
                    "below is the list of archived videos that would’ve been packaged in "
                    "your ARCHIVE_ROOT folder. Run the <code>create_archive_package</code> "
                    "command without the <code>--dry</code> option to delete them from %s."
                )
                % __TITLE_SITE__
            )
        else:
            msg = (
                _(
                    "For your information, "
                    "below is the list of archived videos that have been packaged in "
                    "your ARCHIVE_ROOT folder, and definitely deleted from %s."
                )
                % __TITLE_SITE__
            )

        msg_html.append("<p>%s</p>" % msg)
        msg_html.append(self.get_list_video_html(list_video))

        msg = _(
            "And below is the list of ignored videos that were not packaged "
            "because they have been recently viewed."
        )

        msg_html.append("<p>%s</p>" % msg)
        msg_html.append(self.get_list_video_html(ignored_video))

        msg_html.append("<p>%s</p>" % total_msg)
        msg_html.append("<p>%s</p>" % _("Regards."))
        msg_html = "\n".join(msg_html)
        subject = _("Packaging %s archived videos on Pod") % total_processed
        mail_managers(
            subject,
            striptags(msg_html),
            fail_silently=False,
            html_message=msg_html,
        )
        print("Summary sent by email to managers.")
