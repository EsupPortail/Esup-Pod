from django.core.exceptions import ValidationError
from django.db import models
from django.db import connection
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from pod.video.models import Video


def get_nextautoincrement(model):
    cursor = connection.cursor()
    cursor.execute(
        'SELECT Auto_increment FROM information_schema.tables ' +
        'WHERE table_name="{0}";'.format(model._meta.db_table)
    )
    row = cursor.fetchone()
    cursor.close()
    return row[0]


class Chapter(models.Model):
    video = models.ForeignKey(Video, verbose_name=_('video'))
    title = models.CharField(_('title'), max_length=100)
    slug = models.SlugField(
        _('slug'),
        unique=True,
        max_length=105,
        help_text=_(
            u'Used to access this instance, the "slug" is a short label ' +
            'containing only letters, number, underscore or dash top.'),
        editable=False)
    time_start = models.PositiveIntegerField(
        _('Start time'),
        default=0,
        help_text=_(u'Start time of the chapter, in seconds.'))
    time_end = models.PositiveIntegerField(
        _('End time'),
        default=1,
        help_text=_(u'End time of the chapter, in seconds.'))

    class Meta:
        verbose_name = _('Chapter')
        verbose_name_plural = _('Chapters')
        ordering = ['time_start']
        unique_together = ('title', 'time_start', 'time_end', )

    def clean(self):
        msg = list()
        msg = self.verify_title_items() + self.verify_time()
        msg = msg + self.verify_overlap()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_title_items(self):
        msg = list()
        if (not self.title or self.title == '' or len(self.title) < 2 or
                len(self.title) > 100):
            msg.append(_('Please enter a title from 2 to 100 characters.'))
        if len(msg) > 0:
            return msg
        return list()

    def verify_time(self):
        msg = list()
        if self.time_start > self.time_end:
            msg.append(
                _('The value of the time start field is greater than the ' +
                    'value of the end time field.'))
        elif self.time_end > self.video.duration:
            msg.append(_('The value of time end field is greater than the ' +
                         'video duration.'))
        elif self.time_start == self.time_end:
            msg.append(_('Time end field and time start field can\'t ' +
                         'be equal.'))
        if len(msg) > 0:
            return msg
        return list()

    def verify_overlap(self):
        msg = list()
        instance = None
        if self.slug:
            instance = Chapter.objects.get(slug=self.slug)
        list_chapter = Chapter.objects.filter(video=self.video)
        if instance:
            list_chapter = list_chapter.exclude(id=instance.id)
        if len(list_chapter) > 0:
            for element in list_chapter:
                if not ((self.time_start < element.time_start and
                         self.time_end <= element.time_start) or
                        (self.time_start >= element.time_end and
                         self.time_end > element.time_end)):
                    msg.append(_('There is an overlap with ' +
                                 'the chapter {0}, '.format(element.title) +
                                 'please change time start and/or ' +
                                 'time end values.'))
            if len(msg) > 0:
                return msg
        return list()

    def save(self, *args, **kwargs):
        newid = -1
        if not self.id:
            try:
                newid = get_nextautoincrement(Chapter)
            except Exception:
                try:
                    newid = Chapter.objects.latest('id').id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = '{0}'.format(newid)
        self.slug = '{0}-{1}'.format(newid, slugify(self.title))
        super(Chapter, self).save(*args, **kwargs)

    def __str__(self):
        return u'Chapter: {0} - video: {0}'.format(self.title, self.video)
