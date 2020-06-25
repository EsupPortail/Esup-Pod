import os

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from .models import Recording, Recorder, RecordingFile
from .models import RecordingFileTreatment
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from pod.video.models import Type

# Register your models here.


class RecordingAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'source_file', 'date_added')
    list_display_links = ('title',)
    list_filter = ('type',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "recorder":
            kwargs["queryset"] = Recorder.objects.filter(
                    sites=Site.objects.get_current())
        if (db_field.name) == "user":
            kwargs["queryset"] = User.objects.filter(
                    owner__sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "recorder":
            kwargs["queryset"] = Recorder.objects.filter(
                    sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "user":
            kwargs["queryset"] = User.objects.filter(
                    owner__sites=Site.objects.get_current())
        if (db_field.name) == "type":
            kwargs["queryset"] = Type.objects.filter(
                    sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ('sites',)
            self.exclude = exclude
        form = super(RecorderAdmin, self).get_form(request, obj, **kwargs)
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.sites.add(get_current_site(request))
            obj.save()

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "recorder":
            kwargs["queryset"] = Recorder.objects.filter(
                    sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Recording, RecordingAdmin)
admin.site.register(RecordingFile, RecordingFileAdmin)
admin.site.register(RecordingFileTreatment, RecordingFileTreatmentAdmin)
admin.site.register(Recorder, RecorderAdmin)
