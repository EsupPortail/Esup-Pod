"""Esup-Pod speaker admin."""

from django.contrib import admin
from pod.speaker.models import Speaker, Job, JobVideo


class JobInline(admin.StackedInline):
    """Inline configuration for Job."""

    model = Job
    extra = 0
    can_delete = True


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    """Admin configuration for Speaker."""

    list_display = ("firstname", "lastname")
    inlines = [JobInline]


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin configuration for Job."""

    list_display = ("title", "speaker")
    list_filter = ("speaker",)
    search_fields = ("title", "speaker__firstname", "speaker__lastname")


@admin.register(JobVideo)
class JobVideoAdmin(admin.ModelAdmin):
    """Admin configuration for Video speaker by job."""

    list_display = ("job", "video")
    list_filter = ("job", "video")
    search_fields = ("job__title", "video__title")
