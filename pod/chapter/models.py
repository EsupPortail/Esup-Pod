import time

from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _

from pod.video.models import Video
from pod.main.models import get_nextautoincrement


class Chapter(models.Model):
    video = models.ForeignKey(Video, verbose_name=_("video"), on_delete=models.CASCADE)
    title = models.CharField(_("title"), max_length=100)
    slug = models.SlugField(
        _("slug"),
        unique=True,
        max_length=105,
        help_text=_(
            'Used to access this instance, the "slug" is a short'
            + " label containing only letters, numbers, underscore"
            + " or dash top."
        ),
        editable=False,
    )
    time_start = models.PositiveIntegerField(
        _("Start time"),
        default=0,
        help_text=_("Start time of the chapter, in seconds."),
    )

    class Meta:
        verbose_name = _("Chapter")
        verbose_name_plural = _("Chapters")
        ordering = ["time_start"]
        unique_together = (
            "title",
            "time_start",
            "video",
        )

    def clean(self):
        msg = list()
        msg = self.verify_title_items() + self.verify_time()
        msg = msg + self.verify_overlap()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_title_items(self):
        msg = list()
        if (
            not self.title
            or self.title == ""
            or len(self.title) < 2
            or len(self.title) > 100
        ):
            msg.append(_("Please enter a title from 2 to 100 characters."))
        if len(msg) > 0:
            return msg
        return list()

    def verify_time(self):
        """Check that start time is included inside video duration."""
        msg = list()
        if (
            self.time_start == ""
            or self.time_start < 0
            or self.time_start >= self.video.duration
        ):
            msg.append(
                _(
                    "Please enter a correct start field between 0 and "
                    + "{0}".format(self.video.duration - 1)
                )
            )
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
                if self.time_start == element.time_start:
                    msg.append(
                        _(
                            "There is an overlap with the chapter "
                            + "{0}, please change start and/or "
                            + "end values."
                        ).format(element.title)
                    )
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
                    newid = Chapter.objects.latest("id").id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = "{0}".format(newid)
        self.slug = "{0}-{1}".format(newid, slugify(self.title))
        super(Chapter, self).save(*args, **kwargs)

    @property
    def chapter_in_time(self):
        return time.strftime("%H:%M:%S", time.gmtime(self.time_start))

    chapter_in_time.fget.short_description = _("Start time")

    @property
    def sites(self):
        return self.video.sites

    def __str__(self):
        return "Chapter: {0} - video: {1}".format(self.title, self.video)
