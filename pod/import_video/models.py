"""Models for the Import_video module."""
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

SITE_ID = getattr(settings, "SITE_ID", 1)


class ExternalRecording(models.Model):
    """This model hold information about external recordings.

    This model is for external recordings.
    For internal recordings: only BBB recordings that have been uploaded to
    Pod are saved in the database (see Meetings module).
    For external recordings: all recordings are saved in the database.
    """

    # Name
    name = models.CharField(
        max_length=250,
        verbose_name=_("Recording name"),
        help_text=_(
            "Please enter a name that will allow you to easily find this recording."
        ),
    )

    # Start date
    start_at = models.DateTimeField(_("Start date"), default=timezone.now, editable=False)

    # User who create this recording
    owner = models.ForeignKey(
        User,
        related_name="owner_external_recording",
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
        verbose_name=_("User"),
        blank=True,
        null=True,
        help_text=_("User who create this recording"),
    )

    """ Useless for the moment
    # Additional owners for this recording
    additional_owners = models.ManyToManyField(
        User,
        related_name="owners_external_recordings",
        limit_choices_to={"is_staff": True},
        verbose_name=_("Additional owners"),
        blank=True,
        help_text=_(
            "You can add additional owners to this recording. "
            "They will have the same rights as you except that "
            "they cannot delete this recording."
        ),
    )
    """

    # Recording's site
    site = models.ForeignKey(
        Site,
        related_name="site_external_recording",
        verbose_name=_("Site"),
        on_delete=models.CASCADE,
        default=SITE_ID,
    )

    # Type of external recording
    # Possibles choices
    types = [
        ("bigbluebutton", _("Big Blue Button")),
        ("peertube", _("PeerTube")),
        ("video", _("Video file")),
        ("youtube", _("Youtube")),
    ]

    default_type = types[0][0]
    type = models.CharField(
        max_length=50,
        choices=types,
        default=default_type,
        verbose_name=_("External record type"),
        help_text=_(
            "It is possible to manage recordings from "
            "Big Blue Button or another source delivering video files."
        ),
    )

    # Source video URL
    source_url = models.CharField(
        max_length=500,
        default="",
        verbose_name=_("Address of the recording to download"),
        help_text=_(
            "Please enter the address of the recording to download. "
            "This address must match the record type selected."
        ),
    )

    # User who uploaded to Pod the video file
    uploaded_to_pod_by = models.ForeignKey(
        User,
        related_name="uploader_external_recording",
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
        verbose_name=_("User"),
        null=True,
        blank=True,
        help_text=_("User who uploaded to Pod the video file"),
    )

    def __unicode__(self):
        return "%s - %s" % (self.id, self.name)

    def __str__(self):
        return "%s - %s" % (self.id, self.name)

    def save(self, *args, **kwargs):
        super(ExternalRecording, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "External recording"
        verbose_name_plural = _("External recordings")
        ordering = ("-start_at",)
        get_latest_by = "start_at"


@receiver(pre_save, sender=ExternalRecording)
def default_site_recording(sender, instance, **kwargs):
    """Save default site for this recording."""
    if not hasattr(instance, "site"):
        instance.site = Site.objects.get_current()
