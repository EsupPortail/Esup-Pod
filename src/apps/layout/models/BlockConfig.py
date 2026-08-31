"""
Esup-Pod - BlockConfig model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class BlockConfig(models.Model):
    """Model to store configuration for frontend visual blocks."""

    frontend_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Frontend Identifier"),
        help_text=_(
            "The strict ID used by the frontend team (e.g., 'home-carousel-latest')"
        ),
    )

    admin_name = models.CharField(
        max_length=150,
        verbose_name=_("Admin Name"),
        help_text=_("Readable name for the Django administration"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this block should be displayed by the frontend."),
    )

    display_title = models.CharField(
        max_length=200, blank=True, null=True, verbose_name=_("Display Title")
    )

    subtitle_or_text = models.TextField(
        blank=True, null=True, verbose_name=_("Subtitle or Text")
    )

    item_limit = models.PositiveSmallIntegerField(
        default=10,
        verbose_name=_("Item Limit"),
        help_text=_(
            "How many items (e.g., videos) should the frontend request for this block."
        ),
    )

    background_color = models.CharField(
        max_length=20, blank=True, null=True, verbose_name=_("Background Color (Hex)")
    )

    text_color = models.CharField(
        max_length=20, blank=True, null=True, verbose_name=_("Text Color (Hex)")
    )

    extra_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Extra Configuration (JSON)"),
        help_text=_("Additional frontend-specific options (e.g., auto_play: true)."),
    )

    def __str__(self):
        return f"{self.admin_name} ({self.frontend_id})"

    class Meta:
        """Meta options."""

        verbose_name = _("Block Configuration")
        verbose_name_plural = _("Block Configurations")
