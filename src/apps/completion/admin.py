"""
Esup-Pod - Completion admin.
"""

from django.contrib import admin
from src.apps.completion.models import (
    Contributor,
    Contribution,
    Document,
    Overlay,
    EnrichModelQueue,
)
from src.apps.video.admin import SubtitleAdmin


@admin.register(Contributor)
class ContributorAdmin(admin.ModelAdmin):
    """Admin interface for Contributor model."""

    list_display = ("last_name", "first_name", "email_address")
    search_fields = ("last_name", "first_name", "email_address")


@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    """Admin interface for Contribution model."""

    list_display = ("video", "contributor", "role")
    search_fields = ("video__title", "contributor__last_name")
    list_filter = ("role",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model."""

    list_display = ("title", "video", "is_private")
    search_fields = ("title", "video__title")
    list_filter = ("is_private",)


@admin.register(Overlay)
class OverlayAdmin(admin.ModelAdmin):
    """Admin interface for Overlay model."""

    list_display = ("title", "video", "time_start", "time_end")
    search_fields = ("title", "video__title")


@admin.register(EnrichModelQueue)
class EnrichModelQueueAdmin(admin.ModelAdmin):
    """Admin interface for EnrichModelQueue model."""

    list_display = ("track", "status", "added_at")
    list_filter = ("status",)
    actions = ["trigger_processing"]

    @admin.action(description="Trigger Processing (Celery)")
    def trigger_processing(self, request, queryset):
        """Action to trigger processing."""
        from src.apps.completion.tasks import process_enrich_model_queue

        queryset.update(status="pending")
        process_enrich_model_queue.delay()
        self.message_user(request, "Task triggered successfully.")


@admin.action(description="Enrich with selected subtitles (Kaldi/VOSK)")
def enrich_model_action(modeladmin, request, queryset):
    """Action to queue selected subtitles for model enrichment."""
    from src.apps.completion.models import EnrichModelQueue
    from src.apps.completion.tasks import process_enrich_model_queue

    count = 0
    for track in queryset:
        EnrichModelQueue.objects.get_or_create(
            video=track.video, track=track, defaults={"status": "pending"}
        )
        count += 1
    process_enrich_model_queue.delay()
    modeladmin.message_user(request, f"{count} subtitles queued for model enrichment.")


SubtitleAdmin.actions = list(getattr(SubtitleAdmin, "actions", [])) or []
if enrich_model_action not in SubtitleAdmin.actions:
    SubtitleAdmin.actions.append(enrich_model_action)
