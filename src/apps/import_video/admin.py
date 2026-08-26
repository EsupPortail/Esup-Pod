"""
Esup-Pod - Import Video administrator interface.
"""

from django.contrib import admin
from src.apps.import_video.models import ExternalRecording


@admin.register(ExternalRecording)
class ExternalRecordingAdmin(admin.ModelAdmin):
    """Admin interface for ExternalRecording model."""

    list_display = (
        "name",
        "owner",
        "source_type",
        "import_status",
        "site",
        "start_at",
        "imported_at",
    )
    list_filter = ("source_type", "import_status", "site")
    search_fields = ("name", "owner__username", "source_url")
    readonly_fields = (
        "import_status",
        "video",
        "error_message",
        "start_at",
        "imported_at",
    )
    raw_id_fields = ("owner", "video")
