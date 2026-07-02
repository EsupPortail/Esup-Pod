"""Esup-Pod - Launch custom calculation model for each video of the platform

*  run with `python manage.py respite_launcher [--dry]`
"""

import importlib
from datetime import date, datetime, timedelta

from django.core.mail import mail_managers
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import striptags
from django.utils.translation import gettext_lazy as _

from pod import settings
from pod.playlist.models import Playlist
from pod.video.models import Category, Channel, Comment, Discipline, Theme, Video

ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")
USE_RESPITE = getattr(settings, "USE_RESPITE", False)
RESPITE_MODEL = getattr(settings, "RESPITE_MODEL", "base")
WARN_DEADLINES = getattr(settings, "WARN_DEADLINES", [60, 30, 7])
MANAGERS = getattr(settings, "MANAGERS", [])
SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)
URL_SCHEME = "https" if SECURE_SSL_REDIRECT else "http"


class Command(BaseCommand):
    dry_mode = False
    notif_list = []

    def add_arguments(self, parser) -> None:
        """Declare command-line arguments."""
        parser.add_argument(
            "--dry",
            help="Simulate what would be done.",
            action="store_true",
            default=False,
        )

    def handle(self, *args, **options):
        """Run respite processing for all applicable videos and notify managers if needed."""

        if not USE_RESPITE:
            raise CommandError("USE_RESPITE is FALSE")

        if options["dry"]:
            self.dry_mode = True

        higher_warn = self._get_higher_warn()
        respite_module = self._load_respit_model()

        videos = Video.objects.exclude(owner__username=ARCHIVE_OWNER_USERNAME)

        for vid in videos:
            self._process_video(vid, higher_warn, respite_module)

        if not self.dry_mode:
            self._notify_results()

        self.stdout.write("End")

    def _get_higher_warn(self):
        """Return the highest deadline from WARN_DEADLINES."""
        return max(WARN_DEADLINES, default=0)

    def _load_respit_model(self):
        """Import and return the respit model module."""
        try:
            return importlib.import_module(
                "pod.video.management.commands.respite_model." + RESPITE_MODEL
            )
        except ModuleNotFoundError as e:
            self.stderr.write(self.style.ERROR(_("An Error occurred while processing.")))
            raise CommandError(
                _("Respite model not found: %(error)s") % {"error": e}
            ) from e
        except ImportError as e:
            self.stderr.write(self.style.ERROR(_("An Error occurred while processing.")))
            raise CommandError(
                _("Respite model import error: %(error)s") % {"error": e}
            ) from e

    def _apply_respit(self, vid, daysmore):
        """Apply or simulate the respit extension on a single video."""
        vid.date_delete = vid.date_delete + timedelta(days=daysmore)
        self.notif_list.append((vid, daysmore))
        if self.dry_mode is False:
            vid.save()
            self.stdout.write(
                self.style.SUCCESS(
                    "[Video %s] Add %s day(s) to the delete_date %s"
                    % (vid.id, str(daysmore), vid.date_delete)
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "DRY MODE: [Video %s] Simulate Adding %s day(s) to the delete_date %s."
                    % (
                        vid.id,
                        str(daysmore),
                        str(vid.date_delete + timedelta(daysmore)),
                    )
                )
            )
        self.stdout.write("")

    def _process_video(self, vid, higher_warn, respite_module):
        """Evaluate a video for respite extension and apply model results if eligible."""
        if (vid.date_delete - timedelta(days=higher_warn + 1)) <= (date.today()):
            video_data = self._get_video_data(vid)

            # Ask selected model for the numbers of days to be added to given video_data.
            daysmore = respite_module.calcul(video_data, self.dry_mode)
            self._apply_respit(vid, daysmore)
        else:
            self.stdout.write(
                "[Video %s] “%s” has a date delete the %s. It’s in more than %s days. Nothing to do."
                % (vid.id, vid.title, str(vid.date_delete), str(int(higher_warn + 1)))
            )

    def _get_video_data(self, vid):
        """Collect the video features required by the respite calculation model."""
        video_data = {}

        video_data["id"] = vid.id
        video_data["title"] = vid.title
        video_data["view_count"] = vid.get_viewcount()
        video_data["view_count_year"] = vid.get_viewcount(365)
        video_data["is_draft"] = vid.is_draft
        video_data["is_restricted"] = vid.is_restricted

        today = datetime.now()
        diff = today - datetime(
            vid.date_added.year,
            vid.date_added.month,
            vid.date_added.day,
            vid.date_added.hour,
            vid.date_added.minute,
            vid.date_added.second,
        )
        video_data["date_added"] = datetime(
            vid.date_added.year,
            vid.date_added.month,
            vid.date_added.day,
            vid.date_added.hour,
            vid.date_added.minute,
            vid.date_added.second,
        )
        video_data["days_on_platform"] = diff.days
        video_data["date_delete"] = vid.date_delete
        video_data["description"] = vid.description

        # Channels containing vid
        video_data["channels"] = list(Channel.objects.filter(video=vid))

        # Number of favorites containing vid
        favorites = Playlist.objects.filter(name__exact="Favorites")
        favorites_with_vid = favorites.filter(playlistcontent__video=vid).distinct()
        video_data["nb_fav"] = len(favorites_with_vid)

        # Number of comments on vid
        vid_comments = Comment.objects.filter(video=vid)
        video_data["nb_comment"] = len(vid_comments)

        # Video duration
        video_data["duration"] = vid.duration

        # Video Disciplines
        video_data["disciplines"] = list(Discipline.objects.filter(video=vid))

        # Video type
        video_data["type"] = vid.type

        # Video Theme
        video_data["themes"] = list(Theme.objects.filter(video=vid))

        # Video Owner
        video_data["owner"] = vid.owner.username

        # Video Owner Additionnal
        video_data["additional_owners"] = list(vid.additional_owners.all())

        # Categories
        video_data["categories"] = list(Category.objects.filter(video=vid))

        return video_data

    def _notify_results(self):
        """Notify managers with results of respite calculations and send emails if needed."""
        if not self.notif_list:
            self.stdout.write("\n")
            self.stdout.write(
                "** No calculated respite. Don’t send the mail to the managers. **"
            )
        else:
            self.stdout.write("\n")
            self.stdout.write("** Send a mail to the managers. **")
            msg_html = ""
            if self.dry_mode:
                msg_html = "<p> << %s >> </p>" % _(
                    "DRY MODE. This is only a simulation of what would be done."
                )
            msg_html += (
                _(
                    "Hello! The deadline for the following videos has been postponed according to the model’s guidelines: <strong>%s</strong>"
                )
                % RESPITE_MODEL
            )

            if RESPITE_MODEL == "base":
                msg_html += "<p><strong>%s</strong></p>" % _(
                    "Be careful: BASE mode is just a proof of concept, not intented to be used in production."
                )

            msg_html += "<ul>"
            for video, daysmore in self.notif_list:
                if daysmore > 0:
                    msg_html += (
                        '<li><a href="%(scheme)s:%(url)s">“%(title)s”</a> - postponed to %(date)s (+%(daysmore)s day(s))</li>'
                        % {
                            "scheme": URL_SCHEME,
                            "url": video.get_full_url(),
                            "title": video.title,
                            "date": video.date_delete,
                            "daysmore": daysmore,
                        }
                    )
                else:
                    msg_html += (
                        '<li><a href="%(scheme)s:%(url)s">“%(title)s”</a> - keeped unchanged at %(date)s</li>'
                        % {
                            "scheme": URL_SCHEME,
                            "url": video.get_full_url(),
                            "title": video.title,
                            "date": video.date_delete,
                        }
                    )

            msg_html += "</ul><p>%s</p>" % _("Have a good day.")
            if len(MANAGERS) > 0:
                mail_managers(
                    "Deadline Postponed",
                    striptags(msg_html),
                    fail_silently=False,
                    html_message=msg_html,
                )
            else:
                self.stdout.write(msg_html)
                self.stdout.write(
                    self.style.WARNING(
                        "NO mail sent. Set MANAGER in your settings first."
                    )
                )
