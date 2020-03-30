import os
import importlib

from ckeditor.fields import RichTextField
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from django.core.exceptions import ValidationError
from select2 import fields as select2_fields

from pod.video.models import Type

RECORDER_TYPE = getattr(
    settings, 'RECORDER_TYPE',
    (
        ('video', _('Video')),
        ('audiovideocast', _('Audiovideocast')),
    )
)
DEFAULT_RECORDER_PATH = getattr(
    settings, 'DEFAULT_RECORDER_PATH',
    "/data/ftp-pod/ftp/"
)
DEFAULT_RECORDER_USER_ID = getattr(
    settings, 'DEFAULT_RECORDER_USER_ID',
    1
)
DEFAULT_RECORDER_ID = getattr(
    settings, 'DEFAULT_RECORDER_ID',
    1
)
PUBLIC_RECORD_DIR = getattr(
    settings, 'PUBLIC_RECORD_DIR',
    "records"
)


class Recorder(models.Model):
    # Recorder name
    name = models.CharField(_('name'), max_length=200, unique=True)
    # Description of the recorder
    description = RichTextField(_('description'), config_name='complete',
                                blank=True)
    # IP address of the recorder
    address_ip = models.GenericIPAddressField(_('Address IP'), unique=True,
                                              help_text=_(
                                                  'IP address of the recorder.'
    ))
    # Salt for
    salt = models.CharField(_('salt'), max_length=50, blank=True,
                            help_text=_('Recorder salt.'))
    # Manager of the recorder who received mails
    user = select2_fields.ForeignKey(
        User, on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True}, help_text=_(
            'Manager of this recorder. This manager will receive recorder '
            'emails and he will be the owner of the published videos. If no '
            'user is selected, this recorder will use manual assign system.'),
        verbose_name=_('User'), null=True, blank=True)
    # Default type of published videos by this recorder
    type = models.ForeignKey(
        Type, on_delete=models.CASCADE,
        help_text=_('Video type by default.'))

    recording_type = models.CharField(_('Recording Type'), max_length=50,
                                      choices=RECORDER_TYPE,
                                      default=RECORDER_TYPE[0][0])
    # Directory name where videos of this recorder are published
    directory = models.CharField(_('Publication directory'), max_length=50,
                                 unique=True, help_text=_(
        'Basic directory containing the videos published by the recorder.')
    )

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
    recorder = models.ForeignKey(Recorder,
                                 on_delete=models.CASCADE,
                                 verbose_name=_('Recorder'),
                                 default=DEFAULT_RECORDER_ID,
                                 help_text=_('Recorder that made this '
                                             'recording.'))
    user = select2_fields.ForeignKey(User, on_delete=models.CASCADE,
                                     limit_choices_to={'is_staff': True},
                                     default=DEFAULT_RECORDER_USER_ID,
                                     help_text=_
                                     ("User who has made the recording"))
    title = models.CharField(_('title'), max_length=200, unique=True)
    type = models.CharField(_('Recording Type'), max_length=50,
                            choices=RECORDER_TYPE,
                            default=RECORDER_TYPE[0][0])
    source_file = models.FilePathField(
        path=DEFAULT_RECORDER_PATH, unique=True,
        recursive=True)
    comment = models.TextField(_('Comment'), blank=True, default="")
    date_added = models.DateTimeField('date added', default=timezone.now,
                                      editable=False)

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = _("Recording")
        verbose_name_plural = _("Recordings")

    def save(self, *args, **kwargs):
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
        if not self.source_file:
            msg.append(_('Please specify a source file.'))
        elif not os.path.exists(self.source_file):
            msg.append(_("Source file doesn't exists"))
        return msg


@receiver(post_save, sender=Recording)
def process_recording(sender, instance, created, **kwargs):
    if created and os.path.exists(instance.source_file):
        mod = importlib.import_module(
            '%s.plugins.type_%s' % (__package__, instance.type))
        mod.process(instance)


class RecordingFileTreatment(models.Model):
    file = models.FilePathField(path=DEFAULT_RECORDER_PATH, recursive=True,
                                unique=True, help_text=_(
                                    'Source file of the published video.'))
    file_size = models.BigIntegerField(_('File size'), default=0)
    recorder = models.ForeignKey(Recorder, on_delete=models.CASCADE,
                                 verbose_name=_('Recorder'), null=True,
                                 help_text=_(
                                     'Recorder that made this recording.'))
    date_added = models.DateTimeField(_('Date added'), default=timezone.now,
                                      editable=True)
    require_manual_claim = models.BooleanField(_('Require manual claim ?'),
                                               default=False,
                                               help_text=_(
                                                   'Has this recording file '
                                                   'require a manual claim '
                                                   'by a user ?'))
    email_sent = models.BooleanField(_('Email sent ?'), default=False,
                                     help_text=_(
                                         'Has an email been sent to the '
                                         'manager of the concerned recorder '
                                         '?'))
    date_email_sent = models.DateTimeField(_('Date email sent'), blank=True,
                                           null=True, editable=False)
    type = models.CharField(max_length=50, choices=RECORDER_TYPE,
                            default=RECORDER_TYPE[0][0])

    def filename(self):
        return os.path.basename(self.file)

    def publicfileurl(self):
        return os.path.join(settings.MEDIA_URL, PUBLIC_RECORD_DIR,
                            self.recorder.directory,
                            os.path.basename(self.file))

    class Meta:
        verbose_name = _("Recording file treatment")
        verbose_name_plural = _("Recording file treatments")


class RecordingFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    recorder = models.ForeignKey(Recorder,
                                 on_delete=models.CASCADE,
                                 default=DEFAULT_RECORDER_ID,
                                 verbose_name=_('Recorder'),
                                 help_text=_('Recorder that made this '
                                             'recording.'))

    class Meta:
        verbose_name = _("Recording file")
        verbose_name_plural = _("Recording files")


@receiver(post_save, sender=RecordingFile)
def process_recording_file(sender, instance, created, **kwargs):
    if created and instance.file and os.path.isfile(instance.file.path):
        # deplacement du fichier source vers destination
        create_recording(instance)


def create_recording(recordingFile):
    new_path = os.path.join(
        DEFAULT_RECORDER_PATH, os.path.basename(recordingFile.file.path))
    nom, ext = os.path.splitext(os.path.basename(recordingFile.file.path))
    ext = ext.lower()
    os.rename(recordingFile.file.path, new_path)
    user = User.objects.get(id=DEFAULT_RECORDER_USER_ID)
    Recording.objects.create(
        user=user,
        title=nom,
        source_file=new_path,
        recorder=recordingFile.recorder,
        type=recordingFile.recorder.recording_type
    )
