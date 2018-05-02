"""
Custom Model for filepicker
Override File and Image models from file_picker

django-file-picker : 0.9.1.
"""
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User as Owner

import os
import logging
logger = logging.getLogger(__name__)


class UserDirectory(models.Model):
    name = models.CharField(_('Name'), max_length=255)
    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name='children')
    owner = models.ForeignKey(Owner, verbose_name=_('Owner'))

    class Meta:
        unique_together = (('name', 'parent', 'owner'),)
        verbose_name = _('User directory')
        verbose_name_plural = _('User directories')

    def clean(self):
        if self == self.parent:
            raise ValidationError('A directory cannot be its own parent.')
        if self.name == 'Home':
            same_home = UserDirectory.objects.filter(
                owner=self.owner, name='Home')
            if same_home:
                raise ValidationError(
                    'A user cannot have have multiple home directories.')

    def __str__(self):
        return '{0}'.format(self.name)

    def get_path(self, path=''):
        path = path
        if self.parent:
            path = os.path.join(self.name, path)
            return self.parent.get_path(path)
        else:
            return os.path.join(self.name, path)


@receiver(post_save, sender=Owner)
def create_owner_directory(sender, instance, created, **kwargs):
    if created:
        try:
            UserDirectory.objects.create(owner=instance, name='Home')
        except Exception as e:
            msg = '\n Create owner directory ***** Error:{0}'.format(e)
            msg += '\n{0}'.traceback.format_exc()
            logger.error(msg)
            print(msg)


def get_upload_path(instance, filename):
    if instance.created_by.owner:
        user_hash = instance.created_by.owner.hashkey
        return 'files/{0}/{1}/{2}/'.format(
            user_hash,
            instance.directory.get_path(),
            filename)
    else:
        return 'files/{0}/{1}/{2}/'.format(
            instance.created_by.username,
            instance.directory.get_path(),
            filename)


class BaseFileModel(models.Model):
    name = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=16, blank=True)
    date_created = models.DateTimeField()
    date_modified = models.DateTimeField()
    created_by = models.ForeignKey(
        Owner,
        related_name='%(app_label)s_%(class)s_created',
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
        if not self.name or self.name == "":
            self.name = os.path.basename(path)
        return super(BaseFileModel, self).save(**kwargs)

    def __str__(self):
        return '{0}'.format(
            self.name, self.created_by.username)


class CustomFileModel(BaseFileModel):
    directory = models.ForeignKey(UserDirectory)
    file = models.FileField(upload_to=get_upload_path, max_length=255)

    class Meta:
        verbose_name = _('File')
        verbose_name_plural = _('Files')

    def clean(self):
        if self.file:
            name, ext = os.path.splitext(self.file.name)
            if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                raise ValidationError(u'Image not allowed.')

    def delete(self):
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super(CustomFileModel, self).delete()


class CustomImageModel(BaseFileModel):
    directory = models.ForeignKey(UserDirectory)
    file = models.ImageField(upload_to=get_upload_path, max_length=255)

    class Meta:
        verbose_name = _('Image')
        verbose_name_plural = _('Images')

    def clean(self):
        if self.file:
            name, ext = os.path.splitext(self.file.name)
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                raise ValidationError(u'Must be a image.')

    def delete(self):
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super(CustomImageModel, self).delete()
