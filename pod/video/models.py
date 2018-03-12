from django.db import models
from django.db import connection
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language
from django.template.defaultfilters import slugify
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.apps import apps
try:
    from filepicker.models import CustomImageModel
except ImportError:
    pass
try:
    from pod.authentication.models import Owner
except ImportError:
    from django.contrib.auth.models import User as Owner

from datetime import datetime
from ckeditor.fields import RichTextField
from tagging.fields import TagField

import os
import time
import unicodedata

import logging
logger = logging.getLogger(__name__)

FILEPICKER = True if apps.is_installed('filepicker') else False
VIDEOS_DIR = getattr(
    settings, 'VIDEOS_DIR', 'videos')
FILES_DIR = getattr(
    settings, 'FILES_DIR', 'files')
MAIN_LANG_CHOICES = getattr(
    settings, 'MAIN_LANG_CHOICES', (('fr', _('French')),))
CURSUS_CODES = getattr(
    settings, 'CURSUS_CODES', (
        ('0', _("None / All")),
        ('L', _("Bachelor’s Degree")),
        ('M', _("Master’s Degree")),
        ('D', _("Doctorate")),
        ('1', _("Other"))
    ))
DEFAULT_TYPE_ID = getattr(
    settings, 'DEFAULT_TYPE_ID', 1)

LICENCE_CHOICES = getattr(
    settings, 'LICENCE_CHOICES', (
        ('BY', _("Attribution")),
        ('BY ND', _("Attribution + Pas de Modification")),
        ('BY NC ND', _(
            "Attribution + Pas d’Utilisation Commerciale + Pas de Modification"
        )),
        ('BY NC', _("Attribution + Pas d’Utilisation Commerciale")),
        ('BY NC SA',
            _(
                "Attribution + Pas d’Utilisation Commerciale + "
                + "Partage dans les mêmes conditions"
            )),
        ('BY SA', _(
            "Attribution + Partage dans les mêmes conditions"))
    ))

# FUNCTIONS


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


def get_storage_path_video(instance, filename):
    """ Get the storage path. Instance needs to implement owner """
    fname, dot, extension = filename.rpartition('.')
    try:
        fname.index("/")
        return os.path.join(VIDEOS_DIR, instance.owner.hashkey,
                            '%s/%s.%s' % (os.path.dirname(fname),
                                          slugify(os.path.basename(fname)),
                                          extension))
    except ValueError:
        return os.path.join(VIDEOS_DIR, instance.owner.hashkey,
                            '%s.%s' % (slugify(fname), extension))


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


def get_nextautoincrement(mymodel):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT Auto_increment FROM information_schema.tables "
        + "WHERE table_name='%s';" %
        mymodel._meta.db_table)
    row = cursor.fetchone()
    cursor.close()
    return row[0]

# MODELS


class Channel(models.Model):
    title = models.CharField(_('Title'), max_length=100, unique=True)
    slug = models.SlugField(
        _('Slug'), unique=True, max_length=100,
        help_text=_(
            u'Used to access this instance, the "slug" is a short label '
            + 'containing only letters, numbers, underscore or dash top.'))
    description = RichTextField(_('Description'),
                                config_name='complete', blank=True)
    # add headband
    if FILEPICKER:
        headband = models.ForeignKey(CustomImageModel,
                                     blank=True, null=True,
                                     verbose_name=_('Headband'))
    else:
        headband = models.ImageField(
            _('Headband'), null=True, upload_to=get_upload_path_files,
            blank=True, max_length=255)
    color = models.CharField(
        _('Background color'), max_length=10, blank=True, null=True)
    style = models.TextField(_('Extra style'), null=True, blank=True)
    owners = models.ManyToManyField(
        Owner, related_name='owners_channels', verbose_name=_('Owners'),
        blank=True)
    users = models.ManyToManyField(
        Owner, related_name='users_channels', verbose_name=_('Users'),
        blank=True)
    visible = models.BooleanField(
        verbose_name=_('Visible'),
        help_text=_(
            u'If checked, the channel appear in a list of available '
            + 'channels on the platform.'),
        default=False)

    class Meta:
        ordering = ['title']
        verbose_name = _('Channel')
        verbose_name_plural = _('Channels')

    def __str__(self):
        return "%s" % (self.title)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Channel, self).save(*args, **kwargs)


class Theme(models.Model):
    parentId = models.ForeignKey('self', null=True, blank=True)
    title = models.CharField(_('Title'), max_length=100, unique=True)
    slug = models.SlugField(
        _('Slug'), unique=True, max_length=100,
        help_text=_(
            u'Used to access this instance, the "slug" is a short label '
            + 'containing only letters, numbers, underscore or dash top.'))
    description = models.TextField(null=True, blank=True)
    if FILEPICKER:
        headband = models.ForeignKey(CustomImageModel,
                                     blank=True, null=True,
                                     verbose_name=_('Headband'))
    else:
        headband = models.ImageField(
            _('Headband'), null=True, upload_to=get_upload_path_files,
            blank=True, max_length=255)

    channel = models.ForeignKey(
        'Channel', related_name='themes', verbose_name=_('Channel'))

    def __str__(self):
        return "%s: %s" % (self.channel.title, self.title)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Theme, self).save(*args, **kwargs)

    class Meta:
        ordering = ['title']
        verbose_name = _('Theme')
        verbose_name_plural = _('Themes')


