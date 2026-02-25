from datetime import date
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from src.apps.encoding.services.storage import (
    get_storage_path_video,
    get_storage_path_image,
)
from video.conf import video_settings


class Video(models.Model):
    """
    Model representing a video.
    """
    # 1.CHOICES
    class Status(models.TextChoices):
        DRAFT = "DR", _("Draft (Private)")
        PUBLISHED = "PU", _("Published (Public)")
        RESTRICTED = "RE", _("Restricted (Access Controlled)")
        ENCODING = "EN", _("Encoding in progress")
        ERROR = "ER", _("Encoding Error")

    class License(models.TextChoices):
        CC_BY = "CC-BY", _("Creative Commons BY")
        CC_BY_SA = "CC-BY-SA", _("Creative Commons BY-SA")
        CC_BY_NC = "CC-BY-NC", _("Creative Commons BY-NC")
        CC_BY_ND = "CC-BY-ND", _("Creative Commons BY-ND")
        COPYRIGHT = "COPYRIGHT", _("All rights reserved")

    class Cursus(models.TextChoices):
        L1 = "L1", _("Licence 1")
        L2 = "L2", _("Licence 2")
        L3 = "L3", _("Licence 3")
        M1 = "M1", _("Master 1")
        M2 = "M2", _("Master 2")
        DOCTORATE = "D", _("Doctorate")
        OTHER = "0", _("Other")

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
        default=Status.ENCODING,
        db_index=True,
    )
    is_auth_required = models.BooleanField(
        _("Authentication Required"),
        default=False,
        help_text=_(
            "If checked, users must be logged in to access this video (even if they have the password)."
        ),
    )
    password = models.CharField(
        _("Password"),
        max_length=128,
        blank=True,
        null=True,
        help_text=_("Optional password for access protection."),
    )
    # Relations vers les sites et groupes (Strings pour éviter les imports circulaires)
    # sites = models.ManyToManyField("core.Site", blank=True)
    # restricted_groups = models.ManyToManyField("authentication.AccessGroup", blank=True)

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
    license = models.CharField(
        _("License"),
        max_length=20,
        choices=License.choices,
        default=License.COPYRIGHT,
        blank=True,
        null=True,
    )
    cursus = models.CharField(
        _("Cursus"),
        max_length=10,
        choices=Cursus.choices,
        default=Cursus.OTHER,
        blank=True,
    )
    language = models.CharField(
        _("Main Language"),
        max_length=10,
        default=settings.LANGUAGE_CODE,
        help_text=_("Language spoken in the video (e.g. 'fr', 'en')."),
    )
    transcript_language = models.CharField(
        _("Transcript Language"),
        max_length=10,
        blank=True,
        help_text=_("Language of the available audio transcription."),
    )
    # Relations Placeholder (À décommenter quand les modèles seront créés)
    # type = models.ForeignKey("video.Type", on_delete=models.SET_NULL, null=True, default=DEFAULT_TYPE_ID)
    # channels = models.ManyToManyField("video.Channel", blank=True)
    # themes = models.ManyToManyField("video.Theme", blank=True)
    # disciplines = models.ManyToManyField("video.Discipline", blank=True)
    # tags = models.ManyToManyField("core.Tag", blank=True)

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
        if self.thumbnail and hasattr(self.thumbnail, 'url'):
            return self.thumbnail.url
        return video_settings.default_thumbnail

    def get_dublin_core(self):
        """Generates Dublin Core metadata in dictionary format."""
        return {
            "title": self.title,
            "description": self.description or "",
            "creator": self.owner.username if self.owner else "",
            "publisher": video_settings.template_visible_settings.get("TITLE_ETB", "University name"),
            "date": self.created_at.strftime("%Y-%m-%d") if self.created_at else "",
            "format": "video/mp4",
            "rights": self.license if self.license else video_settings.default_dc_rights,
            "coverage": video_settings.default_dc_coverage,
        }

    def set_password(self) -> None:
        """
        Encrypts the password if the video is protected.
        An already encrypted password will not be re-encrypted.
        """
        if self.password and not self.password.startswith("pbkdf2_sha256$"):
            self.password = make_password(self.password, hasher="pbkdf2_sha256")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_id = str(uuid.uuid4())[:8]
            self.slug = f"{base_slug}-{unique_id}"
        self.set_password()
        if not self.id:
            from src.apps.video.services.metadata import calculate_expiration_date
            self.date_to_delete = calculate_expiration_date(self.owner)
        if self.pk:
            old_version = Video.objects.get(pk=self.pk)
            if old_version.owner != self.owner:
                from src.apps.video.services.storage import move_video_files_to_new_owner
                move_video_files_to_new_owner(self, old_version.owner, self.owner)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
