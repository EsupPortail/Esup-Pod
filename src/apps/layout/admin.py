"""
Esup-Pod - Layout admin interface.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from src.apps.layout.models import BlockConfig


@admin.register(BlockConfig)
class BlockConfigAdmin(admin.ModelAdmin):
    """Admin configuration for BlockConfig."""

    list_display = ("admin_name", "frontend_id", "is_active", "item_limit")
    list_filter = ("is_active",)
    search_fields = ("admin_name", "frontend_id", "display_title")

    fieldsets = (
        (
            _("Identification"),
            {
                "fields": ("admin_name", "frontend_id", "is_active"),
            },
        ),
        (
            _("Personalization"),
            {
                "fields": ("display_title", "subtitle_or_text", "item_limit"),
            },
        ),
        (
            _("Theme (Colors)"),
            {
                "fields": ("background_color", "text_color"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Advanced"),
            {
                "fields": ("extra_config",),
                "classes": ("collapse",),
            },
        ),
    )
