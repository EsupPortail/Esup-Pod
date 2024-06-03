"""Esup-Pod speaker models."""

from django.db import models
from django.utils.translation import ugettext as _
from pod.video.models import Video


class Speaker(models.Model):
    """
    Speaker model.

    Attributes:
        firstname (CharField): firstname of speaker.
        lastname (CharField): lastname of speaker.
    """

    firstname = models.CharField(
        verbose_name=_("Firstname"),
        max_length=100
    )
    lastname = models.CharField(
        verbose_name=_("Lastname"),
        max_length=100
    )

    class Meta:
        ordering = ["lastname", "firstname"]
        verbose_name = _("Speaker")
        verbose_name_plural = _("Speakers")

    def __str__(self):
        return f"{self.lastname} {self.firstname}"


class Job(models.Model):
    """
    Job model.

    Attributes:
        title (CharField): title of speaker.
        speaker (ForeignKey <Speaker>): Speaker of the job.
    """

    title = models.CharField(
        verbose_name=_("Title"),
        max_length=100
    )
    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} ({self.speaker})"


class JobVideo(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('job', 'video')

    def __str__(self):
        return f"{self.job} - {self.video}"
