"""
Esup-Pod - Completion admin.
"""

from django.contrib import admin
from src.apps.completion.models import (
    Contributor,
    Contribution,
    Document,
    Overlay,
)

@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    """Admin interface for Contributor model."""

    list_display = ("last_name", "first_name", "email_address")
    search_fields = ("last_name", "first_name", "email_address")


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    """Admin interface for Contribution model."""

    list_display = ("video", "contributor", "role")
    search_fields = ("video__title", "contributor__last_name")
    list_filter = ("role",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model."""

    list_display = ("title", "video", "is_private")
    search_fields = ("title", "video__title")
    list_filter = ("is_private",)


@admin.register(Overlay)
class OverlayAdmin(admin.ModelAdmin):
    """Admin interface for Overlay model."""

    list_display = ("title", "video", "time_start", "time_end")
    search_fields = ("title", "video__title")


