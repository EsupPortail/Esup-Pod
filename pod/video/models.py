from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import get_language
from django.template.defaultfilters import slugify
from django.contrib.auth.models import Group
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


VIDEOS_DIR = getattr(
    settings, 'VIDEOS_DIR', 'videos')
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


def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


def get_storage_path(instance, filename):
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


class Video(models.Model):
    video = models.FileField(
        _('Video'),  upload_to=get_storage_path, max_length=255)

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
        _('Overview'), null=True, upload_to=get_storage_path,
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
        Group, blank=True, verbose_name=_('Goups'))
    password = models.CharField(
        _('password'),
        help_text=_(
            u'Viewing this video will not be possible without this password.'),
        max_length=50, blank=True, null=True)
    tags = TagField()

    def save(self, *args, **kwargs):
        tags = remove_accents(self.tags)
        print(self.tags, type(self.tags), tags)
        self.tags = tags
        super(Video, self).save(*args, **kwargs)

    def duration_in_time(self):
        return time.strftime('%H:%M:%S', time.gmtime(self.duration))

    duration_in_time.short_description = _('Duration')
    duration_in_time.allow_tags = True


class ViewCount(models.Model):
    video = models.ForeignKey(Video)
    date = models.DateField(
        _(u'Date'), auto_now=True)
    count = models.IntegerField(
        _('Number of view'), default=0, editable=False)
