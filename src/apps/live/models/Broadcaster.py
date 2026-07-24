"""
Esup-Pod - Broadcaster model.
"""

import base64
import io
import json
import logging
import os

from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

from src.apps.live.conf import live_settings

logger = logging.getLogger(__name__)

LANG_CHOICES = getattr(settings, "LANGUAGES", [("fr", "French"), ("en", "English")])


class Broadcaster(models.Model):
    """
    Represents a physical or virtual device capable of streaming a live feed.

    A Broadcaster belongs to a Building, carries an RTMP/HLS stream URL,
    and may optionally be piloted (recording start/stop) through an external
    implementation (Wowza, SMP, etc.).
    """

    name = models.CharField(
        _("Name"),
        max_length=200,
        unique=True,
        help_text=_("Unique name for this broadcaster."),
    )
    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=200,
        editable=False,
        default="",
        help_text=_("Auto-generated URL-friendly identifier from the name."),
    )
    building = models.ForeignKey(
        "Building",
        verbose_name=_("Building"),
        on_delete=models.CASCADE,
        help_text=_("Building this broadcaster belongs to."),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Optional description of the broadcaster."),
    )
    poster = models.ImageField(
        _("Poster"),
        upload_to="live/broadcasters/",
        blank=True,
        null=True,
        help_text=_("Optional poster image for this broadcaster."),
    )
    url = models.URLField(
        _("Stream URL"),
        unique=True,
        help_text=_("URL of the live stream (RTMP/HLS)."),
    )
    status = models.BooleanField(
        _("Active"),
        default=False,
        help_text=_("Indicates whether the broadcaster is currently sending a stream."),
    )
    enable_add_event = models.BooleanField(
        _("Enable event creation"),
        default=False,
        help_text=_(
            "If enabled, users with rights can create events on this broadcaster."
        ),
    )
    enable_viewer_count = models.BooleanField(
        _("Enable viewer count"),
        default=True,
        help_text=_("Show the number of live viewers on this stream."),
    )
    is_restricted = models.BooleanField(
        _("Restricted access"),
        default=False,
        help_text=_("If enabled, only authenticated users can access this live stream."),
    )
    public = models.BooleanField(
        _("Show in live list"),
        default=True,
        help_text=_("If enabled, this broadcaster appears in the public live listing."),
    )
    manage_groups = models.ManyToManyField(
        Group,
        blank=True,
        verbose_name=_("Management groups"),
        related_name="managed_broadcasters",
        help_text=_("Groups whose members can create events on this broadcaster."),
    )
    piloting_implementation = models.CharField(
        _("Piloting implementation"),
        max_length=100,
        blank=True,
        default="",
        help_text=_("Identifier of the external piloting system (e.g. 'Wowza', 'SMP')."),
    )
    piloting_conf = models.TextField(
        _("Piloting configuration"),
        blank=True,
        default="",
        help_text=_("JSON configuration passed to the piloting implementation."),
    )
    main_lang = models.CharField(
        _("Main language"),
        max_length=10,
        choices=LANG_CHOICES,
        default="fr",
        help_text=_("Primary language used in the live stream (for transcription)."),
    )
    transcription_file = models.FileField(
        upload_to="live/transcripts/",
        max_length=255,
        null=True,
        blank=True,
        editable=False,
        help_text=_("Auto-managed VTT file for live transcription output."),
    )

    class Meta:
        """Broadcaster model metadata."""

        verbose_name = _("Broadcaster")
        verbose_name_plural = _("Broadcasters")
        ordering = ["building", "name"]

    def __str__(self) -> str:
        return f"{self.name} — {self.url}"

    def save(self, *args, **kwargs) -> None:
        """Auto-generate slug and initialise the transcription VTT file."""
        self.slug = slugify(self.name)
        self._init_transcription_file()
        super().save(*args, **kwargs)

    def _init_transcription_file(self) -> None:
        """Create the empty VTT transcription file on the filesystem if it does not exist."""
        if not settings.MEDIA_ROOT:
            return
        folder_name = live_settings.live_transcriptions_folder
        trans_folder = os.path.join(settings.MEDIA_ROOT, folder_name)
        filename = self.slug + ".vtt"
        trans_file = os.path.join(trans_folder, filename)
        if not os.path.exists(trans_folder):
            os.makedirs(trans_folder, exist_ok=True)
        if not os.path.exists(trans_file):
            open(trans_file, "a").close()
        self.transcription_file = os.path.join(folder_name, filename)

    def get_poster_url(self) -> str:
        """Return the poster image URL or the default thumbnail."""
        if self.poster:
            return self.poster.url
        return "".join([settings.STATIC_URL, live_settings.default_thumbnail])

    @property
    def sites(self):
        """Expose sites via the parent Building (multi-tenancy)."""
        return self.building.sites

    def is_recording(self) -> bool:
        """Check if the broadcaster is currently recording via its piloting implementation."""
        from src.apps.live.services.piloting import get_piloting_implementation

        impl = get_piloting_implementation(self)
        if impl:
            try:
                return impl.is_recording()
            except Exception as exc:
                logger.warning("is_recording check failed for %s: %s", self.name, exc)
        return False

    def get_piloting_conf_dict(self) -> dict:
        """Safely parse and return the piloting_conf JSON as a dict."""
        if not self.piloting_conf:
            return {}
        try:
            return json.loads(self.piloting_conf)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in piloting_conf for broadcaster %s", self.name)
            return {}

    @property
    def qrcode(self) -> str:
        """
        Generate a QR code (base64 PNG data-URI) pointing to the immediate
        event creation URL for this broadcaster.

        Mirrors V4 Broadcaster.qrcode property.
        Returns an empty string if the `qrcode` library is not installed.
        """
        try:
            import qrcode as qrcode_lib
        except ImportError:
            logger.warning(
                "qrcode library is not installed — cannot generate QR code for broadcaster %s",
                self.name,
            )
            return ""

        from django.urls import reverse

        try:
            url = reverse("live:event_immediate_edit", args=[self.id])
        except Exception:
            # URL may not be registered in API-only mode; use a relative fallback
            url = f"/live/event/add/?broadcaster={self.id}"

        img = qrcode_lib.make(url)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
