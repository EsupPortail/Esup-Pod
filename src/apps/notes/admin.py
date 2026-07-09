"""
Esup-Pod - Notes administrator interface.
"""

from django.contrib import admin
from src.apps.notes.models import VideoNote


@admin.register(VideoNote)
class VideoNoteAdmin(admin.ModelAdmin):
    """Admin interface for VideoNote model."""

    list_display = ("owner", "video", "privacy", "timestamp", "created_at")
    list_filter = ("privacy", "created_at")
    search_fields = ("owner__username", "video__title", "content")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("owner", "video")
