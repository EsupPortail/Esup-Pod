from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.flatpages.models import FlatPage
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.db import connection

import os
import mimetypes

FILES_DIR = getattr(
    settings, 'FILES_DIR', 'files')


def get_nextautoincrement(model):
    cursor = connection.cursor()
    cursor.execute(
        'SELECT Auto_increment FROM information_schema.tables ' +
        'WHERE table_name="{0}" AND table_schema=DATABASE();'
        .format(model._meta.db_table)
    )
    row = cursor.fetchone()
    cursor.close()
    return row[0]


def get_upload_path_files(instance, filename):
    fname, dot, extension = filename.rpartition('.')
    try:
        fname.index("/")
        return os.path.join(FILES_DIR,
                            '%s/%s.%s' % (os.path.dirname(fname),
                                          slugify(os.path.basename(fname)),
                                          extension))
    except ValueError:
        return os.path.join(FILES_DIR,
                            '%s.%s' % (slugify(fname), extension))


class CustomImageModel(models.Model):
    file = models.ImageField(
        _('Image'), null=True, upload_to=get_upload_path_files,
        blank=True, max_length=255)

    @property
    def file_type(self):
        filetype = mimetypes.guess_type(self.file.path)[0]
        if filetype is None:
            fname, dot, extension = self.file.path.rpartition('.')
            filetype = extension.lower()
        return filetype
    file_type.fget.short_description = _('Get the file type')

    @property
    def file_size(self):
        return os.path.getsize(self.file.path)
    file_size.fget.short_description = _('Get the file size')

    @property
    def name(self):
        return os.path.basename(self.file.path)
    name.fget.short_description = _('Get the file name')

    def file_exist(self):
        return (self.file and os.path.isfile(self.file.path))

    def __str__(self):
        return '%s (%s, %s)' % (self.name, self.file_type, self.file_size)


class CustomFileModel(models.Model):
    file = models.ImageField(
        _('Image'), null=True, upload_to=get_upload_path_files,
        blank=True, max_length=255)

    @property
    def file_type(self):
        filetype = mimetypes.guess_type(self.file.path)[0]
        if filetype is None:
            fname, dot, extension = self.file.path.rpartition('.')
            filetype = extension.lower()
        return filetype
    file_type.fget.short_description = _('Get the file type')

    @property
    def file_size(self):
        return os.path.getsize(self.file.path)
    file_size.fget.short_description = _('Get the file size')

    @property
    def name(self):
        return os.path.basename(self.file.path)
    name.fget.short_description = _('Get the file name')

    def file_exist(self):
        return (self.file and os.path.isfile(self.file.path))

    def __str__(self):
        return '%s (%s, %s)' % (self.name, self.file_type, self.file_size)


class LinkFooter(models.Model):
    title = models.CharField(_('Title'), max_length=250)
    order = models.PositiveSmallIntegerField(
        _('order'), default=1, blank=True, null=True)
    url = models.CharField(
        _('Web link'), blank=True, null=True, max_length=250,
        help_text=_('This field allows you to add an url.'))
    page = models.ForeignKey(
        FlatPage, blank=True, null=True,
        help_text=_('Select the page of Pod you want to link with.'))

    class Meta:
        ordering = ['order', 'title']
        verbose_name = _('bottom menu')
        verbose_name_plural = _('bottom menu')

    def get_url(self):
        if self.url:
            return self.url
        return self.page.url

    def __str__(self):
        return "%s - %s" % (self.id, self.title)

    def clean(self):
        if self.url is None and self.page is None:
            raise ValidationError(
                _('You must give an URL or a page to link the link'))
