import requests
from django.contrib import admin, messages
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from pod.video.models import Video

from .models import (
    EncodingAudio,
    EncodingLog,
    EncodingStep,
    EncodingVideo,
    PlaylistVideo,
    RunnerManager,
    Task,
    VideoRendition,
)
from .task_queue import refresh_pending_task_ranks


@admin.register(EncodingVideo)
class EncodingVideoAdmin(admin.ModelAdmin):
    """Admin model for EncodingVideo."""

    list_display = ("video", "get_resolution", "encoding_format")
    list_filter = ["encoding_format", "rendition"]
    search_fields = ["id", "video__id", "video__title"]

    @admin.display(description=_("resolution"))
    def get_resolution(self, obj):
        """Get the resolution of the video rendition."""
        return obj.rendition.resolution

    def get_queryset(self, request):
        """Get the queryset based on the request."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize the form field for foreign keys."""
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        if (db_field.name) == "rendition":
            kwargs["queryset"] = VideoRendition.objects.filter(
                sites=Site.objects.get_current()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(EncodingAudio)
class EncodingAudioAdmin(admin.ModelAdmin):
    """Admin model for EncodingAudio."""

    list_display = ("video", "encoding_format")
    list_filter = ["encoding_format"]
    search_fields = ["id", "video__id", "video__title"]

    def get_queryset(self, request):
        """Get the queryset based on the request."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize the form field for foreign keys."""
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(EncodingLog)
class EncodingLogAdmin(admin.ModelAdmin):
    """Admin model for EncodingLog."""

    def video_id(self, obj):
        """Get the video ID."""
        return obj.video.id

    list_display = (
        "id",
        "video_id",
        "video",
    )
    readonly_fields = ("video", "log")
    search_fields = ["id", "video__id", "video__title"]

    def get_queryset(self, request):
        """Get the queryset based on the request."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs


@admin.register(EncodingStep)
class EncodingStepAdmin(admin.ModelAdmin):
    """Admin model for EncodingStep."""

    list_display = ("video", "num_step", "desc_step")
    readonly_fields = ("video", "num_step", "desc_step")
    search_fields = ["id", "video__id", "video__title"]

    def get_queryset(self, request):
        """Get the queryset based on the request."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs


@admin.register(VideoRendition)
class VideoRenditionAdmin(admin.ModelAdmin):
    """Admin model for VideoRendition."""

    list_display = (
        "resolution",
        "video_bitrate",
        "audio_bitrate",
        "encode_mp4",
    )

    def get_form(self, request, obj=None, **kwargs):
        """Get the form to be used in the admin."""
        if not request.user.is_superuser:
            exclude = ()
            exclude += ("sites",)
            self.exclude = exclude
        form = super(VideoRenditionAdmin, self).get_form(request, obj, **kwargs)
        return form

    def save_model(self, request, obj, form, change):
        """Save the VideoRendition model."""
        super().save_model(request, obj, form, change)
        if not change:
            obj.sites.add(get_current_site(request))
            obj.save()

    def get_queryset(self, request):
        """Get the queryset based on the request."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(request))
        return qs


@admin.register(PlaylistVideo)
class PlaylistVideoAdmin(admin.ModelAdmin):
    autocomplete_fields = ["video"]
    list_display = ("name", "video", "encoding_format")
    search_fields = ["id", "video__id", "video__title"]
    list_filter = ["encoding_format"]

    def get_queryset(self, request):
        """Limit queryset to objects linked to the current site for non-superusers."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restrict selectable videos to those available on the current site."""
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(RunnerManager)
class RunnerManagerAdmin(admin.ModelAdmin):
    """Administration for runner managers.

    Args:
        admin (ModelAdmin): admin model
    """

    change_form_template = "admin_test_connection.html"

    list_display = (
        "id",
        "name",
        "priority",
        "url",
        "site",
    )
    list_display_links = ("id", "name")
    ordering = ("-id", "priority")
    readonly_fields = []
    search_fields = ["id", "name", "site"]

    def get_urls(self):
        """Register the custom admin endpoint used to test runner connectivity."""
        custom_urls = [
            path(
                "<path:object_id>/test-connection/",
                self.admin_site.admin_view(self.test_connection_view),
                name="video_encode_transcript_runnermanager_test_connection",
            ),
        ]
        return custom_urls + super().get_urls()

    def _health_url(self, runner_manager: RunnerManager) -> str:
        """Build runner manager health endpoint URL."""
        return (
            runner_manager.url + "manager/health"
            if runner_manager.url.endswith("/")
            else runner_manager.url + "/manager/health"
        )

    def _auth_headers(self, runner_manager: RunnerManager) -> dict[str, str]:
        """Build headers used for the runner manager availability check."""
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {runner_manager.token}",
        }

    def _change_url(self, runner_manager: RunnerManager) -> str:
        """Build the admin change URL for a runner manager instance."""
        return reverse(
            "admin:video_encode_transcript_runnermanager_change",
            args=[runner_manager.pk],
        )

    def test_connection_view(self, request, object_id):
        """Call the runner health endpoint and show the result in admin messages."""
        runner_manager = self.get_object(request, object_id)
        if runner_manager is None:
            self.message_user(
                request,
                _("Runner manager not found."),
                level=messages.ERROR,
            )
            return HttpResponseRedirect(
                reverse("admin:video_encode_transcript_runnermanager_changelist")
            )
        if not self.has_change_permission(request, runner_manager):
            raise PermissionDenied

        health_url = self._health_url(runner_manager)
        try:
            response = requests.get(
                health_url,
                headers=self._auth_headers(runner_manager),
                timeout=15,
            )
        except requests.RequestException as exc:
            self.message_user(
                request,
                _(
                    "Unable to reach runner manager '%(name)s' at %(url)s. "
                    "Check the URL and network access. Error: %(error)s"
                )
                % {
                    "name": runner_manager.name,
                    "url": runner_manager.url,
                    "error": str(exc),
                },
                level=messages.ERROR,
            )
            return HttpResponseRedirect(self._change_url(runner_manager))

        if response.status_code in (401, 403):
            self.message_user(
                request,
                _(
                    "Runner manager '%(name)s' responded but rejected authentication "
                    "(HTTP %(status)s). Check the bearer token."
                )
                % {"name": runner_manager.name, "status": response.status_code},
                level=messages.ERROR,
            )
        elif response.status_code in (200, 204):
            self.message_user(
                request,
                _(
                    "Connection to runner manager '%(name)s' succeeded "
                    "(HTTP %(status)s)."
                )
                % {"name": runner_manager.name, "status": response.status_code},
                level=messages.SUCCESS,
            )
        elif response.status_code == 404:
            self.message_user(
                request,
                _(
                    "Runner manager '%(name)s' is reachable but endpoint %(url)s "
                    "was not found (HTTP 404). Check the configured URL."
                )
                % {"name": runner_manager.name, "url": health_url},
                level=messages.ERROR,
            )
        else:
            self.message_user(
                request,
                _(
                    "Runner manager '%(name)s' is reachable but returned an "
                    "unexpected response (HTTP %(status)s)."
                )
                % {"name": runner_manager.name, "status": response.status_code},
                level=messages.WARNING,
            )

        return HttpResponseRedirect(self._change_url(runner_manager))


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Administration for runner manager tasks.

    Args:
        admin (ModelAdmin): admin model
    """

    list_display = (
        "id",
        "video_id_display",
        "video_label",
        "recording_id_display",
        "recording_label",
        "type",
        "status_badge",
        "task_id",
        "date_added",
        "runner_manager",
    )
    list_display_links = ("id",)
    ordering = ("-id",)
    readonly_fields = ["date_added"]
    fields = (
        "type",
        "status",
        "date_added",
        "task_id",
        "video",
        "recording",
        "runner_manager",
        "script_output",
    )
    search_fields = ["id", "video__id", "runner_manager__name"]
    actions = ["relaunch_selected_tasks"]

    def get_readonly_fields(self, request, obj=None):
        """Keep type and status immutable after task creation."""
        if obj is None:
            return self.readonly_fields
        return [*self.readonly_fields, "type", "status"]

    def _truncate_label(self, label):
        """Return a short label for list display."""
        return Truncator(label).chars(50)

    @admin.display(description="Video ID", ordering="video__id")
    def video_id_display(self, obj):
        """Display the related video identifier, or '-' when absent."""
        if not obj.video_id:
            return "-"
        return obj.video_id

    @admin.display(description="Video", ordering="video__title")
    def video_label(self, obj):
        """Display a truncated video title, or '-' when no video is linked."""
        if not obj.video_id:
            return "-"
        return self._truncate_label(obj.video.title)

    @admin.display(description="Recording ID", ordering="recording__id")
    def recording_id_display(self, obj):
        """Display the related recording identifier, or '-' when absent."""
        if not obj.recording_id:
            return "-"
        return obj.recording_id

    @admin.display(description="Recording", ordering="recording__title")
    def recording_label(self, obj):
        """Display a truncated recording title, or '-' when not linked."""
        if not obj.recording_id:
            return "-"
        return self._truncate_label(obj.recording.title)

    @admin.display(description="Statut", ordering="status")
    def status_badge(self, obj):
        """Render task status with a colored badge in list display."""
        badge_map = {
            "pending": "bg-secondary",
            "running": "bg-warning text-dark",
            "failed": "bg-danger",
            "timeout": "bg-danger",
            "completed": "bg-success",
        }
        badge_class = badge_map.get(obj.status, "bg-secondary")
        status_label = obj.get_status_display()
        return format_html(
            '<span class="badge {}">{}</span>',
            badge_class,
            status_label,
        )

    @admin.action(description=_("Restart selected tasks"))
    def relaunch_selected_tasks(self, request, queryset):
        """Reset selected tasks and relaunch one job per unique source."""
        from .runner_manager import (
            encode_studio_recording,
            encode_video,
            transcript_video,
        )

        relaunched_count = 0
        skipped_count = 0
        launched_sources = set()

        for task in queryset:
            source_key = (task.type, task.video_id, task.recording_id)
            if source_key in launched_sources:
                skipped_count += 1
                continue

            # Force selected task as pending so runner_manager helpers update this row
            # instead of creating a new pending task.
            task.status = "pending"
            task.task_id = None
            task.runner_manager = None
            task.rank = None
            task.script_output = None
            task.date_added = timezone.now()
            task.save(
                update_fields=[
                    "status",
                    "task_id",
                    "runner_manager",
                    "rank",
                    "script_output",
                    "date_added",
                ]
            )

            if task.type == "encoding" and task.video_id:
                encode_video(task.video_id)
            elif task.type == "transcription" and task.video_id:
                transcript_video(task.video_id)
            elif task.type == "studio" and task.recording_id:
                encode_studio_recording(task.recording_id)
            else:
                skipped_count += 1
                continue

            launched_sources.add(source_key)
            relaunched_count += 1

        refresh_pending_task_ranks()
        self.message_user(
            request,
            _("%(count)s task(s) relaunched immediately.")
            % {"count": relaunched_count},
            level=messages.SUCCESS,
        )
        if skipped_count:
            self.message_user(
                request,
                _("%(count)s task(s) skipped (duplicate or missing source).")
                % {"count": skipped_count},
                level=messages.WARNING,
            )
