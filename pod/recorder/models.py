import os
import importlib

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from django.core.exceptions import ValidationError


RECORDER_TYPE = getattr(
    settings, 'RECORDER_TYPE',
    (
        ('video', _('Video')),
        ('audiovideocast', _('Audiovideocast')),
    )
)
DEFAULT_RECORDER_PATH = getattr(
    settings, 'DEFAULT_RECORDER_PATH',
    "/home/pod/files"
)
DEFAULT_RECORDER_USER_ID = getattr(
    settings, 'DEFAULT_RECORDER_USER_ID',
    1
)


class Recording(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True}, default=DEFAULT_RECORDER_USER_ID)
    title = models.CharField(_('title'), max_length=200, unique=True)
    source_file = models.FilePathField(
        path=DEFAULT_RECORDER_PATH, recursive=True)  # match="foo.*"
    type = models.CharField(
        max_length=50, choices=RECORDER_TYPE, default=RECORDER_TYPE[0][0])
    commentaire = models.TextField(_('Comment'), blank=True, default="")
    date_added = models.DateTimeField(
        'date added', default=timezone.now, editable=False)

    def __str__(self):
        return "%s" % (self.title)

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
    # if created and os.path.exists(instance.source_file):
    if os.path.exists(instance.source_file):
        mod = importlib.import_module(
            '%s.plugins.type_%s' %(__package__,instance.type))
        mod.process(instance)


class RecordingFile(models.Model):
    file = models.FileField(upload_to='uploads/')
    type = models.CharField(
        max_length=50, choices=RECORDER_TYPE, default=RECORDER_TYPE[0][0])

    class Meta:
        verbose_name = _("Recording file")
        verbose_name_plural = _("Recording files")


@receiver(post_save, sender=RecordingFile)
def process_recording_file(sender, instance, created, **kwargs):
    if created:
        print("move upload file and create recording")
