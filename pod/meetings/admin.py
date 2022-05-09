from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from pod.meetings.models import Meetings

class MeetingsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "attendee_password",
        "moderator_password",
    )
    list_display_links = ("id", "name")
    readonly_fields = []
    search_fields = [
        "id",
        "name",
    ]

admin.site.register(Meetings, MeetingsAdmin)