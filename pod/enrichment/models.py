from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from ckeditor.fields import RichTextField
from pod.video.models import Video
if apps.is_installed('pod.filepicker'):
    from pod.filepicker.models import CustomImageModel
    from pod.filepicker.models import CustomFileModel
    FILEPICKER = True


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


class EnrichmentImage(models.Model):
    file = models.ImageField(
        _('Image'),
        null=True,
        upload_to=get_upload_path_files,
        blank=True,
        max_length=255)


class EnrichmentFile(models.Model):
    file = models.FileField(
        _('File'),
        null=True,
        upload_to=get_upload_path_files,
        blank=True,
        max_length=255)


class Enrichment(models.Model):

    ENRICH_CHOICES = (
        ('image', _("image")),
        ('richtext', _("richtext")),
        ('weblink', _("weblink")),
        ('document', _("document")),
        ('embed', _("embed")),
    )

    video = models.ForeignKey(Video, verbose_name=_('video'))
    title = models.CharField(_('title'), max_length=100)
    slug = models.SlugField(
        _('slug'),
        unique=True,
        max_length=105,
        help_text=_(u'Used to access this instance, the "slug" is a short ' +
                    'label containing only letters, numbers, underscore or dash top.'),
        editable=False)
    stop_video = models.BooleanField(
        _('Stop video'),
        default=False,
        help_text=_(u'The video will pause when displaying the enrichment.'))
    start = models.PositiveIntegerField(
        _('Start'),
        default=0,
        help_text=_('Start of enrichment display in seconds.'))
    end = models.PositiveIntegerField(
        _('End'),
        default=1,
        help_text=_('End of enrichment display in seconds.'))
    type = models.CharField(
        _('Type'), max_length=10, choices=ENRICH_CHOICES, null=True, blank=True)
    if FILEPICKER:
        image = models.ForeignKey(
            CustomImageModel, verbose_name=_('Image'), null=True, blank=True)
        document = models.ForeignKey(
            CustomFileModel,
            verbose_name=_('Document'),
            null=True,
            blank=True,
            help_text=_(u'Integrate an document (PDF, text, html)'))
    else:
        image = models.ForeignKey(
            EnrichmentImage, verbose_name=('Image'), null=True, blank=True)
        document = models.ForeignKey(
            EnrichmentFile,
            verbose_name=('Document'),
            null=True,
            blank=True,
            help_text=_(u'Integrate an document (PDF, text, html)'))
    richtext = RichTextField(_('Richtext'), config_name='complete', blank=True)
    weblink = models.URLField(
        _(u'Web link'), max_length=200, null=True, blank=True)
    embed = models.TextField(
        _('Embed'),
        max_length=300,
        null=True,
        blank=True,
        help_text=_(u'Integrate an external source.'))

    class Meta:
        verbose_name = _('Enrichment')
        verbose_name_plural = _('Enrichments')
        ordering = ['start']

    def clean(self):
        msg = list()
        msg = self.verify_end_start_item() + self.verify_all_fields() + \
            self.overlap()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_all_fields(self):
        msg = list()
        if (not self.title or self.title == '' or len(self.title) < 2 or
                len(self.title) > 100):
            msg.append(_('Please enter a title from 2 to 100 characters.'))
        if (self.start == '' or self.start < 0 or
                self.start >= self.video.duration):
            msg.append(_('Please enter a correct start field between 0 and ' +
                         '{0}.'.format(self.video.duration - 1)))
        if (not self.end or self.end == '' or self.end <= 0 or
                self.end > self.video.duration):
            msg.append(_('Please enter a correct end field between 1 and ' +
                         '{0}.'.format(self.video.duration)))
        if self.type == 'image' and not self.image:
            msg.append(_('Please enter a correct image.'))
        elif self.type == 'richtext' and not self.richtext:
            msg.append(_('Please enter a correct richtext.'))
        elif self.type == 'weblink' and not self.weblink:
            msg.append(_('Please enter a correct weblink.'))
        elif self.type == 'document' and not self.document:
            msg.append(_('Please enter a correct document.'))
        elif self.type == 'embed' and not self.embed:
            msg.append(_('Please enter a correct embed.'))
        elif not self.type:
            msg.append(_('Please enter a type in index field.'))

        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_end_start_item(self):
        msg = list()
        video = Video.objects.get(id=self.video.id)
        if self.start > self.end:
            msg.append(
                _('The value of the start field is greater than the value ' +
                  'of end field.'))
        if self.end > video.duration:
            msg.append(
                _('The value of end field is greater than the video duration.'))
        if self.start == self.end:
            msg.append(
                _('End field and start field can\'t be equal.'))

        if len(msg) > 0:
            return msg
        else:
            return list()

    def overlap(self):
        msg = list()
        instance = None
        if self.slug:
            instance = Enrichment.objects.get(slug=self.slug)
        list_enrichment = Enrichment.objects.filter(video=self.video)
        if instance:
            list_enrichment = list_enrichment.exclude(id=instance.id)
        if len(list_enrichment) > 0:
            for element in list_enrichment:
                if (not (self.start < element.start and
                         self.end <= element.start) or
                        (self.start >= element.end and
                         self.end > element.end)):
                    msg.append(
                        _('There is an overlap with ' +
                          'the enrichment {0}, '.format(element.title) +
                          'please change start and/or end values.'))
                if len(msg) > 0:
                    return msg
        return list()

        def save(self, *args, **kwargs):
            newid = -1
            if not self.id:
                try:
                    newid = get_nextautoincrement(Enrichment)
                except Exception:
                    try:
                        newid = Enrichment.objects.latest('id').id
                        newid += 1
                    except Exception:
                        newid = 1
            else:
                newid = self.id
            newid = '{0}'.format(newid)
            self.slug = '{0} - {1}'.format(newid, slugify(self.title))
            super(Enrichment, self).save(*args, **kwargs)

        def __str__(self):
            return u'Media : {0} - Video: {1}'.format(self.title, self.video)
