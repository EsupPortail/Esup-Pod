from django.conf import settings
from django.contrib import admin
from .models import Enrichment, EnrichmentGroup, EnrichmentVtt
from .forms import EnrichmentAdminForm, EnrichmentVttAdminForm
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from pod.video.models import Video
from django.contrib.auth.models import Group

USE_PODFILE = getattr(settings, "USE_PODFILE", False)


class EnrichmentInline(admin.TabularInline):
    model = Enrichment
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False


class EnrichmentAdmin(admin.ModelAdmin):
    form = EnrichmentAdminForm
    list_display = (
        "title",
        "type",
        "video",
    )
    autocomplete_fields = ["video"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {
            "all": (
                # "bootstrap/dist/css/bootstrap.min.css",
                # "bootstrap/dist/css/bootstrap-grid.min.css",
                # "css/pod.css",
            )
        }
        js = (
            "js/main.js",
            "podfile/js/filewidget.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )


if USE_PODFILE:
    admin.site.register(Enrichment, EnrichmentAdmin)
else:
    admin.site.register(Enrichment)


@admin.register(EnrichmentGroup)
class EnrichmentGroupAdmin(admin.ModelAdmin):
    list_display = ("video", "get_groups")
    autocomplete_fields = ["video"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if (db_field.name) == "groups":
            kwargs["queryset"] = Group.objects.filter(
                groupsite__sites=Site.objects.get_current()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # class Media:
    #     css = {"all": ("css/pod.css",)}

    def get_groups(self, obj):
        return "\n".join([g.name for g in obj.groups.all()])


@admin.register(EnrichmentVtt)
class EnrichmentVttAdmin(admin.ModelAdmin):
    form = EnrichmentVttAdminForm
    list_display = ("video", "src", "get_file_name")
    readonly_fields = ("video",)

    def get_file_name(self, obj):
        return obj.src.file.name

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    class Media:
        css = {
            "all": (
                # "bootstrap/dist/css/bootstrap.min.css",
                # "bootstrap/dist/css/bootstrap-grid.min.css",
                # "css/pod.css",
            )
        }
        js = (
            "js/main.js",
            "podfile/js/filewidget.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )
