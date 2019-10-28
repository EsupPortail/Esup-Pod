from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Recording, Recorder
from .models import RecordingFile


# Register your models here.

class RecordingAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'source_file', 'type', 'date_added')
    list_display_links = ('title',)
    list_filter = ('type',)


class RecordingFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'type')
    # list_display_links = ('title',)
    list_filter = ('type',)


class RecorderAdmin(admin.ModelAdmin):
    def Description(self, obj):
        return mark_safe('%s' % obj.description)

    list_display = (
        'name', 'Description', 'address_ip', 'user', 'type', 'directory')
    list_display_links = ('name',)
    readonly_fields = []


admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingFile, RecordingFileAdmin)
admin.site.register(Recorder, RecorderAdmin)
