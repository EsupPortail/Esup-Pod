import os
import re
import xlwt
import pytz
import operator
from datetime import datetime, timedelta
from django.utils import translation
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from pod.video.models import Video
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from pod.main.context_processors import TEMPLATE_VISIBLE_SETTINGS
TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, "TITLE_SITE", "Pod")
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")
file_name = "outdated-videos-list.xls"
SAVE_SRC = os.getcwd()+"/"+file_name
LIMIT_YEAR_VIDEO = getattr(settings, "LIMIT_YEAR_VIDEO", {})


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
        utc = pytz.UTC
        try:
            # get all obsoletes videos less than
            # (current year minus the smallest limit year)
            videos = Video.objects.filter(
                    date_added__lte=utc.localize(
                        datetime.now()-timedelta(365*self.get_year()
                            )
                        )
                    )
            for video in videos:
                cur_affil = self.get_affiliation(
                        video.owner.owner.affiliation.upper()
                        )
                if cur_affil in LIMIT_YEAR_VIDEO:
                    if video.year_elapsed() >= LIMIT_YEAR_VIDEO[cur_affil]:
                        # send an email to the user concerned
                        self.sendEmail(video, LIMIT_YEAR_VIDEO[cur_affil])
                        # write to excel file
                        self.write(video)
            self.wb.save(SAVE_SRC)
            self.sendEmail(None, None, to_managers=True)
            os.remove(SAVE_SRC)
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

    # return the bigger or smallest limit year video
    def get_year(self, smallest=True):
        if smallest:
            return min(
                    LIMIT_YEAR_VIDEO.items(),
                    key=operator.itemgetter(1)
                    )[1]
        else:
            return max(
                    LIMIT_YEAR_VIDEO.items(),
                    key=operator.itemgetter(1)
                    )[1]

    # return a user affiliation(s)
    def get_affiliation(self, cur_affil):
        if isinstance(cur_affil, str):
            if len(cur_affil) > 1:
                list_affil = " ".join(re.findall(
                    "[a-zA-Z]+", cur_affil)).split(" ")
                return self.bigger_affiliation(list_affil)
            else:
                return cur_affil

        elif isinstance(cur_affil, list):
            return self.bigger_affiliation(cur_affil)

    # return the affiliation that has the biggest limit of year
    def bigger_affiliation(self, list_affil):
        limit = 1
        bigger_af = ""
        for af in list_affil:
            if LIMIT_YEAR_VIDEO[af] > limit:
                bigger_af = af
                limit = LIMIT_YEAR_VIDEO[af]
        return bigger_af

    # write in excel file
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
                + "%(year)s years") % {'year': self.get_year()},
            _("Regards")
        )
        html_message = '<p>%s</p><p>%s</p><p>%s</p>' % (
            _("Hello"),
            _(u"You will find attached the list of videos whose pod "
                + "hosting time is equal to or greater than %(year)s"
                + " years") % {'year': self.get_year()},
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
