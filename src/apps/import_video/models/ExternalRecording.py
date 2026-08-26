"""
Esup-Pod - ExternalRecording model.
"""

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class ExternalRecording(models.Model):
    """Represents an external video source to be imported into Pod."""

    class SourceType(models.TextChoices):
        """Supported external video source types."""

        YOUTUBE = "youtube", _("YouTube")
        PEERTUBE = "peertube", _("PeerTube")
        BBB = "bigbluebutton", _("BigBlueButton")
        VIDEO_FILE = "video", _("Video file")
        MEDIACAD = "mediacad", _("Mediacad")

    class ImportStatus(models.TextChoices):
        """Import pipeline status."""

        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        DONE = "done", _("Done")
        ERROR = "error", _("Error")

    name = models.CharField(
        _("Name"),
        max_length=250,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="external_recordings",
        verbose_name=_("Owner"),
    )
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="external_recordings",
        verbose_name=_("Site"),
    )
    source_type = models.CharField(
        _("Source Type"),
        max_length=20,
        choices=SourceType.choices,
    )
    source_url = models.URLField(
        _("Source URL"),
        max_length=500,
    )
    import_status = models.CharField(
        _("Import Status"),
        max_length=20,
        choices=ImportStatus.choices,
        default=ImportStatus.PENDING,
    )
    video = models.OneToOneField(
        "video.Video",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="external_recording",
        verbose_name=_("Imported Video"),
        help_text=_("Video created after successful import."),
    )
    error_message = models.TextField(
        _("Error Message"),
        blank=True,
        default="",
    )
    start_at = models.DateTimeField(
        _("Declared At"),
        default=timezone.now,
    )
    imported_at = models.DateTimeField(
        _("Imported At"),
        null=True,
        blank=True,
    )

    class Meta:
        """ExternalRecording model metadata."""

        verbose_name = _("External Recording")
        verbose_name_plural = _("External Recordings")
        ordering = ["-start_at"]

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()}) — {self.get_import_status_display()}"
