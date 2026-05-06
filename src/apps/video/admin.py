"""
Esup-Pod - Video administrator interface.
"""

from django.contrib import admin
from src.apps.video.models import Video, Type, Discipline, Subtitle


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """
    Esup-Pod - Admin interface for the Video model.
    """

    list_display = ("title", "owner", "status", "created_at", "file_size_mb")
    list_filter = ("status", "created_at", "sites")
    filter_horizontal = ("sites",)
    search_fields = ("title", "description", "owner__username", "owner__email")
    readonly_fields = ("slug", "duration", "created_at", "updated_at")

    def file_size_mb(self, obj):
        """
        Calculates and returns the file size of the video in Megabytes.
        """
        if obj.video_file and hasattr(obj.video_file, "size"):
            return f"{obj.video_file.size / (1024 * 1024):.2f} MB"
        return "N/A"

    file_size_mb.short_description = "Size (MB)"


@admin.register(Type)
class TypeAdmin(admin.ModelAdmin):
    """Admin for Video Type."""

    list_display = ("title", "slug")
    search_fields = ("title",)


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    """Admin for Discipline."""

    list_display = ("title", "slug")
    search_fields = ("title",)


@admin.register(Subtitle)
class SubtitleAdmin(admin.ModelAdmin):
    """Admin for Subtitles."""

    list_display = ("video", "language", "file")
    list_filter = ("language",)
