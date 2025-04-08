"""Esup-Pod Video chapter models."""

import time

from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext as _

from pod.video.models import Video
from pod.video.utils import verify_field_length
from pod.main.models import get_nextautoincrement


class Chapter(models.Model):
    """Chapter model."""

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
        """Chapter Metadata."""

        verbose_name = _("Chapter")
        verbose_name_plural = _("Chapters")
        ordering = ["time_start"]
        unique_together = (
            "title",
            "time_start",
            "video",
        )

    def clean(self) -> None:
        """Check chapter fields validity."""
        msg = list()
        msg = verify_field_length(self.title) + self.verify_time()
        msg = msg + self.verify_overlap()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_time(self) -> list:
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
        return msg

    def verify_overlap(self) -> list:
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
        return msg

    def save(self, *args, **kwargs) -> None:
        """Save a chapter."""
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
    def chapter_in_time(self) -> str:
        return time.strftime("%H:%M:%S", time.gmtime(self.time_start))

    chapter_in_time.fget.short_description = _("Start time")

    @property
    def sites(self):
        """Get the related video sites."""
        return self.video.sites

    def __str__(self) -> str:
        return "Chapter: {0} - video: {1}".format(self.title, self.video)
