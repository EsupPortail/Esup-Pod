import base64

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from ckeditor.fields import RichTextField
from pod.video.models import Video
from pod.main.models import get_nextautoincrement
from select2 import fields as select2_fields

if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True
    from pod.podfile.models import CustomFileModel
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel

ROLE_CHOICES = getattr(
    settings, 'ROLE_CHOICES', (
        ('actor', _('actor')),
        ('author', _('author')),
        ('designer', _('designer')),
        ('consultant', _('consultant')),
        ('contributor', _('contributor')),
        ('editor', _('editor')),
        ('speaker', _('speaker')),
        ('soundman', _('soundman')),
        ('director', _('director')),
        ('writer', _('writer')),
        ('technician', _('technician')),
        ('voice-over', _('voice-over')),
    ))
KIND_CHOICES = getattr(
    settings, 'KIND_CHOICES', (
        ('subtitles', _('subtitles')),
        ('captions', _('captions')),
    ))
LANG_CHOICES = getattr(
    settings, 'LANG_CHOICES', (
        (' ', settings.PREF_LANG_CHOICES),
        ('----------', settings.ALL_LANG_CHOICES)
    ))
LANG_CHOICES_DICT = {key: value for key,
                     value in LANG_CHOICES[0][1] + LANG_CHOICES[1][1]}


