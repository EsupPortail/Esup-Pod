"""Esup-Pod - Launch custom calculation model for each video of the platform

*  run with 'python manage.py create_archive_package [--dry]'
"""

import importlib
from datetime import datetime, timedelta, date

from django.core.mail import mail_managers
from django.template.defaultfilters import striptags

from pod import settings
from pod.custom.settings_local import RESPIT_MODEL, WARN_DEADLINES
from pod.video.models import Video, Channel, Comment, Type, Theme, Category

from pod.playlist.models import Playlist

# https://docs.djangoproject.com/fr/6.0/howto/custom-management-commands/   python3 manage.py respit_launcher
import time

from django.core.management.base import BaseCommand, CommandError

from django.db.models import Q

USE_RESPIT = getattr(settings, "USE_RESPIT", False)


class Command(BaseCommand):
    help = "Closes the specified poll for voting"
    dry_mode = False

    # flake8: noqa: C901
    def handle(self, *args, **options):
        """Get all concerned datas for each video and launch the custom calculation model"""
        if USE_RESPIT:

            all_warn = WARN_DEADLINES
            higher_warn = 0

            for aw in all_warn:
                if higher_warn <= aw:
                    higher_warn = aw

            notif_list = []

            videos = Video.objects.exclude(
                Q(title__startswith="Archivé") | Q(title__startswith="Archived")
            )
            for p in videos:

                if (p.date_delete - timedelta(days=higher_warn + 1)) <= (date.today()):
                    data_to_add = {}

                    # print(p.id)
                    # print(p.title)

                    data_to_add["id"] = p.id
                    data_to_add["title"] = p.title
                    data_to_add["view_count"] = p.get_viewcount()
                    data_to_add["view_count_year"] = p.get_viewcount(365)

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

                    # Nombre de chaines
                    nb_chaine = 0

                    for vvc in Channel.objects.filter(video=p):
                        nb_chaine = nb_chaine + 1

                    data_to_add["channel_count"] = nb_chaine

                    # Nombre de fois en favoris
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
                    data_to_add["duration_video"] = time.strftime(
                        "%H:%M:%S", time.gmtime(p.duration)
                    )

                    # video type
                    type = ""
                    for tv in Type.objects.filter(video=p):
                        type = tv.title

                    data_to_add["type_video"] = type

                    # Video Theme
                    theme_list = []
                    for vthe in Theme.objects.filter(video=p):
                        theme_list.append(vthe.title)

                    data_to_add["themes_video"] = theme_list

                    # Video Owner
                    for ow in Video.objects.filter(id=p.id):
                        data_to_add["owner_video"] = ow.owner.username

                    # Video Owner Additionnal
                    additionnal_owner_list = []
                    for owc in p.additional_owners.all():
                        additionnal_owner_list.append(owc.username)

                    data_to_add["owner_video_additional"] = additionnal_owner_list

                    # Categorie
                    category_list = []
                    for cat in Category.objects.filter(video=p):
                        category_list.append(cat.slug)

                    data_to_add["category_list"] = category_list

                    # laucnh the calcul model
                    mod = importlib.import_module(
                        "pod.video.management.commands.respit_model." + RESPIT_MODEL
                    )

                    # Insert repist in BDD
                    daysmore = mod.calcul(data_to_add)

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

                        notif_list.insert(p.id, p.title)

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
                        "Hello ! The deadline for the following videos has been postponed according to the model's guidelines : "
                        + RESPIT_MODEL
                        + " : \n"
                    )

                    for nl in notif_list:
                        msg_html += "-" + nl + "\n"

                    msg_html += "\nHave a good day."

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
