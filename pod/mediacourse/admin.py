from django.contrib import admin
from django.utils.html import *
from django.utils.text import mark_safe

from .models import Recording, Recorder, Job


class JobAdmin(admin.ModelAdmin):
    list_display = ('mediapath', 'file_size', 'date_added', 'email_sent', 'date_email_sent', 'require_manual_claim')
    list_display_links = ('mediapath',)
    list_filter = ('email_sent',)
    readonly_fields = ('date_added', 'date_email_sent')


class RecordingAdmin(admin.ModelAdmin):
    list_display = ('title', 'recorder', 'mediapath', 'date_added')
    list_display_links = ('title',)
    list_filter = ('recorder',)


class RecorderAdmin(admin.ModelAdmin):
    def Description(self, obj):
        return mark_safe('%s' % obj.description)

    list_display = ('name', 'Description', 'address_ip', 'user', 'type', 'directory')
    list_display_links = ('name',)
    list_filter = ('user',)
    readonly_fields = []


admin.site.register(Job, JobAdmin)
admin.site.register(Recording, RecordingAdmin)
admin.site.register(Recorder, RecorderAdmin)
