from django.contrib import admin

from .models import Recording
from .models import RecordingFile

# Register your models here.


class RecordingAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'source_file', 'type', 'date_added')
    list_display_links = ('title',)
    list_filter = ('user', 'type')


class RecordingFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'type')
    # list_display_links = ('title',)
    list_filter = ('type',)


admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingFile, RecordingFileAdmin)
