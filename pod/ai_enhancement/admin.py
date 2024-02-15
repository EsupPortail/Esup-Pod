"""Esup-Pod AI enhancement admin."""
from django.contrib import admin

from .models import AIEnrichment


@admin.register(AIEnrichment)
class ModelNameAdmin(admin.ModelAdmin):
    """AIEnrichment admin page."""

    date_hierarchy = "updated_at"
    list_display = (
        "id",
        "ai_enrichment_id_in_aristote",
        "video",
        "is_ready",
        "created_at",
        "updated_at",
    )
    list_display_links = ("id", "ai_enrichment_id_in_aristote")
    list_filter = ("is_ready", )
    search_fields = ["ai_enrichment_id_in_aristote", "video__title"]
