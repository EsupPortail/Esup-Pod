from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from pod.video.models import Video


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
    time = models.PositiveIntegerField(
        _('Start time'),
        default=0,
        help_text=_(u'Start time of the chapter, in seconds.'))

    class Meta:
        verbose_name = _('Chapter')
        verbose_name_plural = _('Chapters')
        ordering = ['time']

    def clean(self):
        msg = list()
        msg = self.verify_start_title_items() + self.verify_overlap()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_start_title_items(self):
        msg = list()
        if (not self.title or self.title == '' or len(self.title) < 2 or
                len(self.title) > 100):
            msg.append(_('Please enter a title from 2 to 100 characters.'))
        if (self.time == '' or self.time < 0 or
                self.time >= self.video.duration):
            msg.append(_('Please enter a correct start field between 0 and ' +
                         '{0}.'.format(self.video.duration - 1)))
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
                if self.time == element.time:
                    msg.append(
                        _('There is an overlap with the chapter {0}, please' +
                          ' change start and/or end values.'.format(
                              element.title)))
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
    			except:
    				newid = 1
    	else:
    		newid = self.id
    	newid = '{0}'.format(newid)
    	self.slug = '{0}-{0}'.format(newid, slugify(self.title))
    	super(Chapter, self).save(*args, **kwargs)

    def __str__(self):
    	return u'Chapter: {0} - video: {0}'.format(self.title, self.video)
