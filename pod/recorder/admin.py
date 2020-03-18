import os

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from .models import Recording, Recorder, RecordingFile
from .models import RecordingFileTreatment
from django.contrib.sites.shortcuts import get_current_site

# Register your models here.


class RecordingAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'source_file', 'date_added')
    list_display_links = ('title',)
    list_filter = ('type',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(recorder__sites=get_current_site(
                request))
        return qs


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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(recorder__sites=get_current_site(
                request))
        return qs


class RecorderAdmin(admin.ModelAdmin):
    def Description(self, obj):
        return mark_safe('%s' % obj.description)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(
                request))
        return qs

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ('sites',)
            self.exclude = exclude
        form = super(RecorderAdmin, self).get_form(request, obj, **kwargs)
        return form

    list_display = (
        'name', 'Description', 'address_ip', 'user', 'type', 'recording_type',
        'directory')
    list_display_links = ('name',)
    readonly_fields = []


class RecordingFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'file', 'recorder')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(recorder__sites=get_current_site(
                request))
        return qs


admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingFile, RecordingFileAdmin)
admin.site.register(RecordingFileTreatment, RecordingFileTreatmentAdmin)
admin.site.register(Recorder, RecorderAdmin)
