from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from pod.meetings.models import Meetings #,Attendee, #Stream

class MeetingsAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "titre",
        "attendee_password",
        "moderator_password",
    )
    list_display_links = ("id", "titre")
    readonly_fields = []
    search_fields = [
        "id",
        "titre",
    ]

'''
class AttendeeAdmin(admin.ModelAdmin):
    list_display = ("id", "fullname", "role", "username")
    list_display_links = ("id", "fullname")
    ordering = ("fullname",)
    readonly_fields = []
    search_fields = ["id", "fullname"]


class StreamAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "id",
        "meetings",
        "start_date",
        "end_date",
    )
    list_display_links = ("id", "meetings")
    ordering = ("-id", "-start_date")
    readonly_fields = []
    search_fields = [
        "id",
        "meetings__meetings_name",
        "user__username",
        "user__first_name",
        "user__last_name",
    ]
'''

admin.site.register(Meetings, MeetingsAdmin)
#admin.site.register(Attendee, AttendeeAdmin)
#admin.site.register(Stream, StreamAdmin)