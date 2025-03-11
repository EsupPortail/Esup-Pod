"""Esup-Pod speaker models."""

from django.db import models
from django.utils.translation import gettext as _
from pod.video.models import Video


class Speaker(models.Model):
    """
    Speaker model.

    Attributes:
        firstname (CharField): first name of speaker.
        lastname (CharField): last name of speaker.
    """

    firstname = models.CharField(verbose_name=_("First name"), max_length=100)
    lastname = models.CharField(verbose_name=_("Last name"), max_length=100)

    class Meta:
        ordering = ["lastname", "firstname"]
        verbose_name = _("Speaker")
        verbose_name_plural = _("Speakers")

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class Job(models.Model):
    """
    Job model.

    Attributes:
        title (CharField): title of speaker.
        speaker (ForeignKey <Speaker>): Speaker of the job.
    """

    title = models.CharField(verbose_name=_("Title"), max_length=100)
    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.speaker} ({self.title})"


class JobVideo(models.Model):
    """
    JobVideo model.

    Attributes:
        job (ForeignKey <Job>): job of speaker.
        video (ForeignKey <Video>): video.
    """

    job = models.ForeignKey(
        Job, verbose_name=_("Speaker’s job"), on_delete=models.CASCADE
    )
    video = models.ForeignKey(Video, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("job", "video")

    def __str__(self):
        return f"{self.job} - {self.video}"
