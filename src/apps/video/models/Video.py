"""
Esup-Pod - Video model.
"""

from datetime import date
from django.contrib.sites.models import Site
from django.db.models import Q
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.hashers import make_password, identify_hasher
import tagulous.models
from src.apps.encoding.services.storage import (
    get_storage_path_video,
    get_storage_path_image,
)
from src.apps.video.conf import video_settings


class VideoManager(models.Manager):
    """Custom manager for Video model providing visibility filtering."""

    def visible_for(self, user):
        """Returns a queryset of videos visible to the given user."""
        if user.is_authenticated and user.is_superuser:
            return self.get_queryset()

        if not user.is_authenticated:
            q_filter = Q(status=self.model.Status.PUBLISHED) | (
                Q(status=self.model.Status.RESTRICTED) & Q(is_auth_required=False)
            )
            if not video_settings.homepage_shows_passworded:
                q_filter &= Q(password__isnull=True) | Q(password__exact="")
            return self.get_queryset().filter(q_filter)

        # Authenticated users
        base_q = (
            Q(status=self.model.Status.PUBLISHED)
            | Q(status=self.model.Status.RESTRICTED)
            | Q(owner=user)
            | Q(co_owners=user)
            | Q(channel__owner=user)
            | Q(channel__collaborators=user)
        )
        if hasattr(user, "owner"):
            base_q |= Q(restricted_groups__users=user.owner)

        return self.get_queryset().filter(base_q).distinct()


