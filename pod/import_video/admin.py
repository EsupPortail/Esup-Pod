"""Admin for the Import video module."""

from django.contrib import admin
from .models import ExternalRecording


@admin.register(ExternalRecording)
class ExternalRecordingAdmin(admin.ModelAdmin):
    """Administration for external recordings.

    Args:
        admin (ModelAdmin): admin model
    """

    list_display = (
        "name",
        "start_at",
        "type",
        "source_url",
        "state",
        "owner",
    )
    search_fields = [
        "name",
        "source_url",
        "owner",
    ]
