from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Recording, Recorder, RecordingFile
from .models import RecordingFileTreatment


# Register your models here.

class RecordingAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'source_file', 'date_added')
    list_display_links = ('title',)
    list_filter = ('type',)


class RecordingFileTreatmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'file')


class RecorderAdmin(admin.ModelAdmin):
    def Description(self, obj):
        return mark_safe('%s' % obj.description)

    list_display = (
        'name', 'Description', 'address_ip', 'user', 'type', 'recording_type',
        'directory')
    list_display_links = ('name',)
    readonly_fields = []


class RecordingFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'type')
    # list_display_links = ('title',)
    list_filter = ('type',)


admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingFile, RecordingFileAdmin)
admin.site.register(RecordingFileTreatment, RecordingFileTreatmentAdmin)
admin.site.register(Recorder, RecorderAdmin)
