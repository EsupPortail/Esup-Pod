"""
Custom Model for filepicker
Override File and Image models from file_picker

django-file-picker : 0.9.1.
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext as _
try:
    from pod.authentication.models import Owner
except ImportError:
    from django.contrib.auth.models import User as Owner

import os


class UserDirectory(models.Model):
    name = models.CharField(_('Name'), max_length=255)
    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name='children')
    owner = models.ForeignKey(Owner, verbose_name=_('Owner'))
    users = models.ManyToManyField(
        Owner,
        related_name='users_directory',
        verbose_name=_('Users directory'),
        blank=True)

    class Meta:
        verbose_name = _('User directory')
        verbose_name_plural = _('User directories')

    def __str__(self):
        return '{0}'.format(self.name)

    def get_path(self, path=''):
        path = path
        if self.parent:
            path = os.path.join(self.name, path)
            return self.parent.get_path(path)
        else:
            return os.path.join(self.name, path)


def get_upload_path(instance, filename):
    user_hash = instance.created_by.hashkey
    return 'files/{0}/{1}/{2}/'.format(
        user_hash,
        instance.directory.get_path(),
        filename
    )


class BaseFileModel(models.Model):
    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    file_size = models.PositiveIntegerField(
        null=True, blank=True)
    file_type = models.CharField(
        max_length=16, blank=True)
    date_created = models.DateTimeField()
    date_modified = models.DateTimeField()
    created_by = models.ForeignKey(
        Owner,
        related_name='%(app_label)s_%(class)s_created',
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    modified_by = models.ForeignKey(
        Owner,
        related_name='%(app_label)s_%(class)s_modified',
        null=True,
        blank=True,
        on_delete=models.CASCADE)

    class Meta:
        abstract = True
        ordering = ('-date_modified',)

    def save(self, **kwargs):
        now = timezone.now()
        if not self.pk:
            self.date_created = now
        self.date_modified = now
        try:
            self.file_size = self.file.size
        except OSError:
            pass
        path, ext = os.path.splitext(self.file.name)
        self.file_type = ext.lstrip('.').upper()
        return super(BaseFileModel, self).save(**kwargs)

    def __str__(self):
        return 'File: {0} - Owner: {1}'.format(self.name, self.created_by.user.username)


class CustomFileModel(BaseFileModel):
    directory = models.ForeignKey(UserDirectory)
    file = models.FileField(upload_to=get_upload_path, max_length=255)

    class Meta:
        verbose_name = _('File')
        verbose_name_plural = _('Files')


class CustomImageModel(BaseFileModel):
    directory = models.ForeignKey(UserDirectory)
    file = models.ImageField(upload_to=get_upload_path, max_length=255)

    class Meta:
        verbose_name = _('Image')
        verbose_name_plural = _('Images')
