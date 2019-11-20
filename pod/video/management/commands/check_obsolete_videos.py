import os
import re
import xlwt
from datetime import datetime
from django.utils import timezone
from django.utils import translation
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from pod.main.context_processors import TEMPLATE_VISIBLE_SETTINGS
from pod.video.models import Video, VideoToDelete
from pod.authentication.models import User
# import video utils functions
from pod.video.utils import remaining_days, remaining_weeks, remaining_months
from pod.video.utils import filter_obsoletes_videos

TITLE_SITE = getattr(TEMPLATE_VISIBLE_SETTINGS, "TITLE_SITE", "Pod")
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")
MANAGERS = getattr(settings, 'MANAGERS', [])
USE_ESTABLISHMENT = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)
POD_ARCHIVE = getattr(settings, "POD_ARCHIVE", False)
ARCHIVE_PASSWORD = getattr(settings, "ARCHIVE_PASSWORD", "&Jhon-Doe1234+&")
#  les moments où l'ont doit notifier l'utilisateur avant
#  la date de suppression de sa vidéo ex: 1m => 1 mois avant,
#  1s => 1 semaine avant et 1j => 1 jour avant
WARN_DEADLINES = getattr(settings, "WARN_DEADLINES", [])
soon_file = (
        "Soon-" + 'archived-videos.xls'if POD_ARCHIVE else "deleted-videos.xls"
        )
deleted_file = "Deleted-videos.xls"
archived_file = "Archived-videos.xls"
SAVE_SRC = os.getcwd()+"/"


