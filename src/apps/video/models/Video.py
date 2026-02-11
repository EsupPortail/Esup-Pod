import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from src.apps.video.services.storage import get_storage_path_video


class Video(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DR", _("Draft (Private)")
        PUBLISHED = "PU", _("Published (Public)")
        RESTRICTED = "RE", _("Restricted (Auth only)")
        ENCODING = "EN", _("Encoding in progress")
        ERROR = "ER", _("Encoding Error")

    title = models.CharField(_("Title"), max_length=250)
    slug = models.SlugField(_("Slug"), unique=True, max_length=255, editable=False)
    description = models.TextField(_("Description"), blank=True)
    video_file = models.FileField(
        _("Video File"), upload_to=get_storage_path_video, max_length=255
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="videos",
        on_delete=models.CASCADE,
        verbose_name=_("Owner"),
    )
    status = models.CharField(
        _("Status"), max_length=2, choices=Status.choices, default=Status.ENCODING
    )
    duration = models.IntegerField(_("Duration"), default=0, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Video")
        verbose_name_plural = _("Videos")
        indexes = [
            models.Index(fields=["status"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_id = str(uuid.uuid4())[:8]
            self.slug = f"{base_slug}-{unique_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
