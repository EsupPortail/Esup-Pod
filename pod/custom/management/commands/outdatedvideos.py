import os
from django.utils import translation
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from pod.video.models import Video
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
import xlwt
from pod.main.context_processors import TEMPLATE_VISIBLE_SETTINGS
TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, "TITLE_SITE", "Pod")
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")
file_name = "outdated-videos-list.xls"
SAVE_SRC = os.getcwd()+"/"+file_name
STUDENT_YEAR = settings.STUDENT_VIDEO_LIMIT_YEAR
STAFF_YEAR = settings.STAFF_VIDEO_LIMIT_YEAR


class Command(BaseCommand):
    help = _("Listing outdated videos and Sending an email to warn the owner")
    wb = xlwt.Workbook()
    ws = wb.add_sheet(_("Videos outdated"))

    def handle(self, *args, **options):
        translation.activate(os.getenv('LANG'))
        style = xlwt.easyxf("font: bold 1; pattern: pattern solid,"
                            + " fore-colour light_orange")
        self.ws.write(0, 0, _("User"), style)
        self.ws.write(0, 1, _("Video"), style)
        self.ws.write(0, 2, _("Establishment"), style)
        self.line = 1
        try:
            for video in Video.objects.all():
                if "p" in video.owner.owner.affiliation.lower():
                    if video.year_elapsed() >= STAFF_YEAR:
                        # send an email to the staff concerned
                        self.sendEmail(video, STAFF_YEAR)
                        # write to excel file
                        self.write(video)
                else:
                    if video.year_elapsed() >= STUDENT_YEAR:
                        # send an email to the user concerned
                        self.sendEmail(video, STUDENT_YEAR)
                        # write to excel file
                        self.write(video)

            self.wb.save(SAVE_SRC)
            self.sendEmail(None, None, to_managers=True)
        except Video.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    _(
                        'Error when writing video %(id)s '
                        + 'in the file "%(file)s".')
                    % {'id': video.id, 'file': file_name}
                )
            )
            raise CommandError(
                    _('Video "%(video_title)s" does not exist')
                    % {'video_title': video.title}
            )

    def write(self, video):
        self.ws.write(self.line, 0, video.owner.__str__())
        self.ws.write(self.line, 1, video.title)
        self.ws.write(self.line, 2, video.owner.owner.establishment)
        # log
        self.stdout.write(
                self.style.SUCCESS(
                    ('Successfully writed video %(id)s.')
                    % {'id': video.id}
                )
        )
        self.line += 1

    def sendEmail(self, video, year, to_managers=False):
        file_rows = len(self.ws._Worksheet__rows)
        file_exist = os.path.isfile(SAVE_SRC)
        if to_managers and file_exist and file_rows > 1:
            self.send_manager_email()
        elif video:
            self.send_user_email(video, year)

    def send_manager_email(self):

        subject = "[%s] %s" % (
            TITLE_SITE,
            _(u"The obsolete videos on Pod")
        )
        message = "%s\n%s\n\n\n%s\n" % (
            _("Hello"),
            _(u"You will find attached the list of videos whose pod "
                + "hosting time is equal to or greater than "
                + "%(year)s years") % {'year': STUDENT_YEAR},
            _("Regards")
        )
        html_message = '<p>%s</p><p>%s</p><p>%s</p>' % (
            _("Hello"),
            _(u"You will find attached the list of videos whose pod "
                + "hosting time is equal to or greater than %(year)s"
                + " years") % {'year': STUDENT_YEAR},
            _("Regards")
        )
        MANAGERS = getattr(settings, 'MANAGERS', [])
        bcc_email = []
        if MANAGERS:
            for name, target_email in MANAGERS:
                bcc_email.append(target_email)
        msg = EmailMultiAlternatives(
                subject,
                message,
                DEFAULT_FROM_EMAIL,
                bcc=bcc_email)
        msg.attach_alternative(html_message, "text/html")
        msg.attach_file(SAVE_SRC)
        msg.send()

    def send_user_email(self, video, year):
        content_url = "http:%s" % video.get_full_url()
        subject = "[%s] %s" % (
            TITLE_SITE,
            _(u"Video #%(content_id)s will be deleted soon") % {
                'content_id': video.id
            }
        )
        message = "%s\n%s\n\n%s\n%s\n%s\n" % (
            _("Hello"),
            _(u"It's been more than %(year)s year since you posted "
                + "this video <b>“%(title)s”</b>, it will "
                + "soon be deleted! please return it again "
                + "or save it if you still have it.")
            % {'year': year, 'title': video.title},
            _(u"You will find it here:"),
            content_url,
            _("Regards")
        )
        to_email = []
        to_email.append(video.owner.email)

        html_message = ""

        html_message = '<p>%s</p><p>%s</p><p>%s<br><a href="%s"><i>%s</i></a>\
                    </p><p>%s</p>' % (
            _("Hello"),
            _(u"It's been more than %(year)s year since you posted "
                + "this video <b>“%(title)s”</b>, "
                + "it will soon be deleted! "
                + "please return it again or save it if you still have it.")
            % {'year': year, 'title': video.title},
            _(u"You will find it here:"),
            content_url,
            content_url,
            _("Regards")
        )
        send_mail(
                subject,
                message,
                DEFAULT_FROM_EMAIL,
                to_email,
                fail_silently=False,
                html_message=html_message)