class Video(models.Model):
    """
    Model representing a video.
    """

    objects = VideoManager()

    # 1.CHOICES
    class Status(models.TextChoices):
        """Visibility/publication status of a video (independent of encoding)."""

        DRAFT = "DR", _("Draft (Private)")
        PUBLISHED = "PU", _("Published (Public)")
        RESTRICTED = "RE", _("Restricted (Access Controlled)")

    class EncodingStatus(models.TextChoices):
        """Encoding pipeline status (independent of visibility)."""

        PENDING = "PE", _("Pending")
        PROCESSING = "PR", _("Processing")
        DONE = "DO", _("Done")
        ERROR = "ER", _("Error")

    # 2. CORE
    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_("A title as short and accurate as possible."),
    )
    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=255,
        editable=False,
        help_text=_("URL friendly identifier."),
    )
    description = models.TextField(
        _("Description"), blank=True, help_text=_("Full description of the content.")
    )
    video_file = models.FileField(
        _("Video File"),
        upload_to=get_storage_path_video,
        max_length=255,
        null=True,
        blank=True,
    )
    is_video = models.BooleanField(
        _("Is Video"),
        default=True,
        editable=False,
        help_text=_("Distinguishes between Audio and Video."),
    )

    # 3.TECHNICAL & MEDIA INFO
    thumbnail = models.ImageField(
        _("Thumbnail"),
        upload_to=get_storage_path_image,
        null=True,
        blank=True,
        help_text=_("Custom cover image for the video."),
    )
    overview = models.ImageField(
        _("Overview"),
        upload_to=get_storage_path_image,
        null=True,
        blank=True,
        editable=False,
        help_text=_("Automatically generated image from the video."),
    )
    duration = models.IntegerField(_("Duration (s)"), default=0, editable=False)
    view_count = models.PositiveIntegerField(_("View Count"), default=0, editable=False)
    is_360 = models.BooleanField(
        _("360° Video"),
        default=False,
        help_text=_("Check if this is a 360-degree immersive video."),
    )
    # 4. OWNERSHIP & ACCESS
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="videos",
        on_delete=models.CASCADE,
        verbose_name=_("Owner"),
    )
    channel = models.ForeignKey(
        "collection.Channel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="videos",
        verbose_name=_("Channel"),
        help_text=_("The channel this video belongs to."),
    )
    co_owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="co_owned_videos",
        blank=True,
        verbose_name=_("Co-Owners"),
        help_text=_("Users with edit rights on this video."),
    )
    status = models.CharField(
        _("Status"),
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    encoding_status = models.CharField(
        _("Encoding Status"),
        max_length=2,
        choices=EncodingStatus.choices,
        default=EncodingStatus.PENDING,
        db_index=True,
        help_text=_(
            "Tracks the encoding pipeline state independently from the video’s visibility."
        ),
    )
    is_auth_required = models.BooleanField(
        _("Authentication Required"),
        default=False,
        help_text=_(
            "If checked, users must be logged in to access this video (even if they have the password)."
        ),
    )
    # 4. ACCESS CONTROL
    sites = models.ManyToManyField(
        Site,
        blank=True,
        related_name="videos",
        verbose_name=_("Sites"),
        help_text=_("Portals where this video will be published."),
    )
    password = models.CharField(
        _("Password"),
        max_length=128,
        blank=True,
        null=True,
        help_text=_("Optional password for access protection."),
    )

    # 5. SETTINGS
    allow_downloading = models.BooleanField(
        _("Allow Downloading"),
        default=False,
        help_text=_("Allow users to download the source file."),
    )
    disable_comment = models.BooleanField(
        _("Disable Comments"),
        default=False,
        help_text=_("Prevent users from commenting on this specific content."),
    )
    order = models.PositiveSmallIntegerField(
        _("Order"),
        default=1,
        blank=True,
        null=True,
        help_text=_("Order priority in channels or playlists."),
    )
    # 6.CONTENT DESCRIPTION & CLASSIFICATION
    date_of_event = models.DateField(
        _("Date of Event"), default=date.today, blank=True, null=True
    )
    license = models.ForeignKey(
        "video.License",
        on_delete=models.SET_NULL,
        verbose_name=_("License"),
        blank=True,
        null=True,
    )
    cursus = models.ForeignKey(
        "video.Cursus",
        on_delete=models.SET_NULL,
        verbose_name=_("Cursus"),
        blank=True,
        null=True,
    )
    language = models.ForeignKey(
        "video.Language",
        on_delete=models.SET_NULL,
        verbose_name=_("Main Language"),
        blank=True,
        null=True,
        help_text=_("Language spoken in the video (e.g. 'fr', 'en')."),
    )
    transcript_language = models.CharField(
        _("Transcript Language"),
        max_length=10,
        blank=True,
        help_text=_("Language of the available audio transcription."),
    )
    restricted_groups = models.ManyToManyField(
        "authentication.AccessGroup",
        blank=True,
        related_name="videos",
        verbose_name=_("Restricted Groups"),
        help_text=_("One or more groups who can access this video."),
    )
    type = models.ForeignKey(
        "video.Type",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Type"),
        help_text=_("The general format of the video."),
    )
    # [TODO] themes = models.ManyToManyField("video.Theme", blank=True)
    disciplines = models.ManyToManyField(
        "video.Discipline", blank=True, verbose_name=_("Disciplines")
    )
    tags = tagulous.models.TagField(
        blank=True, help_text=_("A comma-separated list of tags.")
    )

    # 7. TIMESTAMPS
    created_at = models.DateTimeField(_("Created At"), default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    date_to_delete = models.DateField(
        _("Expiration Date"),
        null=True,
        blank=True,
        help_text=_("Date when the video will be automatically archived/deleted."),
    )

    class Meta:
        """Video model metadata and database indexing."""

        ordering = ["-created_at"]
        verbose_name = _("Video")
        verbose_name_plural = _("Videos")
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["created_at"]),
        ]

    @property
    def thumbnail_url(self):
        """Returns the thumbnail URL or the default one if it doesn't exist."""
        if self.thumbnail and hasattr(self.thumbnail, "url"):
            return self.thumbnail.url

        if self.overview and hasattr(self.overview, "url"):
            return self.overview.url

        from django.templatetags.static import static

        return static(video_settings.default_thumbnail or "img/default_thumbnail.svg")

    def get_tag_list(self):
        """Returns the tags as a comma-separated string."""
        if not self.id:
            return ""
        return ", ".join([t.name for t in self.tags.all()])

    def get_json_to_index(self):
        """Returns the tags as a list of dictionaries for indexing."""
        if not self.id:
            return []
        return list(self.tags.all().values("name", "slug"))

    def get_dublin_core(self):
        """Generates Dublin Core metadata in dictionary format."""
        return {
            "title": self.title,
            "description": self.description or "",
            "creator": self.owner.username if self.owner else "",
            "publisher": video_settings.template_visible_settings.get(
                "TITLE_ETB", "University name"
            ),
            "date": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
            "format": "video/mp4",
            "rights": (
                self.license.slug if self.license else video_settings.default_dc_rights
            ),
            "coverage": video_settings.default_dc_coverage,
            "subject": ", ".join([d.title for d in self.disciplines.all()]),
            "type": self.type.title if self.type else "",
            "language": self.language.name if self.language else "",
            "identifier": self.get_absolute_url(),
        }

    def set_password(self) -> None:
        """
        Encrypts the password if the video is protected.
        An already encrypted password will not be re-encrypted.
        """
        if self.password:
            try:
                identify_hasher(self.password)
            except ValueError:
                self.password = make_password(self.password)

    def save(self, *args, **kwargs):
        """
        Overridden save method.

        NOTE: Slug is not generated here because it depends on the PK
        (available only after INSERT). It is handled in the post_save signal (set_video_slug).
        The slug is created once and remains immutable in V5, unlike V4.
        """
        self.set_password()

        if not self.id:
            from src.apps.video.services.metadata import calculate_expiration_date
            from src.apps.video.models import License, Type

            self.date_to_delete = calculate_expiration_date(self.owner)

            if not self.license_id and video_settings.default_license:
                try:
                    self.license = License.objects.get(
                        slug=video_settings.default_license
                    )
                except License.DoesNotExist:
                    pass

            if not self.type_id and video_settings.default_type_id:
                try:
                    self.type = Type.objects.get(pk=video_settings.default_type_id)
                except Type.DoesNotExist:
                    pass

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def get_absolute_url(self):
        """
        Returns the V4-compatible permalink.
        Format: /video/<slug>/ where slug is already "0042-my-video-title".

        previously this returned f"/video/{self.pk}-{self.slug}/" which
        produced a double-ID like /video/42-0042-titre/. The slug already embeds
        the zero-padded ID, so only the slug is needed here.
        """
        return f"/video/{self.slug}/"