class Type(models.Model):
    title = models.CharField(_('Title'), max_length=100, unique=True)
    slug = models.SlugField(
        _('Slug'), unique=True, max_length=100,
        help_text=_(
            u'Used to access this instance, the "slug" is a short label '
            + 'containing only letters, numbers, underscore or dash top.'))
    description = models.TextField(null=True, blank=True)
    if FILEPICKER:
        icon = models.ForeignKey(CustomImageModel,
                                 blank=True, null=True,
                                 verbose_name=_('Icon'))
    else:
        icon = models.ImageField(
            _('Icon'), null=True, upload_to=get_upload_path_files,
            blank=True, max_length=255)

    def __str__(self):
        return "%s" % (self.title)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Type, self).save(*args, **kwargs)

    class Meta:
        ordering = ['title']
        verbose_name = _('Type')
        verbose_name_plural = _('Types')


class Discipline(models.Model):
    title = models.CharField(_('title'), max_length=100, unique=True)
    slug = models.SlugField(
        _('slug'), unique=True, max_length=100,
        help_text=_(
            u'Used to access this instance, the "slug" is a short label '
            + 'containing only letters, numbers, underscore or dash top.'))
    description = models.TextField(null=True, blank=True)
    if FILEPICKER:
        icon = models.ForeignKey(CustomImageModel,
                                 blank=True, null=True,
                                 verbose_name=_('Icon'))
    else:
        icon = models.ImageField(
            _('Icon'), null=True, upload_to=get_upload_path_files,
            blank=True, max_length=255)

    def __str__(self):
        return "%s" % (self.title)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Discipline, self).save(*args, **kwargs)

    class Meta:
        ordering = ['title']
        verbose_name = _('Discipline')
        verbose_name_plural = _('Disciplines')


class Video(models.Model):
    video = models.FileField(
        _('Video'),  upload_to=get_storage_path_video, max_length=255)

    allow_downloading = models.BooleanField(
        _('allow downloading'), default=False)
    is_360 = models.BooleanField(_('video 360'), default=False)
    title = models.CharField(_('Title'), max_length=250)
    slug = models.SlugField(_('Slug'), unique=True, max_length=255,
                            help_text=_(
                                'Used to access this instance, the "slug" is '
                                + 'a short label containing only letters, '
                                + 'numbers, underscore or dash top.'),
                            editable=False)
    owner = models.ForeignKey(Owner, verbose_name=_('Owner'))
    date_added = models.DateField(_('Date added'), default=datetime.now)
    date_evt = models.DateField(
        _(u'Date of event'), default=datetime.now, blank=True, null=True)
    description = RichTextField(
        _('Description'), config_name='complete', blank=True)
    cursus = models.CharField(
        _('University course'), max_length=1,
        choices=CURSUS_CODES, default="0")
    main_lang = models.CharField(
        _('Main language'), max_length=2,
        choices=MAIN_LANG_CHOICES, default=get_language())
    overview = models.ImageField(
        _('Overview'), null=True, upload_to=get_upload_path_files,
        blank=True, max_length=255, editable=False)
    duration = models.IntegerField(
        _('Duration'), default=0, editable=False, blank=True)
    infoVideo = models.TextField(null=True, blank=True, editable=False)
    is_draft = models.BooleanField(
        verbose_name=_('Draft'),
        help_text=_(
            u'If this box is checked, '
            + 'the video will be visible and accessible only by you.'),
        default=True)
    is_restricted = models.BooleanField(
        verbose_name=_(u'Restricted access'),
        help_text=_(
            u'If this box is checked, '
            + 'the video will only be accessible to authenticated users.'),
        default=False)
    restrict_access_to_groups = models.ManyToManyField(
        Group, blank=True, verbose_name=_('Goups'),
        help_text=_(u'Select one or more groups who can access to this video'))
    password = models.CharField(
        _('password'),
        help_text=_(
            u'Viewing this video will not be possible without this password.'),
        max_length=50, blank=True, null=True)
    tags = TagField(help_text=_(
        u'Separate tags with spaces, '
        + 'enclose the tags consist of several words in quotation marks.'),
        verbose_name=_('Tags'))
    if FILEPICKER:
        thumbnail = models.ForeignKey(CustomImageModel,
                                      blank=True, null=True,
                                      verbose_name=_('Thumbnails'))
    else:
        thumbnail = models.ImageField(
            _('Thumbnail'), null=True, upload_to=get_upload_path_files,
            blank=True, max_length=255)

    type = models.ForeignKey(Type, verbose_name=_('Type'),
                             default=DEFAULT_TYPE_ID)
    discipline = models.ManyToManyField(
        Discipline, blank=True, verbose_name=_('Disciplines'))
    channel = models.ManyToManyField(
        Channel, verbose_name=_('Channels'), blank=True)
    theme = models.ManyToManyField(
        Theme, verbose_name=_('Themes'), blank=True)

    licence = models.CharField(
        _('Licence'), max_length=8,
        choices=LICENCE_CHOICES, blank=True, null=True)

    def save(self, *args, **kwargs):
        newid = -1
        if not self.id:
            try:
                newid = get_nextautoincrement(Video)
            except Exception:
                try:
                    newid = Video.objects.latest('id').id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = '%04d' % newid
        self.slug = "%s-%s" % (newid, slugify(self.title))
        self.tags = remove_accents(self.tags)
        super(Video, self).save(*args, **kwargs)

    def __str__(self):
        return "%s - %s" % ('%04d' % self.id, self.title)

    def get_viewcount(self):
        count_sum = self.viewcount_set.all().aggregate(Sum('count'))
        if count_sum['count__sum'] is None:
            return 0
        return count_sum['count__sum']

    def duration_in_time(self):
        return time.strftime('%H:%M:%S', time.gmtime(self.duration))

    duration_in_time.short_description = _('Duration')
    duration_in_time.allow_tags = True


class ViewCount(models.Model):
    video = models.ForeignKey(Video)
    date = models.DateField(
        _(u'Date'), default=datetime.now)
    count = models.IntegerField(
        _('Number of view'), default=0, editable=False)