class Command(BaseCommand):
    help = _("Listing outdated videos and Sending an email to warn the owner")
    line_soon = 1
    line_deleted = 1
    line_archived = 1
    wb_archived = xlwt.Workbook()
    wb_deleted = xlwt.Workbook()
    wb_soon = xlwt.Workbook()
    ws_archived = wb_archived.add_sheet(_("Archived videos"))
    ws_deleted = wb_deleted.add_sheet(_("Deleted videos"))
    ws_soon = wb_soon.add_sheet(_("Soon obsolete videos"))
    CONCERNED_MANAGERS_EMAILS = []

    def handle(self, *args, **options):
        self.set_column("archived")
        self.set_column("deleted")
        self.set_column("soon")
        translation.activate(os.getenv('LANG'))
        try:
            #  Tous les videos obsolètes exceptés celles
            #  dans la liste de suppression (VideoToDelete)
            all_videos = filter_obsoletes_videos(Video, WARN_DEADLINES)
            for v in all_videos:
                if not v.date_delete:
                    v.save()  # going to set date_delete attribute
                # Si on doit alerter l'utilisateur
                if self.remaining_time_to_alert_achieved(v):
                    #  Prevenir les manageurs seulement à la derniere notif
                    #  de la suppression prochaine d'une/des vidéo(s)
                    #  si on ne souhaite pas archiver les vidéos
                    #  if is_last and not POD_ARCHIVE:
                    #  Mémoriser le mail du manageur de l'etablissement
                    #  du propriétaire de la vidéo
                    self.set_concerned_manager_email(v)
                    #  Ecriture dans le fichier excel déstiné au(x) manageur(s)
                    self.write(v, "soon")
                    #  envoie de mail à l'utilisateur
                    self.send_email(v)
                #  Si la date de suppression est atteinte ou dépassée
                elif v.date_delete.date() <= timezone.now().date():
                    if POD_ARCHIVE:
                        #  Ecriture dans le fichier
                        #  excel déstiné au(x) manageur(s)
                        self.write(v, "archived")
                        #  change owner, make it private
                        #  change the slug, add it to videotodelete table
                        v.owner = self.get_archive_owner()
                        v.is_draft = True
                        v.slug = self.new_slug(v)
                        vd = VideoToDelete(date_deletion=v.date_delete)
                        vd.save()
                        v.videotodelete_set.add(vd)
                        v.save()
                        #  Garder le mail du manageur de l'établissement
                        #  du propritétaire de la vidéo
                        self.set_concerned_manager_email(v)
                    else:
                        #  Ecriture dans le fichier excel
                        #  déstiné au(x) manageur(s)
                        self.write(v, "deleted")
                        #  Suppression de la vidéo
                        v.delete()
            #  Sauvegarde des fichiers
            self.wb_archived.save(SAVE_SRC+archived_file)
            self.wb_deleted.save(SAVE_SRC+deleted_file)
            self.wb_soon.save(SAVE_SRC+soon_file)
            #  Envoie de mail au(x) manageur(s)
            self.send_email(None, to_manager=True)
            #  Suppression des fichiers
            os.remove(SAVE_SRC+archived_file)
            os.remove(SAVE_SRC+deleted_file)
            os.remove(SAVE_SRC+soon_file)
        except Video.DoesNotExist:
            self.stderr.write(
                self.style.ERROR(
                    _('An Error occurred while processing ')
                )
            )
            raise CommandError(
                    _('An error has occured')
            )

    def get_archive_owner(self):
        owner = User.objects.filter(username="archive").first()
        if not owner:
            owner = User()
            owner.username = "archive"
            owner.email = DEFAULT_FROM_EMAIL
            owner.password = ARCHIVE_PASSWORD
            owner.save()
        return owner

    def remaining_time_to_alert_achieved(self, video):
        video_remaining_times = [
                remaining_days(video.date_delete),
                remaining_weeks(video.date_delete),
                remaining_months(video.date_delete)]
        for remaining_time in video_remaining_times:
            if remaining_time in WARN_DEADLINES:
                return True
        return False

    def set_concerned_manager_email(self, video):
        if USE_ESTABLISHMENT:
            manager_emails = self.get_manager_emails(video)
            # save manager email if you are using establishment function
            self.CONCERNED_MANAGERS_EMAILS += [
                    email for email in manager_emails if (
                        email not in self.CONCERNED_MANAGERS_EMAILS)
                    ]

    def get_manager_emails(self, video):
        if USE_ESTABLISHMENT:
            estab = video.owner.owner.establishment
            # MANAGERS must be a nested tuple ( (k,v), (k,v) )
            return [v for k, v in MANAGERS if k == estab]
        return [v for k, v in MANAGERS]

    def new_slug(self, video):
        already_changed = next(
                iter(re.findall(r"(\-archived[\-\d]+)", video.slug)), None)
        archive_slug = "-archived-" + str(
                datetime.timestamp(datetime.now())
                ).replace(".", "-")
        if already_changed:
            archive_slug = video.slug.replace(already_changed, archive_slug)
        else:
            archive_slug = video.slug + archive_slug
        return archive_slug

    # Specify columns
    def set_column(self, type_sheet):
        # écriture des colonnes du fichier excel à générer
        style = xlwt.easyxf("font: bold 1; pattern: pattern solid,"
                            + " fore-colour light_orange")
        name = 'ws_{}'.format(type_sheet)
        ws = getattr(Command, name)
        ws.write(0, 0, _("User"), style)
        ws.write(0, 1, _("Video"), style)
        ws.write(0, 2, _("Url video"), style)
        ws.write(0, 3, _("Email addresse"), style)
        if POD_ARCHIVE:
            ws.write(0, 4, _("Archive date"), style)
        else:
            ws.write(0, 4, _("Delete date"), style)

        if USE_ESTABLISHMENT:
            ws.write(0, 5, _("Establishment"), style)

    # write in excel file
    def write(self, video, type_sheet):
        ws = getattr(Command, 'ws_{}'.format(type_sheet))
        line = getattr(Command, 'line_{}'.format(type_sheet))
        ws.write(line, 0, video.owner.owner.__str__())
        ws.write(line, 1, video.title)
        ws.write(line, 2, video.get_full_url())
        ws.write(line, 3, video.owner.email)
        ws.write(line, 4, video.date_delete.strftime("%d/%m/%Y"))
        if USE_ESTABLISHMENT:
            ws.write(line, 5, video.owner.owner.establishment)

        # log
        self.stdout.write(
                self.style.SUCCESS(
                    ('Successfully writed video %(id)s.')
                    % {'id': video.title}
                )
        )
        setattr(Command, 'line_{}'.format(type_sheet), line+1)

    def get_email_message(self, video, manager=False):
        plain_text = "%s\n%s\n\n\n%s\n"
        html_msg = "<p>%s</p><p>%s</p><p>%s</p>"
        if video:
            name = video.owner.last_name + " " + video.owner.first_name
            staff_msg_html = _(
                    u"you can change the removal date "
                    + "by editing your video:"
                    + "<p><a href='%(url)s' rel='noopener' target='_blank'>"
                    + "click here to edit your video</a></p>.") % {
                            "url": video.get_full_url()}
            staff_msg_text = _(
                    u"you can change the removal date "
                    + "by copying the link below on your browser:\n"
                    + "%(url)s\n") % {"url": video.get_full_url()}
            staff_msg = _(
                    u"Without modification on your part,"
                    + "the video will be deleted on %(deadline)s") % {
                            "deadline": video.date_delete.strftime("%d/%m/%Y")}
            msg = _(
                    u"Your video will soon arrive at the deletion deadline."
                    + "If you want to keep it, ")
            student_msg = _(
                    u"please contact the manager(s) in charge of your "
                    + "establishment at this address(es): %(email_address)s"
                    ) % {"email_address": ", ".join(
                        self.get_manager_emails(video))}
            body_msg_html = (
                    _("Hello %(name)s") % {"name": name},
                    (
                        msg + staff_msg_html + staff_msg
                        ) if video.owner.is_staff else msg + student_msg,
                    _("Regards")
                    )
            body_msg_text = (
                    _("Hello %(name)s") % {"name": name},
                    (
                        msg + staff_msg_text + staff_msg
                        ) if video.owner.is_staff else msg + student_msg,
                    _("Regards")
                    )
        manager_msg = (
                _("Hello"),
                _(
                    u"For information, you will find attached "
                    + "the list of videos that will be soon "
                    + ("archived or already archived " if POD_ARCHIVE
                        else "deleted or already deleted ") + "on Pod"),
                _("Regards")
                )
        if manager:
            return {
                    "plain_text": plain_text % manager_msg,
                    "html": html_msg % manager_msg}

        return {
                "plain_text": plain_text % body_msg_text,
                "html": html_msg % body_msg_html}

    def send_email(self, video, to_manager=False):
        archived_rows = len(self.ws_archived._Worksheet__rows)
        deleted_rows = len(self.ws_deleted._Worksheet__rows)
        soon_rows = len(self.ws_soon._Worksheet__rows)

        archived_file_exists = os.path.isfile(SAVE_SRC+archived_file)
        deleted_file_exists = os.path.isfile(SAVE_SRC+deleted_file)
        soon_file_exists = os.path.isfile(SAVE_SRC+soon_file)
        emails_addresses = []
        if MANAGERS:
            if USE_ESTABLISHMENT:
                emails_addresses = self.CONCERNED_MANAGERS_EMAILS
            else:
                for name, email in MANAGERS:
                    emails_addresses.append(email)
        subject = "[%s] %s" % (TITLE_SITE, _(u"The obsolete videos on Pod"))
        content = self.get_email_message(
                video,
                manager=to_manager)
        emails_addresses = [video.owner.email] if video else emails_addresses
        email = EmailMultiAlternatives(
                subject,
                content['plain_text'],
                DEFAULT_FROM_EMAIL,
                emails_addresses)
        email.attach_alternative(content['html'], "text/html")

        if to_manager:
            # si les fichiers existent et au moins une vidéo
            # obsolète trouvée
            if archived_file_exists and archived_rows > 1:
                email.attach_file(SAVE_SRC+archived_file)
            if deleted_file_exists and deleted_rows > 1:
                email.attach_file(SAVE_SRC+deleted_file)
            if soon_file_exists and soon_rows > 1:
                email.attach_file(SAVE_SRC+soon_file)
            # Envoie de mail seulement si on a au moins une pièce jointe
            if email.attachments:
                email.send()
        if not to_manager:
            email.send()
