from django.conf import settings
from django.utils import translation
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from django.template.defaultfilters import striptags
from django.core.mail import send_mail
from django.contrib.auth.models import User
# from django.core.mail import mail_admins
from django.core.mail import mail_managers

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
    }
)
TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, 'TITLE_SITE', 'Pod')
DEFAULT_FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@univ.fr')
ARCHIVE_OWNER_USERNAME = getattr(settings, 'ARCHIVE_OWNER_USERNAME', 'archive')
POD_ARCHIVE = getattr(settings, 'POD_ARCHIVE', True)
# number of step in days defore deletion
WARN_DEADLINES = getattr(settings, "WARN_DEADLINES", [])
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", 'fr')


class Command(BaseCommand):

    def handle(self, *args, **options):
        # Activate a fixed locale fr
        translation.activate(LANGUAGE_CODE)

        if USE_OBSOLESCENCE:
            self.notify_video_treatment()
            self.video_to_delete_treatment()
        else:
            self.stderr.write(
                self.style.ERROR(
                    _('An Error occurred while processing ')
                )
            )
            raise CommandError(
                _('USE_OBSOLESCENCE is FALSE')
            )

    def notify_video_treatment(self):
        # check video with deadlines to send email to each owner
        list_video_notified_by_establishment = {}
        list_video_notified_by_establishment.setdefault('other', {})
        for step_day in sorted(WARN_DEADLINES):
            step_date = date.today() - timedelta(days=step_day)
            videos = Video.objects.filter(date_delete=step_date)
            for video in videos:
                self.notify_user(video, step_day)
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

        self.notify_manager(list_video_notified_by_establishment, False)

    def video_to_delete_treatment(self):
        # get video with deadline out of time to deal with deletion
        vids = Video.objects.filter(date_delete__lt=date.today())
        print(date.today(), vids.first().date_delete)
        if POD_ARCHIVE:
            vids.exclude(owner__username=ARCHIVE_OWNER_USERNAME)

        list_video_deleted_by_establishment = {}
        list_video_deleted_by_establishment.setdefault('other', {})
        for vid in vids:
            title = vid.id + " - " + vid.title
            estab = vid.owner.owner.establishment.lower()

            if POD_ARCHIVE:
                archive_user, created = User.objects.get_or_create(
                    username=ARCHIVE_OWNER_USERNAME,
                )
                vid.owner = archive_user
                vid.is_draft = True
                vid.title = _('Archived') + " " + vid.title
                vid.save()

                # add video to delete
                vid_delete, created = VideoToDelete.objects.get_or_create(
                    date_deletion=vid.date_delete)
                vid_delete.video.add(vid)
                vid_delete.save()

            else:
                vid.delete()

            if (USE_ESTABLISHMENT and MANAGERS and estab in dict(MANAGERS)):
                list_video_deleted_by_establishment.setdefault(
                    estab, {})
                list_video_deleted_by_establishment[estab].setdefault(
                    str(0), []).append(title)
            else:
                list_video_deleted_by_establishment['other'].setdefault(
                    str(0), []).append(title)
        self.notify_manager(list_video_deleted_by_establishment, True)

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
                + "<p><a href='http:%(url)s' rel='noopener' target='_blank'>"
                + "http:%(url)s</a></p>.\n") % {
                "url": video.get_full_url()}
            msg_html += "<p>" + _("Regards") + "</p>.\n"
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
        send_mail(
            "[%s] %s" % (TITLE_SITE, _("A video will be obsolete on Pod")),
            striptags(msg_html),
            DEFAULT_FROM_EMAIL,
            to_email,
            fail_silently=False,
            html_message=msg_html,
        )

    def notify_manager(self, list_video, deleted):
        for estab in list_video:
            msg_html = _("Hello manager(s),") + " <br/>\n"
            if deleted:
                action = "archived" if POD_ARCHIVE else "deleted"
                msg_html += "<p>"
                msg_html += _(
                    "For information, "
                    + "you will find below the list of "
                    + "%(action)s videos.") % {"action": action}
                msg_html += "</p>"
            else:
                msg_html += "<p>" + _(
                    "For information, "
                    + "you will find below the list of video will soon arrive "
                    + "at the deletion deadline.") + "</p>"

            msg_html += "\n<p>"
            msg_html += self.get_list_video_html(
                list_video[estab], deleted)
            msg_html += "\n</p>"
            msg_html += "\n<p>" + _("Regards") + "</p>\n"

            if deleted:
                action = "archived" if POD_ARCHIVE else "deleted"
                subject = "[%s] %s" % (
                    TITLE_SITE,
                    _("The %(action)s videos on Pod") % {"action": action}
                )
            else:
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

    def get_list_video_html(self, list_video, deleted):
        msg_html = ""
        for deadline in list_video:
            if deleted is False:
                msg_html += "\n<br/>"
                msg_html += _("In %(deadline)s days") % {"deadline": deadline}
                msg_html += ":"
            for vid in list_video[deadline]:
                if deleted:
                    msg_html += "\n<br/> - " + vid
                else:
                    msg_html += (
                        "\n<br/> - <a href='http:%(url)s' rel='noopener'"
                        + " target='_blank'>%(title)s</a>.") % {
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


"""
TO CHANGE ALL DATE DELETED
vds = Video.objects.all()
for vid in vds:
  vid.date_delete = date(vid.date_added.year+2,
                          vid.date_added.month,vid.date_added.day)
  vid.save()
"""
