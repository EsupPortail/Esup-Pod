import os
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from pod.video.models import Video
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import mail_managers
from django.core.mail import EmailMultiAlternatives
import json, xlwt
from pod.main.context_processors import TEMPLATE_VISIBLE_SETTINGS
TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, "TITLE_SITE", "Pod")
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")
SAVE_SRC = os.getcwd()+"/outdated-videos-list.xls"
class Command(BaseCommand):
    help = _("Listing outdated videos and Sending an email to warn the owner")
    def handle(self, *args, **options):
        wb = xlwt.Workbook()
        ws = wb.add_sheet("Videos outdated")
        style = xlwt.easyxf("font: bold 1; pattern: pattern solid,"
        +" fore-colour light_orange")
        ws.write(0,0, "Utilisateur", style)
        ws.write(0,1, "Video", style)
        ws.write(0,2, "Etablissement", style)
        line = 1;
        try:
            for video in Video.objects.all():
                if "p" in video.owner.owner.affiliation.lower():
                    if video.year_elapsed() >= settings.STAFF_VIDEO_LIMIT_YEAR:
                        # send an email to the staff concerned
                        self.sendEmail(video, settings.STAFF_VIDEO_LIMIT_YEAR)
                        # write to excel file
                        ws.write(line, 0, video.owner.__str__())
                        ws.write(line, 1, video.title)
                        ws.write(line, 2, video.owner.owner.establishment)
                        line += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                'Successfully writed video [%s].' % video.id
                                )
                        )
                else:
                    if video.year_elapsed() >= settings.STUDDENT_VIDEO_LIMIT_YEAR:
                        # send an email to the user concerned
                        self.sendEmail(video, settings.STUDDENT_VIDEO_LIMIT_YEAR)
                        # write to excel file
                        ws.write(line, 0, video.id)
                        ws.write(line, 1, video.owner.__str__())
                        ws.write(line, 2, video.title)
                        line += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                'Successfully writed video [%s].' % video.id
                                )
                        )
            wb.save(SAVE_SRC)
            self.sendEmail(None, None, is_staff=True)
            os.remove(SAVE_SRC)
        except Video.DoesNotExist:
            self.stderr.write(
                self.style.ERROR('Successfully writed [%s].' % video.id)
            )
            raise CommandError('Video "%s" does not exist' % video)

    def sendEmail(self, video, year, is_staff=False):

        file_exist = os.path.isfile(SAVE_SRC)
        if file_exist and is_staff:
            self.send_manager_email();
        else:
            self.send_user_email(video, year);

    def send_manager_email(self):

        subject = "[%s] %s" % (
            TITLE_SITE,
            _(u"The obsolete videos on Pod")
        )
        message = "%s\n%s\n\n\n%s\n" % (
            _("Hello"),
            _(u"You will find attached the list of videos whose "
                +"duration of hiring on pod is equal or exceeds "
                +str(settings.STUDDENT_VIDEO_LIMIT_YEAR)+" years"),
            _("Regards")
        )
        html_message = '<p>%s</p><p>%s</p><p>%s</p>' % (
            _("Hello"),
            _(u"You will find attached the list of videos whose "
            +"duration of hiring on pod is equal or exceeds "
            +str(settings.STUDDENT_VIDEO_LIMIT_YEAR)+" years"),
            _("Regards")
        )
        MANAGERS = getattr(settings, 'MANAGERS', [])
        bcc_email = []
        if MANAGERS:
            for name, target_email in MANAGERS:
                bcc_email.append(target_email)
        msg = EmailMultiAlternatives(subject,
                message,
                DEFAULT_FROM_EMAIL,
                bcc=bcc_email
                )
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
            _(u"It's been more than "+str(year)+" year since you posted this video "+
                "“"+str(video.title)+"s”, it will soon be deleted! please return it"
            +" again or save it if you still have it."),
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
            _(u"It's been more than "+str(year)+" year since you posted this video "+
                "“"+str(video.title)+"s”, it will soon be deleted! please return it"
                +" again or save it if you still have it."),
            _(u"You will find it here:"),
            content_url,
            content_url,
            _("Regards")
        )
        send_mail(subject,
                message,
                DEFAULT_FROM_EMAIL,
                to_email,
                fail_silently=False,
                html_message=html_message,
                )
