"""Check Obsolete videos."""
from django.conf import settings
from django.utils import translation
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from django.template.defaultfilters import striptags
from django.core.mail import send_mail
from django.contrib.auth.models import User

# from django.core.mail import mail_admins
from django.core.mail import mail_managers
from django.contrib.sites.shortcuts import get_current_site
import csv
import os

from pod.video.models import Video, VideoToDelete

from datetime import date, timedelta


USE_OBSOLESCENCE = getattr(settings, "USE_OBSOLESCENCE", False)
USE_ESTABLISHMENT = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)
MANAGERS = getattr(settings, "MANAGERS", [])
CONTACT_US_EMAIL = getattr(
    settings,
    "CONTACT_US_EMAIL",
    [mail for name, mail in getattr(settings, "MANAGERS")],
)

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)
URL_SCHEME = "https" if SECURE_SSL_REDIRECT else "http"

##
# Settings exposed in templates
#
TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "TITLE_ETB": "University name",
        "LOGO_SITE": "img/logoPod.svg",
        "LOGO_ETB": "img/esup-pod.svg",
        "LOGO_PLAYER": "img/pod_favicon.svg",
        "LINK_PLAYER": "",
        "LINK_PLAYER_NAME": _("Home"),
        "FOOTER_TEXT": ("",),
        "FAVICON": "img/pod_favicon.svg",
        "CSS_OVERRIDE": "",
        "PRE_HEADER_TEMPLATE": "",
        "POST_FOOTER_TEMPLATE": "",
        "TRACKING_TEMPLATE": "",
    },
)
__TITLE_SITE__ = (
    TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
)
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")
ARCHIVE_OWNER_USERNAME = getattr(settings, "ARCHIVE_OWNER_USERNAME", "archive")
# list of affiliation's owner to archive instead of delete video
POD_ARCHIVE_AFFILIATION = getattr(settings, "POD_ARCHIVE_AFFILIATION", [])
# number of step in days defore deletion
WARN_DEADLINES = getattr(settings, "WARN_DEADLINES", [])
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", "fr")


