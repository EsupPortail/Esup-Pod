from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.flatpages.models import FlatPage
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify
from django.db import connection

import os

FILES_DIR = getattr(
    settings, 'FILES_DIR', 'files')


def get_nextautoincrement(model):
    cursor = connection.cursor()
    cursor.execute(
        'SELECT Auto_increment FROM information_schema.tables ' +
        'WHERE table_name="{0}";'.format(model._meta.db_table)
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


class CustomFileModel(models.Model):
    file = models.ImageField(
        _('Image'), null=True, upload_to=get_upload_path_files,
        blank=True, max_length=255)


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

    def __str__(self):
        return "%s - %s" % (self.id, self.title)

    def clean(self):
        if self.url is None and self.page is None:
            raise ValidationError(
                _('You must give an URL or a page to link the link'))
