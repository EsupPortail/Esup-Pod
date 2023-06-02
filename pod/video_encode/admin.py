from django.contrib import admin

from pod.video.models import Video, VideoRendition
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from .models import EncodingAudio, EncodingVideo
from .models import EncodingLog
from .models import EncodingStep


class EncodingVideoAdmin(admin.ModelAdmin):
    list_display = ("video", "get_resolution", "encoding_format")
    list_filter = ["encoding_format", "rendition"]
    search_fields = ["id", "video__id", "video__title"]

    def get_resolution(self, obj):
        return obj.rendition.resolution

    get_resolution.short_description = "resolution"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        if (db_field.name) == "rendition":
            kwargs["queryset"] = VideoRendition.objects.filter(
                sites=Site.objects.get_current()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class EncodingAudioAdmin(admin.ModelAdmin):
    list_display = ("video", "encoding_format")
    list_filter = ["encoding_format"]
    search_fields = ["id", "video__id", "video__title"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class EncodingLogAdmin(admin.ModelAdmin):
    def video_id(self, obj):
        return obj.video.id

    list_display = (
        "id",
        "video_id",
        "video",
    )
    readonly_fields = ("video", "log")
    search_fields = ["id", "video__id", "video__title"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs


class EncodingStepAdmin(admin.ModelAdmin):
    list_display = ("video", "num_step", "desc_step")
    readonly_fields = ("video", "num_step", "desc_step")
    search_fields = ["id", "video__id", "video__title"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs


admin.site.register(EncodingVideo, EncodingVideoAdmin)
admin.site.register(EncodingAudio, EncodingAudioAdmin)
admin.site.register(EncodingLog, EncodingLogAdmin)
admin.site.register(EncodingStep, EncodingStepAdmin)
