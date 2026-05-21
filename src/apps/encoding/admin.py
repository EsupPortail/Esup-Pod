"""
Esup-Pod - Admin configuration for the encoding app.
"""

from django.contrib import admin
from src.apps.encoding.models import EncodingVideo


@admin.register(EncodingVideo)
class EncodingVideoAdmin(admin.ModelAdmin):
    """
    Admin configuration for the EncodingVideo model.
    """

    list_display = ("id", "video", "resolution", "created_at")
    list_filter = ("resolution", "created_at")
    search_fields = ("video__title", "resolution")
    raw_id_fields = ("video",)
    readonly_fields = ("created_at",)
