"""Esup-Pod recorder administration."""

import os
from django.conf import settings
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from .models import Recording, Recorder, RecordingFile
from .models import RecordingFileTreatment
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from pod.video.models import Type

# Register your models here.

RECORDER_ADDITIONAL_FIELDS = getattr(settings, "RECORDER_ADDITIONAL_FIELDS", ())


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "source_file", "date_added")
    list_display_links = ("title",)
    list_filter = ("type",)
    autocomplete_fields = ["recorder", "user"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "recorder":
            kwargs["queryset"] = Recorder.objects.filter(sites=Site.objects.get_current())
        if (db_field.name) == "user":
            kwargs["queryset"] = User.objects.filter(
                owner__sites=Site.objects.get_current()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(recorder__sites=get_current_site(request))
        return qs


@admin.register(RecordingFileTreatment)
class RecordingFileTreatmentAdmin(admin.ModelAdmin):
    list_display = ("id", "file")
    actions = ["delete_source"]
    autocomplete_fields = ["recorder"]

    @admin.action(
        description=_("Delete selected Recording file treatments + source files")
    )
    def delete_source(self, request, queryset) -> None:
        for item in queryset:
            if os.path.exists(item.file):
                os.remove(item.file)
            item.delete()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "recorder":
            kwargs["queryset"] = Recorder.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(recorder__sites=get_current_site(request))
        return qs


@admin.register(Recorder)
class RecorderAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    autocomplete_fields = [
        "user",
        "additional_users",
        "type",
        "discipline",
        "channel",
        "theme",
    ]

    def Description(self, obj):
        return mark_safe("%s" % obj.description)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "user":
            kwargs["queryset"] = User.objects.filter(
                owner__sites=Site.objects.get_current()
            )
        if (db_field.name) == "type":
            kwargs["queryset"] = Type.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        exclude = ()
        available_fields = (
            "additional_users",
            "is_draft",
            "password",
            "is_restricted",
            "restrict_access_to_groups",
            "cursus",
            "main_lang",
            "tags",
            "discipline",
            "licence",
            "channel",
            "theme",
            "transcript",
            "allow_downloading",
            "is_360",
            "disable_comment",
        )
        for f in available_fields:
            if f not in RECORDER_ADDITIONAL_FIELDS:
                exclude += (f,)
        if (
            not getattr(settings, "USE_TRANSCRIPTION", False)
            and "transcript" not in exclude
        ):
            exclude += ("transcript",)
        if not request.user.is_superuser:
            exclude += ("sites",)

        self.exclude = exclude
        form = super(RecorderAdmin, self).get_form(request, obj, **kwargs)
        return form

    def save_model(self, request, obj, form, change) -> None:
        super().save_model(request, obj, form, change)
        if not change:
            obj.sites.add(get_current_site(request))
            obj.save()

    list_display = (
        "name",
        "Description",
        "address_ip",
        "credentials_login",
        "user",
        "type",
        "recording_type",
        "directory",
    )
    list_display_links = ("name",)
    readonly_fields = []


@admin.register(RecordingFile)
class RecordingFileAdmin(admin.ModelAdmin):
    list_display = ("id", "file", "recorder")
    autocomplete_fields = ["recorder"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(recorder__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "recorder":
            kwargs["queryset"] = Recorder.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
