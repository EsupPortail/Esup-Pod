from django.contrib import admin

from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from .models import EncodingAudio, EncodingVideo, VideoRendition
from .models import EncodingLog
from .models import EncodingStep
from .models import PlaylistVideo
from pod.video.models import Video


@admin.register(EncodingVideo)
class EncodingVideoAdmin(admin.ModelAdmin):
    """Admin model for EncodingVideo."""

    list_display = ("video", "get_resolution", "encoding_format")
    list_filter = ["encoding_format", "rendition"]
    search_fields = ["id", "video__id", "video__title"]

    @admin.display(description="resolution")
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
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
