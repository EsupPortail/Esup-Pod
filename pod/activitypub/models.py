from django.db import models
from django.utils.translation import ugettext_lazy as _

from pod.video.models import Video


class Follower(models.Model):
    actor = models.CharField(
        _("Actor"),
        max_length=255,
        help_text=_("Actor who initiated the Follow activity"),
    )


class Following(models.Model):
    class Status(models.IntegerChoices):
        NONE = 0, _("None")
        REQUESTED = 1, _("Following request sent")
        ACCEPTED = 2, _("Following request accepted")
        REFUSED = 3, _("Following request refused")

    object = models.CharField(
        _("Object"),
        max_length=255,
        help_text=_("URL of the instance to follow"),
    )
    status = models.IntegerField(
        _("Status"),
        help_text=_("URL of the instance to follow"),
        choices=Status.choices,
        default=Status.NONE,
    )


class ExternalVideo(Video):
    source_instance = models.ForeignKey(
        Following,
        on_delete=models.CASCADE,
        verbose_name=_("Source instance"),
        help_text=_("Video origin instance"),
    )
    ap_id = models.CharField(
        _("Video identifier"),
        max_length=255,
        help_text=_("Video identifier URL"),
    )
