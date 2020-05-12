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


USE_OBSOLESCENCE = getattr(
    settings, "USE_OBSOLESCENCE", False)
USE_ESTABLISHMENT = getattr(
    settings, 'USE_ESTABLISHMENT_FIELD', False)
MANAGERS = getattr(settings, 'MANAGERS', {})
CONTACT_US_EMAIL = getattr(
    settings, 'CONTACT_US_EMAIL', [
        mail for name, mail in getattr(settings, 'MANAGERS')])

SECURE_SSL_REDIRECT = getattr(settings, 'SECURE_SSL_REDIRECT', False)
URL_SCHEME = "https" if SECURE_SSL_REDIRECT else "http"

##
# Settings exposed in templates
#
TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    'TEMPLATE_VISIBLE_SETTINGS',
    {
        'TITLE_SITE': 'Pod',
        'TITLE_ETB': 'University name',
        'LOGO_SITE': 'img/logoPod.svg',
        'LOGO_ETB': 'img/logo_etb.svg',
        'LOGO_PLAYER': 'img/logoPod.svg',
        'LINK_PLAYER': '',
        'FOOTER_TEXT': ('',),
        'FAVICON': 'img/logoPod.svg',
        'CSS_OVERRIDE': '',
        'PRE_HEADER_TEMPLATE': '',
        'POST_FOOTER_TEMPLATE': '',
        'TRACKING_TEMPLATE': '',
    }
)
TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, 'TITLE_SITE', 'Pod')
DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@univ.fr')
ARCHIVE_OWNER_USERNAME = getattr(settings, 'ARCHIVE_OWNER_USERNAME', 'archive')
# list of affiliation's owner to archive instead of delete video
POD_ARCHIVE_AFFILIATION = getattr(settings, 'POD_ARCHIVE_AFFILIATION', [])
# number of step in days defore deletion
WARN_DEADLINES = getattr(settings, "WARN_DEADLINES", [])
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", 'fr')