class Contributor(models.Model):

    video = select2_fields.ForeignKey(Video, verbose_name=_('video'))
    name = models.CharField(_('lastname / firstname'), max_length=200)
    email_address = models.EmailField(
        _('mail'), null=True, blank=True, default='')
    role = models.CharField(
        _(u'role'), max_length=200, choices=ROLE_CHOICES, default='author')
    weblink = models.URLField(
        _(u'Web link'), max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = _('Contributor')
        verbose_name_plural = _('Contributors')

    def clean(self):
        msg = list()
        msg = self.verify_attributs() + self.verify_not_same_contributor()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_attributs(self):
        msg = list()
        if not self.name or self.name == '':
            msg.append(_('Please enter a name.'))
        elif len(self.name) < 2 or len(self.name) > 200:
            msg.append(_('Please enter a name from 2 to 200 caracters.'))
        if self.weblink and len(self.weblink) > 200:
            msg.append(
                _('You cannot enter a weblink with more than 200 caracters.'))
        if not self.role:
            msg.append(_('Please enter a role.'))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_not_same_contributor(self):
        msg = list()
        list_contributor = Contributor.objects.filter(video=self.video)
        if self.id:
            list_contributor = list_contributor.exclude(id=self.id)
        if len(list_contributor) > 0:
            for element in list_contributor:
                if self.name == element.name and self.role == element.role:
                    msg.append(
                        _('There is already a contributor with the same ' +
                          'name and role in the list.')
                    )
                    return msg
        return list()

    def __str__(self):
        return u'Video:{0} - Name:{1} - Role:{2}'.format(
            self.video, self.name, self.role)

    def get_base_mail(self):
        data = base64.b64encode(self.email_address.encode())
        return data

    def get_noscript_mail(self):
        return self.email_address.replace('@', "__AT__")


class Document(models.Model):
    video = select2_fields.ForeignKey(Video, verbose_name=_('Video'))
    document = models.ForeignKey(
        CustomFileModel,
        null=True,
        blank=True,
        verbose_name=_('Document')
    )

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')

    def clean(self):
        msg = list()
        msg = self.verify_document() + self.verify_not_same_document()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_document(self):
        msg = list()
        if not self.document:
            msg.append(_('Please enter a document.'))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_not_same_document(self):
        msg = list()
        list_doc = Document.objects.filter(video=self.video)
        if self.id:
            list_doc = list_doc.exclude(id=self.id)
        if len(list_doc) > 0:
            for element in list_doc:
                if self.document == element.document:
                    msg.append(
                        _('This document is already contained ' +
                          'in the list')
                    )
            if len(msg) > 0:
                return msg
        return list()

    def __str__(self):
        return u'Document: {0} - Video: {1}'.format(
            self.document.name,
            self.video)


class Track(models.Model):

    video = select2_fields.ForeignKey(Video, verbose_name=_('Video'))
    kind = models.CharField(
        _('Kind'),
        max_length=10,
        choices=KIND_CHOICES,
        default='subtitles'
    )
    lang = models.CharField(_('Language'), max_length=2, choices=LANG_CHOICES)
    src = models.ForeignKey(CustomFileModel,
                            blank=True,
                            null=True,
                            verbose_name=_('Subtitle file'))

    def get_label_lang(self):
        return "%s" % LANG_CHOICES_DICT[self.lang]

    class Meta:
        verbose_name = _('Track')
        verbose_name_plural = _('Tracks')

    def clean(self):
        msg = list()
        msg = self.verify_attributs() + self.verify_not_same_track()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_attributs(self):
        msg = list()
        if not self.kind:
            msg.append(_('Please enter a kind.'))
        elif self.kind != 'subtitles' and self.kind != 'captions':
            msg.append(_('Please enter a correct kind.'))
        if not self.lang:
            msg.append(_('Please enter a language.'))
        if not self.src:
            msg.append(_('Please specify a track file.'))
        elif 'vtt' not in self.src.file_type:
            msg.append(_('Only ".vtt" format is allowed.'))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_not_same_track(self):
        msg = list()
        list_track = Track.objects.filter(video=self.video)
        if self.id:
            list_track = list_track.exclude(id=self.id)
        if len(list_track) > 0:
            for element in list_track:
                if self.kind == element.kind and self.lang == element.lang:
                    msg.append(_('There is already a subtitle with the ' +
                                 'same kind and language in the list.'))
                    return msg
        return list()

    def __str__(self):
        return u'{0} - File: {1} - Video: {2}'.format(
            self.kind,
            self.src.name,
            self.video
        )


class Overlay(models.Model):

    POSITION_CHOICES = (
        ('top-left', _(u'top-left')),
        ('top', _(u'top')),
        ('top-right', _(u'top-right')),
        ('right', _(u'right')),
        ('bottom-right', _(u'bottom-right')),
        ('bottom', _(u'bottom')),
        ('bottom-left', _(u'bottom-left')),
        ('left', _(u'left')),
    )

    video = select2_fields.ForeignKey(Video, verbose_name=_('Video'))
    title = models.CharField(_('Title'), max_length=100)
    slug = models.SlugField(
        _('Slug'),
        unique=True,
        max_length=105,
        help_text=_('Used to access this instance, the "slug" is a short' +
                    ' label containing only letters, numbers, underscore' +
                    ' or dash top.'),
        editable=False

    )
    time_start = models.PositiveIntegerField(
        _('Start time'),
        default=1,
        help_text=_(u'Start time of the overlay, in seconds.')
    )
    time_end = models.PositiveIntegerField(
        _('End time'),
        default=2,
        help_text=_(u'End time of the overlay, in seconds.')
    )
    content = RichTextField(
        _('Content'),
        null=False,
        blank=False,
        config_name='complete'
    )
    position = models.CharField(
        _('Position'),
        max_length=100,
        null=True,
        blank=False,
        choices=POSITION_CHOICES,
        default='bottom-right',
        help_text=_(u'Position of the overlay.')
    )
    background = models.BooleanField(
        _('Show background'),
        default=True,
        help_text=_(u'Show the background of the overlay.')
    )

    class Meta:
        verbose_name = _('Overlay')
        verbose_name_plural = _('Overlays')
        ordering = ['time_start']

    def clean(self):
        msg = list()
        msg += self.verify_title_items()
        msg += self.verify_time_items()
        msg += self.verify_overlap()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_title_items(self):
        msg = list()
        if not self.title or self.title == '':
            msg.append(_('Please enter a title.'))
        elif len(self.title) < 2 or len(self.title) > 100:
            msg.append(_('Please enter a title from 2 to 100 characters.'))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_time_items(self):
        msg = list()
        if self.time_start > self.time_end:
            msg.append(
                _('The value of the time start field is greater than ' +
                  'the value of the end time field.'))
        elif self.time_end > self.video.duration:
            msg.append(_('The value of time end field is greater than the ' +
                         'video duration.'))
        elif self.time_start == self.time_end:
            msg.append(_('Time end field and time start field can\'t ' +
                         'be equal.'))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_overlap(self):
        msg = list()
        instance = None
        if self.slug:
            instance = Overlay.objects.get(slug=self.slug)
        list_overlay = Overlay.objects.filter(video=self.video)
        if instance:
            list_overlay = list_overlay.exclude(id=instance.id)
        if len(list_overlay) > 0:
            for element in list_overlay:
                if not (self.time_start < element.time_start and
                        self.time_end <= element.time_start or
                        self.time_start >= element.time_end and
                        self.time_end > element.time_end):
                    msg.append(_("There is an overlap with the overlay {0},"
                                 " please change time start and/or "
                                 "time end values.").format(element.title))
            if len(msg) > 0:
                return msg
        return list()

    def save(self, *args, **kwargs):
        newid = -1
        if not self.id:
            try:
                newid = get_nextautoincrement(Overlay)
            except Exception:
                try:
                    newid = Overlay.objects.latest('id').id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = '{0}'.format(newid)
        self.slug = '{0}-{1}'.format(newid, slugify(self.title))
        super(Overlay, self).save(*args, **kwargs)

    def __str__(self):
        return 'Overlay: {0} - Video: {1}'.format(self.title, self.video)
