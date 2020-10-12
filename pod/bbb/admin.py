from django.contrib import admin
from .models import Meeting
from .models import User as BBBUser


class MeetingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'date', 'meeting_name', 'encoding_step',
        'recorded', 'recording_available', 'encoded_by')
    list_display_links = ('id', 'meeting_name')
    ordering = ('-id', '-date')
    readonly_fields = []


class BBBUserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'full_name', 'role', 'username',
        'meeting', 'user')
    list_display_links = ('id', 'full_name')
    ordering = ('full_name',)
    readonly_fields = []


admin.site.register(Meeting, MeetingAdmin)
admin.site.register(BBBUser, BBBUserAdmin)
