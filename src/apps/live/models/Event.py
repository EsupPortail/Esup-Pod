"""
Esup-Pod - Event model.
"""

import hashlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site

from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.apps.video.models.Video import Video
from src.apps.video.models.Type import Type
from src.apps.live.utils import current_time, one_hour_hence

User = get_user_model()
SECRET_KEY = getattr(settings, "SECRET_KEY", "")


class Event(models.Model):
    """
    Represents a planned live-streaming session on a specific Broadcaster.

    An Event has a defined time window (start_date → end_date), an owner,
    optional access restrictions (password, groups, draft), and may produce
    one or more Video recordings after the stream ends.
    """

    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=255,
        editable=False,
    )
    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_(
            "Short and accurate title reflecting the main subject of this event."
        ),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Optional description with context and related information."),
    )
    owner = models.ForeignKey(
        User,
        verbose_name=_("Owner"),
        on_delete=models.CASCADE,
        related_name="owned_events",
    )
    additional_owners = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Additional owners"),
        related_name="co_owned_events",
        help_text=_(
            "Users who share ownership of this event (same rights, except deletion)."
        ),
    )
    start_date = models.DateTimeField(
        _("Start date"),
        default=current_time,
        help_text=_("When the live stream begins."),
    )
    end_date = models.DateTimeField(
        _("End date"),
        default=one_hour_hence,
        help_text=_("When the live stream ends."),
    )
    broadcaster = models.ForeignKey(
        "Broadcaster",
        verbose_name=_("Broadcaster"),
        on_delete=models.CASCADE,
        related_name="events",
        help_text=_("The broadcaster used for this live stream."),
    )
    type = models.ForeignKey(
        Type,
        verbose_name=_("Type"),
        on_delete=models.CASCADE,
        help_text=_("Category type of this event."),
    )
    iframe_url = models.URLField(
        _("Embedded site URL"),
        null=True,
        blank=True,
        help_text=_("URL of a page to display in an iframe alongside the stream."),
    )
    iframe_height = models.IntegerField(
        _("Embedded site height (px)"),
        null=True,
        blank=True,
        help_text=_("Height in pixels of the inline iframe."),
    )
    aside_iframe_url = models.URLField(
        _("Aside embedded site URL"),
        null=True,
        blank=True,
        help_text=_("URL of a secondary page displayed in the aside panel."),
    )
    is_draft = models.BooleanField(
        _("Draft"),
        default=True,
        help_text=_(
            "Draft events are only visible to owners. "
            "Anyone with the private link can still access them."
        ),
    )
    is_restricted = models.BooleanField(
        _("Restricted access"),
        default=False,
        help_text=_("If enabled, only authenticated users can watch this event."),
    )
    restrict_access_to_groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        verbose_name=_("Restricted groups"),
        related_name="restricted_events",
        help_text=_("If set, only members of these groups may access this event."),
    )
    is_auto_start = models.BooleanField(
        _("Auto start"),
        default=False,
        help_text=_("If enabled, recording starts automatically when the event begins."),
    )
    is_recording_stopped = models.BooleanField(
        _("Recording stopped"),
        default=False,
        help_text=_("Internal flag: set to True once the recording has been stopped."),
    )
    video_on_hold = models.ForeignKey(
        Video,
        blank=True,
        null=True,
        verbose_name=_("Video on hold"),
        related_name="events_on_hold",
        on_delete=models.SET_NULL,
        help_text=_("Video displayed while the live stream has not started yet."),
    )
    thumbnail = models.ImageField(
        _("Thumbnail"),
        upload_to="live/events/",
        blank=True,
        null=True,
        help_text=_("Optional thumbnail image for this event."),
    )
    password = models.CharField(
        _("Password"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Optional password required to watch this event."),
    )
    max_viewers = models.IntegerField(
        _("Max viewers"),
        default=0,
        help_text=_("Peak number of simultaneous viewers (maintained by heartbeats)."),
    )
    viewers = models.ManyToManyField(
        User,
        blank=True,
        editable=False,
        related_name="watched_events",
        verbose_name=_("Viewers"),
    )
    videos = models.ManyToManyField(
        Video,
        blank=True,
        editable=False,
        related_name="source_events",
        verbose_name=_("Recordings"),
        help_text=_("Video recordings produced from this event."),
    )
    enable_transcription = models.BooleanField(
        _("Enable transcription"),
        default=False,
        help_text=_("If enabled, live transcription will be generated for this event."),
    )

    class Meta:
        """Event model metadata."""

        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        ordering = ["start_date"]

    def __str__(self) -> str:
        if self.id:
            return f"{self.id:04d} - {self.title}"
        return "Unsaved Event"

    def save(self, *args, **kwargs) -> None:
        """Auto-generate the slug from the ID and title."""
        creating = not self.pk
        if creating:
            super().save(*args, **kwargs)

        new_slug = f"{self.pk:04d}-{slugify(self.title)}"
        if self.slug != new_slug:
            self.slug = new_slug
            if creating:
                Event.objects.filter(pk=self.pk).update(slug=self.slug)
            else:
                super().save(*args, **kwargs)
        elif not creating:
            super().save(*args, **kwargs)

    def get_hashkey(self) -> str:
        """Generate a private access hash for draft events."""
        return hashlib.sha256(f"{SECRET_KEY}-{self.id}".encode("utf-8")).hexdigest()

    def get_thumbnail_url(self) -> str:
        """Return the thumbnail URL or the default event thumbnail."""
        from django.templatetags.static import static

        if self.thumbnail:
            return self.thumbnail.url
        from src.apps.live.conf import live_settings

        return static(live_settings.default_event_thumbnail)

    def get_full_url(self, request=None) -> str:
        """Return the fully-qualified API URL for this event."""
        domain = get_current_site(request).domain
        return f"//{domain}/api/live/events/{self.slug}/"

    # --- Status helpers ---

    def is_current(self) -> bool:
        """Return True if the event is currently live."""
        if self.start_date and self.end_date:
            now = timezone.localtime(timezone.now())
            return self.start_date <= now <= self.end_date
        return False

    def is_past(self) -> bool:
        """Return True if the event has already ended."""
        if self.end_date:
            return self.end_date <= timezone.localtime(timezone.now())
        return False

    def is_coming(self) -> bool:
        """Return True if the event has not yet started."""
        if self.start_date:
            return timezone.localtime(timezone.now()) < self.start_date
        return False
