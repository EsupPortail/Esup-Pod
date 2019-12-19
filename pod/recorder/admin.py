import os

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from .models import Recording, Recorder, RecordingFile
from .models import RecordingFileTreatment


# Register your models here.

class RecordingAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'source_file', 'date_added')
    list_display_links = ('title',)
    list_filter = ('type',)


class RecordingFileTreatmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'file')
    actions = ['delete_source']

    def delete_source(self, request, queryset):
        for item in queryset:
            if os.path.exists(item.file):
                os.remove(item.file)
            item.delete()
    delete_source.short_description = _('Delete selected Recording file '
                                        'treatments + source files')


class RecorderAdmin(admin.ModelAdmin):
    def Description(self, obj):
        return mark_safe('%s' % obj.description)

    list_display = (
        'name', 'Description', 'address_ip', 'user', 'type', 'recording_type',
        'directory')
    list_display_links = ('name',)
    readonly_fields = []


class RecordingFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'recorder')


admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingFile, RecordingFileAdmin)
admin.site.register(RecordingFileTreatment, RecordingFileTreatmentAdmin)
admin.site.register(Recorder, RecorderAdmin)
