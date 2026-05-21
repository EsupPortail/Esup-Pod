"""Esup-Pod - Launch custom calculation model for each video of the platform

*  run with 'python manage.py respit_launcher [--dry]'
"""

import importlib
from argparse import _
from datetime import datetime, timedelta, date

from django.core.mail import mail_managers
from django.template.defaultfilters import striptags

from pod import settings
from pod.custom.settings_local import RESPIT_MODEL, WARN_DEADLINES
from pod.video.models import Video, Channel, Comment, Type, Theme, Category

from pod.playlist.models import Playlist

import time

from django.core.management.base import BaseCommand, CommandError

from django.db.models import Q

from pod.video.tests.test_obsolescence import ARCHIVE_OWNER_USERNAME

USE_RESPIT = getattr(settings, "USE_RESPIT", False)
SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)
URL_SCHEME = "https" if SECURE_SSL_REDIRECT else "http"


class Command(BaseCommand):
    dry_mode = False

    def add_arguments(self, parser) -> None:
        """Add possible args to the command."""
        parser.add_argument(
            "--dry",
            help="Simulate what would be done.",
            action="store_true",
            default=False,
        )

    # flake8: noqa: C901
    def handle(self, *args, **options):
        """Get all concerned datas for each video and launch the custom calculation model"""
        if options["dry"]:
            self.dry_mode = True

        if USE_RESPIT:

            all_warn = WARN_DEADLINES
            higher_warn = 0

            for aw in all_warn:
                if higher_warn <= aw:
                    higher_warn = aw

            notif_list = []

            videos = Video.objects.exclude(owner__username=ARCHIVE_OWNER_USERNAME)

            for p in videos:

                if (p.date_delete - timedelta(days=higher_warn + 1)) <= (date.today()):
                    data_to_add = {}

                    data_to_add["id"] = p.id
                    data_to_add["title"] = p.title
                    data_to_add["view_count"] = p.get_viewcount()
                    data_to_add["view_count_year"] = p.get_viewcount(365)
                    data_to_add["is_draft"] = p.is_draft
                    data_to_add["is_restricted"] = p.is_restricted

                    today = datetime.now()
                    diff = today - datetime(
                        p.date_added.year,
                        p.date_added.month,
                        p.date_added.day,
                        p.date_added.hour,
                        p.date_added.minute,
                        p.date_added.second,
                    )
                    data_to_add["date_added"] = datetime(
                        p.date_added.year,
                        p.date_added.month,
                        p.date_added.day,
                        p.date_added.hour,
                        p.date_added.minute,
                        p.date_added.second,
                    )
                    data_to_add["days_on_platform"] = diff.days
                    data_to_add["date_delete"] = p.date_delete
                    data_to_add["description"] = p.description

                    # Channels (count and id)
                    nb_chaine = 0
                    channel_list = []
                    for vvc in Channel.objects.filter(video=p):
                        channel_list.append(vvc.id)
                        nb_chaine = nb_chaine + 1

                    data_to_add["channel_list"] = channel_list
                    data_to_add["nb_channel"] = nb_chaine

                    # Number of times added to favorites
                    cfav = 0

                    favorites = Playlist.objects.filter(name__exact="Favorites")
                    favoritesWthP = favorites.filter(playlistcontent__video=p).distinct()
                    for fw in favoritesWthP:
                        cfav = cfav + 1

                    data_to_add["nb_fav"] = cfav

                    # nb comment
                    nb_comment = 0
                    for fav in Comment.objects.filter(video=p):
                        nb_comment = nb_comment + 1

                    data_to_add["nb_comment"] = nb_comment

                    # duration
                    data_to_add["duration_video"] = p.duration

                    # video type
                    type_name = ""
                    type_id = ""
                    for tv in Type.objects.filter(video=p):
                        type_name = tv.title
                        type_id = tv.id

                    data_to_add["type_name_video"] = type_name
                    data_to_add["type_id_video"] = type_id

                    # Video Theme
                    theme_list = []
                    nb_theme = 0
                    for vthe in Theme.objects.filter(video=p):
                        nb_theme = nb_theme + 1
                        theme_list.append(vthe.id)

                    data_to_add["nb_theme"] = nb_theme
                    data_to_add["theme_list"] = theme_list

                    # Video Owner
                    for ow in Video.objects.filter(id=p.id):
                        data_to_add["owner_video"] = ow.owner.username

                    # Video Owner Additionnal
                    additionnal_owner_list = []
                    for owc in p.additional_owners.all():
                        additionnal_owner_list.append(owc.username)

                    data_to_add["owner_video_additional"] = additionnal_owner_list

                    # Category
                    category_list = []
                    for cat in Category.objects.filter(video=p):
                        category_list.append(cat.id)

                    data_to_add["category_list"] = category_list

                    # launch the calcul model
                    try:
                        mod = importlib.import_module(
                            "pod.video.management.commands.respit_model." + RESPIT_MODEL
                        )
                    except ModuleNotFoundError as e:
                        self.stderr.write(
                            self.style.ERROR(_("An Error occurred while processing."))
                        )
                        raise CommandError(
                            _("Respit model not found: %(error)s") % {"error": e}
                        ) from e
                    except ImportError as e:
                        self.stderr.write(
                            self.style.ERROR(_("An Error occurred while processing."))
                        )
                        raise CommandError(
                            _("Respit model import error: %(error)s") % {"error": e}
                        ) from e

                    # Insert repist in BDD
                    daysmore = mod.calcul(data_to_add,self.dry_mode)

                    if self.dry_mode is False:
                        p.date_delete = p.date_delete + timedelta(days=daysmore)
                        p.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                "Add " + str(daysmore) + " days to the delete_date"
                            )
                        )
                        self.stdout.write(self.style.SUCCESS(p.date_delete))
                        self.stdout.write("")

                        notif_list.append((p, daysmore))

                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                "DRY MODE : Simultate a Adding of "
                                + str(daysmore)
                                + " days to the delete_date"
                            )
                        )
                        self.stdout.write(
                            self.style.SUCCESS(str(p.date_delete + timedelta(daysmore)))
                        )
                        self.stdout.write("")
                else:
                    self.stdout.write(
                        "Video '"
                        + p.title
                        + "' has a date delete the "
                        + str(p.date_delete)
                        + ". It's in more than "
                        + str(int(higher_warn + 1))
                        + " days. Nothing to do."
                    )

            if self.dry_mode is False:
                if not notif_list:
                    self.stdout.write("\n")
                    self.stdout.write(
                        "** No calculated respit. Don't send the mail to the managers. **"
                    )
                else:
                    self.stdout.write("\n")
                    self.stdout.write("** Send the mail to the managers. **")
                    msg_html = (
                        "Hello !</br></br>The deadline for the following videos has been postponed according to the model's guidelines : "
                        + RESPIT_MODEL
                        + " : <ul>"
                    )

                    for video, daysmore in notif_list:
                        msg_html += "<li>"
                        msg_html += (
                            "%(title)s ("
                            + "<a href='%(scheme)s:%(url)s' rel='noopener'"
                            + " target='_blank'>%(scheme)s:%(url)s</a>) add %(daysmore)s day(s)."
                        ) % {
                            "scheme": URL_SCHEME,
                            "url": video.get_full_url(),
                            "title": video.title,
                            "daysmore": daysmore
                        }
                        msg_html += "</li>"

                    msg_html += "</ul></br>Have a good day."

                    # print(msg_html)
                    mail_managers(
                        "Deadline Postponed",
                        striptags(msg_html),
                        fail_silently=False,
                        html_message=msg_html,
                    )

        else:
            raise CommandError("USE_RESPIT is FALSE")

        self.stdout.write("End")
