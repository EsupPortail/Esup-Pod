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


class ContributionInline(admin.TabularInline):
    """Inline for Contribution to display all a contributor's video appearances."""

    model = Contribution
    extra = 0
    raw_id_fields = ("video",)
    fields = ("video", "role", "job_title")
    show_change_link = True


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    """Admin interface for Contributor model."""

    list_display = ("last_name", "first_name", "email_address", "weblink", "created_at")
    search_fields = ("last_name", "first_name", "email_address")
    readonly_fields = ("created_at",)
    inlines = [ContributionInline]


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    """Admin interface for Contribution model (link between video and contributor)."""

    list_display = ("video", "contributor", "role", "job_title")
    search_fields = ("video__title", "contributor__last_name", "contributor__first_name")
    list_filter = ("role",)
    raw_id_fields = ("video", "contributor")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model (files attached to videos)."""

    list_display = ("title", "video", "is_private")
    search_fields = ("title", "video__title")
    list_filter = ("is_private",)
    raw_id_fields = ("video",)


@admin.register(Overlay)
class OverlayAdmin(admin.ModelAdmin):
    """Admin interface for Overlay model (timed overlays on videos)."""

    list_display = ("title", "video", "time_start", "time_end")
    search_fields = ("title", "video__title")
    raw_id_fields = ("video",)
