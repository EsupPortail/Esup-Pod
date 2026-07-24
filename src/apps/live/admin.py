"""
Esup-Pod - Live admin interface.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from src.apps.live.models import Building, Broadcaster, Event, HeartBeat


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    """Admin interface for the Building model."""

    list_display = ("name", "gmapurl")
    filter_horizontal = ("sites",)
    search_fields = ("name",)


@admin.register(Broadcaster)
class BroadcasterAdmin(admin.ModelAdmin):
    """Admin interface for the Broadcaster model."""

    list_display = (
        "name",
        "building",
        "url",
        "status",
        "public",
        "is_restricted",
        "piloting_implementation",
        "recording_status_display",
    )
    list_filter = ("building", "public", "is_restricted", "status")
    search_fields = ("name", "url")
    readonly_fields = ("slug", "qrcode_display")
    filter_horizontal = ("manage_groups",)

    def recording_status_display(self, obj: Broadcaster):
        """Display a coloured indicator of the current recording state."""
        try:
            recording = obj.is_recording()
            if recording:
                return format_html(
                    '<img src="/static/admin/img/icon-yes.svg" alt="Recording">'
                )
            return format_html(
                '<img src="/static/admin/img/icon-no.svg" alt="Not recording">'
            )
        except Exception:
            return format_html('<img src="/static/admin/img/icon-alert.svg" alt="Error">')

    recording_status_display.short_description = _("Recording?")

    def qrcode_display(self, obj: Broadcaster):
        """Display the QR code for immediate event creation in admin."""
        data_uri = obj.qrcode
        if not data_uri:
            return _("QR code unavailable (install the 'qrcode' library).")
        return format_html(
            '<img src="{}" alt="{}" style="width:150px;height:150px;" />',
            data_uri,
            _("QR code to create an immediate event"),
        )

    qrcode_display.short_description = _("QR code (immediate event)")


class EventInline(admin.TabularInline):
    """Inline: recorded videos linked to an event."""

    model = Event.videos.through
    extra = 0
    verbose_name = _("Linked recording")
    verbose_name_plural = _("Linked recordings")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin interface for the Event model."""

    list_display = (
        "title",
        "owner",
        "broadcaster",
        "start_date",
        "end_date",
        "is_draft",
        "is_restricted",
        "max_viewers",
    )
    list_filter = ("is_draft", "is_restricted", "broadcaster__building")
    search_fields = ("title", "owner__username", "broadcaster__name")
    readonly_fields = ("slug", "max_viewers", "is_recording_stopped")
    filter_horizontal = ("additional_owners", "restrict_access_to_groups")
    date_hierarchy = "start_date"
    ordering = ("-start_date",)


@admin.register(HeartBeat)
class HeartBeatAdmin(admin.ModelAdmin):
    """Admin interface for the HeartBeat model (read-only view)."""

    list_display = ("event", "user", "viewkey", "last_heartbeat")
    list_filter = ("event",)
    readonly_fields = ("event", "user", "viewkey", "last_heartbeat")

    def has_add_permission(self, request):
        return False
