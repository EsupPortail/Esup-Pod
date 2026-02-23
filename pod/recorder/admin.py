"""Esup-Pod recorder administration."""

import os

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from pod.video.models import Type

from .models import Recorder, Recording, RecordingFile, RecordingFileTreatment

# Register your models here.

RECORDER_ADDITIONAL_FIELDS = getattr(settings, "RECORDER_ADDITIONAL_FIELDS", ())
USE_RUNNER_MANAGER = getattr(settings, "USE_RUNNER_MANAGER", False)


@admin.register(Recording)
class RecordingAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "source_file", "date_added")
    list_display_links = ("title",)
    list_filter = ("type",)
    autocomplete_fields = ["recorder", "user"]
    if USE_RUNNER_MANAGER:
        actions = ["encode_recording"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "recorder":
            kwargs["queryset"] = Recorder.objects.filter(
                sites=Site.objects.get_current()
            )
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

    @admin.action(description=_("Encode selected recordings and create new video"))
    def encode_recording(
        self, request: HttpRequest, queryset: QuerySet[Recording]
    ) -> None:
        """Encode selected studio recordings through Runner Manager.

        When Runner Manager is enabled, this admin action iterates over the
        selected recordings and starts encoding only for items with type
        ``studio``. It reports success, warnings for unsupported recording
        types, and processing errors through Django admin messages.
        """
        if USE_RUNNER_MANAGER:
            # Import here to avoid circular import
            from pod.video_encode_transcript.runner_manager import (
                encode_studio_recording,
            )

            for item in queryset:
                try:
                    if item.type == "studio":
                        self.message_user(
                            request,
                            _(f"Studio recording {item.id} encoding started"),
                            messages.SUCCESS,
                        )
                        # Encode studio recording via Runner Manager
                        encode_studio_recording(item.id)
                    else:
                        # Display a message to the admin user
                        self.message_user(
                            request,
                            _(
                                f"Recording {item.id} is not a studio recording and can’t be encoded"
                            ),
                            messages.WARNING,
                        )
                except Exception as e:
                    self.message_user(
                        request, _(f"Error for {item}: {e}"), messages.ERROR
                    )


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
            kwargs["queryset"] = Recorder.objects.filter(
                sites=Site.objects.get_current()
            )
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
            kwargs["queryset"] = Recorder.objects.filter(
                sites=Site.objects.get_current()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
