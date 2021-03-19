from django.contrib import admin
from .models import Meeting, Attendee, Livestream
from .forms import MeetingForm
from django.utils.translation import ugettext_lazy as _


class MeetingAdminForm(MeetingForm):
    is_staff: bool = True
    is_superuser: bool = False
    is_admin: bool = True


class MeetingSuperAdminForm(MeetingAdminForm):
    is_superuser: bool = True
    encoding_step: int = 1


class MeetingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'session_date', 'meeting_name', 'encoding_step',
        'recorded', 'recording_available', 'encoded_by')
    list_display_links = ('id', 'meeting_name')
    ordering = ('-id', '-session_date')
    readonly_fields = []
    search_fields = ['id', 'meeting_name', 'encoded_by__username',
                     'encoded_by__first_name', 'encoded_by__last_name']

    actions = ['encode_video']

    # Re-encode a BBB presentation Web
    def encode_video(self, request, queryset):
        for item in queryset:
            item.launch_encode = True
            item.save()
    encode_video.short_description = _('Encode selected')


class AttendeeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'full_name', 'role', 'username',
        'meeting', 'user')
    list_display_links = ('id', 'full_name')
    ordering = ('full_name',)
    readonly_fields = []
    search_fields = ['id', 'full_name', 'meeting__meeting_name']


class LivestreamAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'meeting', 'start_date', 'end_date',
        'show_chat', 'download_meeting', 'enable_chat',
        'server', 'status', 'user')
    list_display_links = ('id', 'meeting')
    ordering = ('-id', '-start_date')
    readonly_fields = []
    search_fields = ['id', 'meeting__meeting_name', 'user__username',
                     'user__first_name', 'user__last_name']


admin.site.register(Meeting, MeetingAdmin)
admin.site.register(Attendee, AttendeeAdmin)
admin.site.register(Livestream, LivestreamAdmin)
