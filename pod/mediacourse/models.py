import os
import importlib

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from pod.video.models import Type
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from django.core.exceptions import ValidationError
from ckeditor.fields import RichTextField

RECORDER_TYPE = getattr(
    settings, 'RECORDER_TYPE',
    (
        ('mediacourse', _('Mediacourse')),
        ('video', _('Video')),
    )
)
DEFAULT_MEDIACOURSE_RECORDER_PATH = getattr(
    settings, 'DEFAULT_MEDIACOURSE_RECORDER_PATH',
    "/data/ftp-pod/ftp/"
)

class Recorder(models.Model):
    # Nom de l'enregistreur
    name = models.CharField(_('name'), max_length=200, unique=True)
    # Description facultative de l'enregistreur
    description = RichTextField(_('description'), config_name='complete', blank=True)
    # Adresse IP obligatoire de l'enregistreur
    address_ip = models.GenericIPAddressField(_('Address IP'), unique=True, help_text=_('IP address of the recorder.'))
    # Salt spécifique à cet enregistreur
    salt = models.CharField(_('salt'), max_length=50, blank=True, help_text=_('Mediacourse recorder salt.'))
    # Utilisateur dans Pod qui recevra les emails de la part de l'enregistreur et qui sera le propriétaire des vidéos publiées par cet enregistreur
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True}, help_text=_('Manager of this recorder. This manager will receive mediacourse recorder emails and he will be the owner of the published videos. If no user is seleected, this recorder will use manual assign system.'),
        verbose_name=_('User'), null=True,blank=True)
    # Type par défaut des vidéos publiées par cet enregistreur
    type = models.ForeignKey(
        Type, on_delete=models.CASCADE,
        help_text=_('Video type by default.'))
    # Nom du répertoire contenant les vidéos uploadées par cet enregistreur
    directory = models.CharField(_('Publication directory'), max_length=50, unique=True, help_text=_('Basic directory containing the videos published by the recorder.'))

    def __unicode__(self):
        return "%s - %s" % (self.name, self.address_ip)

    def __str__(self):
        return "%s - %s" % (self.name, self.address_ip)

    def ipunder(self):
        return self.address_ip.replace(".", "_")

    def save(self, *args, **kwargs):
        super(Recorder, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Recorder")
        verbose_name_plural = _("Recorders")
        ordering = ['name']

class Recording(models.Model):
    # Enregistreur ayant réalisé cet enregistrement
    recorder = models.ForeignKey(Recorder, on_delete=models.CASCADE, verbose_name=_('Recorder'), help_text=_('Recorder that made this recording.'))
    # Titre de l'enregistrement réalisé
    title = models.CharField(_('title'), max_length=200, unique=True)
    # Fichier source de la vidéo publiée par l'enregistreur (par défaut dans le répertoire configurée via DEFAULT_MEDIACOURSE_RECORDER_PATH)
    mediapath = models.FilePathField(_('Mediapath'), path=DEFAULT_MEDIACOURSE_RECORDER_PATH, recursive=True, unique=True, match=".*\.*$", help_text=_('Source file of the published video (mediapath).'))
    # Type d'enregistrement (à l'heure actuelle, cela ne peut-être que "mediacourse" ou "video")
    # Le type "mediacourse" signifie que la vidéo est positionnée dans un fichier ZIP, qui contient également les images de slides (en cas d'existence et de publication de celles-ci)
    type = models.CharField(max_length=50, choices=RECORDER_TYPE, default=RECORDER_TYPE[0][0], help_text=_('Recording type (video = MP4 file, mediacourse = ZIP file).'))
    # Commentaire (qui contiendra par la suite des informations sur l'encodage)
    comment = models.TextField(_('Comment'), blank=True, default="")
    # Date d'ajout de cet enregistrement
    date_added = models.DateTimeField(_('Date added'), default=timezone.now, editable=False)

    def __str__(self):
        return "%s" % (self.title)

    class Meta:
        verbose_name = _("Recording")
        verbose_name_plural = _("Recordings")

    def save(self, *args, **kwargs):
        if self.mediapath.endswith("zip"):
            self.type = 'mediacourse'
        else:
            self.type = 'video'
        super(Recording, self).save(*args, **kwargs)

    def clean(self):
        msg = list()
        msg = self.verify_attributs()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_attributs(self):
        msg = list()
        if not self.type:
            msg.append(_('Please specify a type.'))
        elif self.type not in dict(RECORDER_TYPE):
            msg.append(_('Please use the only type in type choices.'))
        if not self.mediapath:
            msg.append(_('Please specify a source file.'))
        elif not os.path.exists(self.mediapath):
            msg.append(_("Source file doesn't exists"))
        return msg

class Job(models.Model):
    # Fichier source de la vidéo publiée par l'enregistreur (par défaut dans le répertoire configurée via DEFAULT_MEDIACOURSE_RECORDER_PATH)
    mediapath = models.FilePathField(_('Mediapath'), path=DEFAULT_MEDIACOURSE_RECORDER_PATH, recursive=True, unique=True, match=".*\.*$", help_text=_('Source file of the published video (mediapath).'))
    # Taille du fichier uploadé
    file_size = models.IntegerField(_('File size'), default=0)
    # Date d'ajout
    date_added = models.DateTimeField(_('Date added'), default=timezone.now, editable=True)
    # Booléen permettant de savoir si un email a déjà été envoyé à l'utilisateur pour traiter cette vidéo
    email_sent = models.BooleanField(_('Email sent ?'), default=False, help_text=_('Has an email been sent to the manager of the concerned recorder ?'))
    # Date d'envoi du mail à l'utilisateur
    date_email_sent = models.DateTimeField(_('Date email sent'), blank=True, null=True, editable=False)

    def __str__(self):
        return "%s" % (self.mediapath)

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")

    def save(self, *args, **kwargs):
        super(Job, self).save(*args, **kwargs)

    def clean(self):
        msg = list()
        msg = self.verify_attributs()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_attributs(self):
        msg = list()
        if not self.mediapath:
            msg.append(_('Please specify a source file.'))
        elif not os.path.exists(self.mediapath):
            msg.append(_("Source file doesn't exists"))
        return msg


@receiver(post_save, sender=Recording)
def process_mediacourse(sender, instance, created, **kwargs):
    if created and os.path.exists(instance.mediapath):
        mod = importlib.import_module(
            '%s.plugins.type_%s' % (__package__, instance.type))
        mod.process(instance)