class Command(BaseCommand):

    def handle(self, *args, **options):
        # Activate a fixed locale fr
        translation.activate(LANGUAGE_CODE)

        if USE_OBSOLESCENCE:
            list_video = self.get_video_treatment_and_notify_user()
            self.notify_manager_of_obsolete_video(list_video)
            (
                list_video_to_delete,
                list_video_to_archive
            ) = self.get_video_archived_deleted_treatment()
            self.notify_manager_of_deleted_video(list_video_to_delete)
            self.notify_manager_of_archived_video(list_video_to_archive)
        else:
            self.stderr.write(
                self.style.ERROR(
                    _('An Error occurred while processing ')
                )
            )
            raise CommandError(
                _('USE_OBSOLESCENCE is FALSE')
            )

    def get_video_treatment_and_notify_user(self):
        # check video with deadlines to send email to each owner
        list_video_notified_by_establishment = {}
        list_video_notified_by_establishment.setdefault('other', {})
        for step_day in sorted(WARN_DEADLINES):
            step_date = date.today() + timedelta(days=step_day)
            videos = Video.objects.filter(date_delete=step_date,
                                          sites=get_current_site(
                                              settings.SITE_ID))
            for video in videos:
                # self.notify_user(video, step_day)
                if (
                    USE_ESTABLISHMENT and
                    MANAGERS and
                    video.owner.owner.establishment.lower() in dict(MANAGERS)
                ):
                    list_video_notified_by_establishment.setdefault(
                        video.owner.owner.establishment.lower(), {})
                    list_video_notified_by_establishment[
                        video.owner.owner.establishment.lower()].setdefault(
                            str(step_day), []).append(video)
                else:
                    list_video_notified_by_establishment['other'].setdefault(
                        str(step_day), []).append(video)

        return list_video_notified_by_establishment

    def get_video_archived_deleted_treatment(self):
        # get video with deadline out of time to deal with deletion
        vids = Video.objects.filter(
            sites=get_current_site(None),
            date_delete__lt=date.today()).exclude(
            owner__username=ARCHIVE_OWNER_USERNAME)

        list_video_deleted_by_establishment = {}
        list_video_deleted_by_establishment.setdefault('other', {})

        list_video_archived_by_establishment = {}
        list_video_archived_by_establishment.setdefault('other', {})

        for vid in vids:
            title = "%s - %s" % (vid.id, vid.title)
            estab = vid.owner.owner.establishment.lower()

            if vid.owner.owner.affiliation in POD_ARCHIVE_AFFILIATION:
                self.write_in_csv(vid, 'archived')
                archive_user, created = User.objects.get_or_create(
                    username=ARCHIVE_OWNER_USERNAME,
                )
                vid.owner = archive_user
                vid.is_draft = True
                vid.title = "%s %s %s" % (
                    _('Archived'),
                    date.today(),
                    vid.title)
                vid.save()

                # add video to delete
                vid_delete, created = VideoToDelete.objects.get_or_create(
                    date_deletion=vid.date_delete)
                vid_delete.video.add(vid)
                vid_delete.save()
                if (
                    USE_ESTABLISHMENT
                    and MANAGERS
                    and estab in dict(MANAGERS)
                ):
                    list_video_archived_by_establishment.setdefault(
                        estab, {})
                    list_video_archived_by_establishment[estab].setdefault(
                        str(0), []).append(vid)
                else:
                    list_video_archived_by_establishment['other'].setdefault(
                        str(0), []).append(vid)

            else:
                self.write_in_csv(vid, 'deleted')
                vid.delete()
                if (
                    USE_ESTABLISHMENT
                    and MANAGERS
                    and estab in dict(MANAGERS)
                ):
                    list_video_deleted_by_establishment.setdefault(
                        estab, {})
                    list_video_deleted_by_establishment[estab].setdefault(
                        str(0), []).append(title)
                else:
                    list_video_deleted_by_establishment['other'].setdefault(
                        str(0), []).append(title)

        return (
            list_video_deleted_by_establishment,
            list_video_archived_by_establishment
        )

    def notify_user(self, video, step_day):
        name = video.owner.last_name + " " + video.owner.first_name
        if video.owner.is_staff:
            msg_html = _("Hello %(name)s,") % {"name": name}
            msg_html += "<br/>\n"
            msg_html += "<p>" + _(
                "Your video intitled \"%(title)s\" will soon arrive "
                + "at the deletion deadline.") % {
                "title": video.title
            }
            msg_html += "<br/>\n"
            msg_html += _("It will be deleted on %(date_delete)s.<br/>\n"
                          + "If you want to keep it, ") % {
                "date_delete": video.date_delete
            }
            msg_html += _(
                "you can change the removal date "
                + "by editing your video:</p>\n"
                + "<p><a href='%(scheme)s:%(url)s' "
                + "rel='noopener' target='_blank'>"
                + "%(scheme)s:%(url)s</a></p>\n") % {
                "scheme": URL_SCHEME,
                "url": video.get_full_url()}
            msg_html += "<p>" + _("Regards") + "</p>\n"
        else:
            msg_html = _("Hello %(name)s,") % {"name": name}
            msg_html += "<br/>\n"
            msg_html += "<p>" + _(
                "Your video intitled \"%(title)s\" will soon arrive "
                + "at the deletion deadline.") % {
                "title": video.title
            }
            msg_html += "<br/>\n"
            msg_html += _("It will be deleted on %(date_delete)s.<br/>\n"
                          + "If you want to keep it, ") % {
                "date_delete": video.date_delete
            }
            msg_html += _(
                "please contact the manager(s) in charge of your "
                + "establishment at this address(es): %(email_address)s</p>\n"
            ) % {"email_address": ", ".join(
                self.get_manager_emails(video))}
            msg_html += "<p>" + _("Regards") + "</p>\n"

        to_email = []
        to_email.append(video.owner.email)
        return send_mail(
            "[%s] %s" % (TITLE_SITE, _("A video will be obsolete on Pod")),
            striptags(msg_html),
            DEFAULT_FROM_EMAIL,
            to_email,
            fail_silently=False,
            html_message=msg_html,
        )

    def notify_manager_of_obsolete_video(self, list_video):
        for estab in list_video:
            if len(list_video[estab]) > 0:
                msg_html = _("Hello manager(s),") + " <br/>\n"
                msg_html += "<p>" + _(
                    "For information, "
                    + "you will find below the list of video will soon arrive "
                    + "at the deletion deadline.") + "</p>"

                msg_html += "\n<p>"
                msg_html += self.get_list_video_html(
                    list_video[estab], False)
                msg_html += "\n</p>"
                msg_html += "\n<p>" + _("Regards") + "</p>\n"

                subject = "[%s] %s" % (TITLE_SITE, _(
                    "The obsolete videos on Pod"))

                if estab == 'other':
                    mail_managers(
                        subject, striptags(msg_html), fail_silently=False,
                        html_message=msg_html)
                else:
                    to_email = []
                    to_email.append(dict(MANAGERS)[estab])
                    send_mail(
                        subject,
                        striptags(msg_html),
                        DEFAULT_FROM_EMAIL,
                        to_email,
                        fail_silently=False,
                        html_message=msg_html,
                    )

    def notify_manager_of_deleted_video(self, list_video):
        for estab in list_video:
            if len(list_video[estab]) > 0:
                msg_html = _("Hello manager(s),") + " <br/>\n"
                msg_html += (
                    "<p>" + _(
                        "For information, "
                        + "you will find below the list of deleted video.")
                    + "</p>")

                msg_html += "\n<p>"
                msg_html += self.get_list_video_html(
                    list_video[estab], True)
                msg_html += "\n</p>"
                msg_html += "\n<p>" + _("Regards") + "</p>\n"

                subject = "[%s] %s" % (TITLE_SITE, _(
                    "The deleted videos on Pod"))

                if estab == 'other':
                    mail_managers(
                        subject, striptags(msg_html), fail_silently=False,
                        html_message=msg_html)
                else:
                    to_email = []
                    to_email.append(dict(MANAGERS)[estab])
                    send_mail(
                        subject,
                        striptags(msg_html),
                        DEFAULT_FROM_EMAIL,
                        to_email,
                        fail_silently=False,
                        html_message=msg_html,
                    )

    def notify_manager_of_archived_video(self, list_video):
        for estab in list_video:
            if len(list_video[estab]) > 0:
                msg_html = _("Hello manager(s),") + " <br/>\n"
                msg_html += (
                    "<p>" + _(
                        "For information, "
                        + "you will find below the list of archived video.")
                    + "</p>")

                msg_html += "\n<p>"
                msg_html += self.get_list_video_html(
                    list_video[estab], False)
                msg_html += "\n</p>"
                msg_html += "\n<p>" + _("Regards") + "</p>\n"

                subject = "[%s] %s" % (TITLE_SITE, _(
                    "The archived videos on Pod"))

                if estab == 'other':
                    mail_managers(
                        subject, striptags(msg_html), fail_silently=False,
                        html_message=msg_html)
                else:
                    to_email = []
                    to_email.append(dict(MANAGERS)[estab])
                    send_mail(
                        subject,
                        striptags(msg_html),
                        DEFAULT_FROM_EMAIL,
                        to_email,
                        fail_silently=False,
                        html_message=msg_html,
                    )

    def get_list_video_html(self, list_video, deleted):
        msg_html = ""
        for i, deadline in enumerate(list_video):
            if deleted is False and deadline != '0':
                if i != 0:
                    msg_html += "<br><br>"
                msg_html += "\n<strong>"
                msg_html += _("In %(deadline)s days") % {"deadline": deadline}
                msg_html += ":</strong>"
            for vid in list_video[deadline]:
                if deleted:
                    msg_html += "\n<br/> - " + vid
                else:
                    msg_html += (
                        "\n<br/> - %(title)s : "
                        + "<a href='%(scheme)s:%(url)s' rel='noopener'"
                        + " target='_blank'>%(scheme)s:%(url)s</a>.") % {
                        "scheme": URL_SCHEME,
                        "url": vid.get_full_url(), "title": vid
                    }
        return msg_html

    def get_manager_emails(self, video):
        if (
            USE_ESTABLISHMENT and
            MANAGERS and
            video.owner.owner.establishment.lower() in dict(MANAGERS)
        ):
            video_estab = video.owner.owner.establishment.lower()
            return dict(MANAGERS)[video_estab]
        else:
            return CONTACT_US_EMAIL

    def write_in_csv(self, vid, type):
        file = '%s/%s.csv' % (settings.LOG_DIRECTORY, type)
        exists = os.path.isfile(file)
        with open(file, 'a', newline='', encoding="utf-8") as csvfile:
            fieldnames = [
                'Date',
                'User name',
                'User email',
                'User Affiliation',
                'User Establishment',
                'Video Id',
                'Video title',
                'Video URL'
            ]
            writer = csv.DictWriter(
                csvfile, delimiter=';', fieldnames=fieldnames)
            if not exists:
                writer.writeheader()
            writer.writerow({
                'Date': date.today(),
                'User name': vid.owner.owner,
                'User email': vid.owner.email,
                'User Affiliation': vid.owner.owner.affiliation,
                'User Establishment': vid.owner.owner.establishment,
                'Video Id': vid.id,
                'Video title': vid.title,
                'Video URL': vid.get_full_url()
            })


"""
TO CHANGE ALL DATE DELETED
vds = Video.objects.all()
for vid in vds:
  vid.date_delete = date(vid.date_added.year+2,
                          vid.date_added.month,vid.date_added.day)
  vid.save()
"""
