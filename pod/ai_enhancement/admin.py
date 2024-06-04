"""Esup-Pod AI enhancement admin."""

from django.contrib import admin

from .models import AIEnhancement


@admin.register(AIEnhancement)
class AIEnhancementAdmin(admin.ModelAdmin):
    """AIEnhancement admin page."""

    date_hierarchy = "updated_at"
    list_display = (
        "id",
        "ai_enhancement_id_in_aristote",
        "video",
        "is_ready",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id", "ai_enhancement_id_in_aristote")
    list_filter = ("is_ready", "created_at", "updated_at")
    search_fields = [
        "ai_enhancement_id_in_aristote",
        "video__title",
        "video__id",
        "video__slug",
    ]