class Command(BaseCommand):
    """Checking obsolete videos."""

    help = "Treatment of obsolete videos."

    def handle(self, *args, **options):
        """Handle the check_obsolete_videos command call."""
        # Activate a fixed locale fr
        translation.activate(LANGUAGE_CODE)

        if USE_OBSOLESCENCE:
            # Notify users for videos with close deadlines
            list_video = self.get_video_treatment_and_notify_user()
            self.notify_manager_of_obsolete_video(list_video)

            # Archive and delete videos with past deadlines
            (
                list_video_deleted,
                list_video_archived,
            ) = self.get_video_archived_deleted_treatment()
            self.notify_manager_of_deleted_video(list_video_deleted)
            self.notify_manager_of_archived_video(list_video_archived)
        else:
            self.stderr.write(self.style.ERROR(_("An Error occurred while processing.")))
            raise CommandError(_("USE_OBSOLESCENCE is FALSE"))

    def get_video_treatment_and_notify_user(self):
        """Check video with close deadlines to send email to each owner."""
        list_video_notified_by_establishment = {}
        list_video_notified_by_establishment.setdefault("other", {})
        for step_day in sorted(WARN_DEADLINES):
            step_date = date.today() + timedelta(days=step_day)
            videos = Video.objects.filter(
                date_delete=step_date, sites=get_current_site(settings.SITE_ID)
            )
            for video in videos:
                self.notify_user(video, step_day)
                if (
                    USE_ESTABLISHMENT
                    and MANAGERS
                    and video.owner.owner.establishment.lower() in dict(MANAGERS)
                ):
                    list_video_notified_by_establishment.setdefault(
                        video.owner.owner.establishment.lower(), {}
                    )
                    list_video_notified_by_establishment[
                        video.owner.owner.establishment.lower()
                    ].setdefault(str(step_day), []).append(video)
                else:
                    list_video_notified_by_establishment["other"].setdefault(
                        str(step_day), []
                    ).append(video)

        return list_video_notified_by_establishment

    def get_video_archived_deleted_treatment(self):
        """Get video with deadline out of time and delete them."""
        vids = Video.objects.filter(
            sites=get_current_site(None), date_delete__lt=date.today()
        ).exclude(owner__username=ARCHIVE_OWNER_USERNAME)

        list_video_deleted_by_establishment = {}
        list_video_deleted_by_establishment.setdefault("other", {})
        nb_deleted = 0

        list_video_archived_by_establishment = {}
        list_video_archived_by_establishment.setdefault("other", {})
        nb_archived = 0

        for vid in vids:
            title = "%s - %s" % (vid.id, vid.title)
            estab = vid.owner.owner.establishment.lower()

            if vid.owner.owner.affiliation in POD_ARCHIVE_AFFILIATION:
                self.write_in_csv(vid, "archived")
                archive_user, created = User.objects.get_or_create(
                    username=ARCHIVE_OWNER_USERNAME,
                )
                # Rename video and change owner.
                vid.owner = archive_user
                vid.is_draft = True
                vid.title = "%s %s %s" % (
                    _("Archived"),
                    date.today(),
                    vid.title,
                )
                # Trunc title to 250 chars max.
                vid.title = vid.title[:250]
                vid.save()
                nb_archived += 1

                # add video to delete
                vid_delete, created = VideoToDelete.objects.get_or_create(
                    date_deletion=vid.date_delete
                )
                vid_delete.video.add(vid)
                vid_delete.save()
                if USE_ESTABLISHMENT and MANAGERS and estab in dict(MANAGERS):
                    list_video_archived_by_establishment.setdefault(estab, {})
                    list_video_archived_by_establishment[estab].setdefault(
                        str(0), []
                    ).append(vid)
                else:
                    list_video_archived_by_establishment["other"].setdefault(
                        str(0), []
                    ).append(vid)

            else:
                self.write_in_csv(vid, "deleted")
                vid.delete()
                nb_deleted += 1
                if USE_ESTABLISHMENT and MANAGERS and estab in dict(MANAGERS):
                    list_video_deleted_by_establishment.setdefault(estab, {})
                    list_video_deleted_by_establishment[estab].setdefault(
                        str(0), []
                    ).append(title)
                else:
                    list_video_deleted_by_establishment["other"].setdefault(
                        str(0), []
                    ).append(title)

        print(_("%s video(s) deleted.") % nb_deleted)
        print(_("%s video(s) archived.") % nb_archived)

        return (
            list_video_deleted_by_establishment,
            list_video_archived_by_establishment,
        )

    def notify_user(self, video, step_day):
        """Notify a user that his video will be deleted soon."""
        name = video.owner.last_name + " " + video.owner.first_name
        if video.owner.is_staff:
            msg_html = _("Hello %(name)s,") % {"name": name}
            msg_html += "<br>\n"
            msg_html += "<p>" + _(
                'Your video intitled <a href="//%(url)s">"%(title)s"</a> will soon arrive'
                + " at the deletion deadline."
            ) % {"url": video.get_full_url(), "title": video.title}
            msg_html += "<br>\n"
            msg_html += _(
                "It will be deleted on %(date_delete)s.<br>\n"
                + "If you want to keep it, "
            ) % {"date_delete": video.date_delete}
            msg_html += _(
                "you can change the removal date "
                + "by editing your video:</p>\n"
                + "<p><a href='%(scheme)s:%(url)s' "
                + "rel='noopener' target='_blank'>"
                + "%(scheme)s:%(url)s</a></p>\n"
            ) % {"scheme": URL_SCHEME, "url": video.get_full_url()}
            msg_html += "<p>" + _("Regards") + "</p>\n"
        else:
            msg_html = _("Hello %(name)s,") % {"name": name}
            msg_html += "<br>\n"
            msg_html += "<p>" + _(
                'Your video intitled "%(title)s" will soon arrive '
                + "at the deletion deadline."
            ) % {"title": video.title}
            msg_html += "<br>\n"
            msg_html += _(
                "It will be deleted on %(date_delete)s.<br>\n"
                + "If you want to keep it, "
            ) % {"date_delete": video.date_delete}
            msg_html += _(
                "please contact the manager(s) in charge of your "
                + "establishment at this address(es): %(email_address)s</p>\n"
            ) % {"email_address": ", ".join(self.get_manager_emails(video))}
            msg_html += "<p>" + _("Regards") + "</p>\n"

        to_email = [video.owner.email]
        for additional in video.additional_owners.all():
            to_email.append(additional.email)
        return send_mail(
            "[%s] %s" % (__TITLE_SITE__, _("Your video will be obsolete")),
            striptags(msg_html),
            DEFAULT_FROM_EMAIL,
            to_email,
            fail_silently=False,
            html_message=msg_html,
        )
        print(
            _("Mail sent to %(to_email)s for video %(title)s.")
            % {"to_email": to_email, "title": video.title}
        )

    def notify_manager_of_obsolete_video(self, list_video):
        """Notify manager(s) with a list of obsolete videos."""
        for estab in list_video:
            if len(list_video[estab]) > 0:
                if estab != "other":
                    msg_html = _("Hello manager(s) of %(estab)s on %(site_title)s,") % {
                        "estab": estab,
                        "site_title": __TITLE_SITE__,
                    }
                else:
                    msg_html = _("Hello manager(s) of %(site_title)s,") % {
                        "site_title": __TITLE_SITE__
                    }
                msg_html += (
                    "<br>\n<p>"
                    + _(
                        "For information, "
                        + "you will find below the list of video will soon arrive "
                        + "at the deletion deadline."
                    )
                    + "</p>"
                )

                msg_html += "\n<p>"
                msg_html += self.get_list_video_html(list_video[estab], False)
                msg_html += "\n</p>"
                msg_html += "\n<p>" + _("Regards") + "</p>\n"

                subject = _("The obsolete videos on Pod")

                if estab == "other":
                    mail_managers(
                        subject,
                        striptags(msg_html),
                        fail_silently=False,
                        html_message=msg_html,
                    )
                else:
                    to_email = []
                    to_email.append(dict(MANAGERS)[estab])
                    send_mail(
                        "[%s] %s"
                        % (
                            __TITLE_SITE__,
                            subject,
                        ),
                        striptags(msg_html),
                        DEFAULT_FROM_EMAIL,
                        to_email,
                        fail_silently=False,
                        html_message=msg_html,
                    )
                if MANAGERS:
                    print(
                        _(
                            "Manager of '%(estab)s' notified for"
                            + " %(nb)s soon to be obsolete video(s)."
                        )
                        % {"estab": estab, "nb": len(list_video[estab])}
                    )

    def notify_manager_of_deleted_video(self, list_video):
        """Notify manager(s) with a list of deleted videos."""
        for estab in list_video:
            if len(list_video[estab]) > 0:
                if estab != "other":
                    msg_html = _("Hello manager(s) of %(estab)s on %(site_title)s,") % {
                        "estab": estab,
                        "site_title": __TITLE_SITE__,
                    }
                else:
                    msg_html = _("Hello manager(s) of %(site_title)s,") % {
                        "site_title": __TITLE_SITE__
                    }
                msg_html += (
                    "<br>\n<p>"
                    + _(
                        "For information, "
                        + "you will find below the list of deleted video."
                    )
                    + "</p>"
                )

                msg_html += "\n<p>"
                msg_html += self.get_list_video_html(list_video[estab], True)
                msg_html += "\n</p>"
                msg_html += "\n<p>" + _("Regards") + "</p>\n"

                subject = _("The deleted videos on Pod")

                if estab == "other":
                    mail_managers(
                        subject,
                        striptags(msg_html),
                        fail_silently=False,
                        html_message=msg_html,
                    )
                else:
                    to_email = []
                    to_email.append(dict(MANAGERS)[estab])
                    send_mail(
                        "[%s] %s"
                        % (
                            __TITLE_SITE__,
                            subject,
                        ),
                        striptags(msg_html),
                        DEFAULT_FROM_EMAIL,
                        to_email,
                        fail_silently=False,
                        html_message=msg_html,
                    )
                if MANAGERS:
                    print(
                        _("Manager of '%(et)s' notified for %(nb)s deleted video(s).")
                        % {"et": estab, "nb": len(list_video[estab])}
                    )

    def notify_manager_of_archived_video(self, list_video):
        """Notify manager(s) with a list of archived videos."""
        for estab in list_video:
            if len(list_video[estab]) > 0:
                if estab != "other":
                    msg_html = _("Hello manager(s) of %(estab)s on %(site_title)s,") % {
                        "estab": estab,
                        "site_title": __TITLE_SITE__,
                    }
                else:
                    msg_html = _("Hello manager(s) of %(site_title)s,") % {
                        "site_title": __TITLE_SITE__
                    }
                msg_html += (
                    "<br>\n<p>"
                    + _(
                        "For information, "
                        + "you will find below the list of archived video."
                    )
                    + "</p>"
                )

                msg_html += "\n<p>"
                msg_html += self.get_list_video_html(list_video[estab], False)
                msg_html += "\n</p>"
                msg_html += "\n<p>" + _("Regards") + "</p>\n"

                subject = _("The archived videos on Pod")

                if estab == "other":
                    # mail_managers() add EMAIL_SUBJECT_PREFIX in front of subject
                    mail_managers(
                        subject,
                        striptags(msg_html),
                        fail_silently=False,
                        html_message=msg_html,
                    )
                else:
                    to_email = []
                    to_email.append(dict(MANAGERS)[estab])
                    send_mail(
                        "[%s] %s"
                        % (
                            __TITLE_SITE__,
                            subject,
                        ),
                        striptags(msg_html),
                        DEFAULT_FROM_EMAIL,
                        to_email,
                        fail_silently=False,
                        html_message=msg_html,
                    )
                if MANAGERS:
                    print(
                        _("Manager of '%(estab)s' notified for %(nb)s archived video(s).")
                        % {"estab": estab, "nb": len(list_video[estab])}
                    )

    def get_list_video_html(self, list_video, deleted):
        """Generate an html version of list_video."""
        msg_html = ""
        for i, deadline in enumerate(list_video):
            if deleted is False and deadline != "0":
                if i != 0:
                    msg_html += "<br>\n"
                msg_html += "<p><strong>"
                msg_html += _("In %(deadline)s days:") % {"deadline": deadline}
                msg_html += "</strong></p>\n<ol>"
            for vid in list_video[deadline]:
                msg_html += "\n<li>"
                if deleted:
                    msg_html += vid
                else:
                    msg_html += (
                        "%(title)s ("
                        + "<a href='%(scheme)s:%(url)s' rel='noopener'"
                        + " target='_blank'>%(scheme)s:%(url)s</a>)."
                    ) % {
                        "scheme": URL_SCHEME,
                        "url": vid.get_full_url(),
                        "title": vid,
                    }
                msg_html += "</li>"
            msg_html += "</ol>"
        return msg_html

    def get_manager_emails(self, video):
        """Return the list of manager emails."""
        if (
            USE_ESTABLISHMENT
            and MANAGERS
            and video.owner.owner.establishment.lower() in dict(MANAGERS)
        ):
            video_estab = video.owner.owner.establishment.lower()
            return dict(MANAGERS)[video_estab]
        else:
            return CONTACT_US_EMAIL

    def write_in_csv(self, vid, type):
        """Add in `type`.csv file informations about the video."""
        file = "%s/%s.csv" % (settings.LOG_DIRECTORY, type)
        exists = os.path.isfile(file)

        fieldnames = [
            "Date",
            "User name",
            "User email",
            "User Affiliation",
            "User Establishment",
            "Video Id",
            "Video title",
            "Video URL",
            "Video type",
            "Date added",
            "Source file",
            "Description",
            "Views",
        ]
        if exists:
            self.check_csv_header(file, fieldnames)

        with open(file, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, delimiter=";", fieldnames=fieldnames)

            if not exists:
                writer.writeheader()
            writer.writerow(
                {
                    "Date": date.today(),
                    "User name": vid.owner.owner,
                    "User email": vid.owner.email,
                    "User Affiliation": vid.owner.owner.affiliation,
                    "User Establishment": vid.owner.owner.establishment,
                    "Video Id": vid.id,
                    "Video title": vid.title,
                    "Video URL": "https:%s" % vid.get_full_url(),
                    "Video type": vid.type.title,
                    "Date added": "%s" % vid.date_added.strftime("%Y/%m/%d"),
                    "Source file": vid.video,
                    "Description": vid.description.replace(";", "$semic$")
                    .replace("\r", "")
                    .replace("\n\n", "\n")
                    .replace("\n", "$newl$"),
                    "Views": vid.viewcount,
                }
            )

    def check_csv_header(self, csv_file, fieldnames):
        """Check for (and add) missing columns in an existing CSV file."""
        with open(csv_file, "r") as f:
            lines = f.readlines()
        if len(lines[0].split(";")) < len(fieldnames):
            print("Adding missing header columns in %s." % csv_file)
            lines[0] = ";".join(fieldnames) + "\n"
            with open(csv_file, "w") as f:
                f.writelines(lines)


"""
# TO CHANGE DATE DELETED FOR ALL VIDEOS
from pod.video.models import Video
from datetime import date
vds = Video.objects.all()
for vid in vds:
  vid.date_delete = date(vid.date_added.year+2,
                          vid.date_added.month,vid.date_added.day)
  print("%s,%s" % (vid.id, vid.title))
  vid.save()
"""

"""
# TO CHANGE DATE DELETED for user "adminPod"
from pod.video.models import Video
from datetime import date

vds = Video.objects.filter(date_delete__lte="2023-03-01", owner__username="adminPod")
# Do only the 50 first to avoid too many connexion on DB
for vid in vds[:50]:
  vid.date_delete = date(vid.date_delete.year+9,
                          vid.date_delete.month,vid.date_delete.day)
  print("%s,vid.owner,%s" % (vid.id, vid.title))
  vid.save()
"""
