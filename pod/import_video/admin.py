"""Admin for the Import video module."""
from django.contrib import admin
from .models import Recording


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    """Administration for external recordings.

    Args:
        admin (ModelAdmin): admin model
    """

    list_display = (
        "name",
        "start_at",
        "type",
        "source_url",
        "owner",
    )
    search_fields = [
        "name",
        "source_url",
        "owner",
    ]
