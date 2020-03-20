from django.contrib import admin

from .models import Building
from .models import Broadcaster
from django.contrib.sites.models import Site
from pod.live.forms import BuildingAdminForm
from .forms import BroadcasterAdminForm
from django.contrib.sites.shortcuts import get_current_site
from pod.video.models import Video

# Register your models here.


class BuildingAdmin(admin.ModelAdmin):
    form = BuildingAdminForm
    list_display = ('name', 'gmapurl')

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
        form = super(BuildingAdmin, self).get_form(request, obj, **kwargs)
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.sites.add(get_current_site(request))
            obj.save()

    class Media:
        css = {
            "all": (
                'bootstrap-4/css/bootstrap.min.css',
                'bootstrap-4/css/bootstrap-grid.css',
                'css/pod.css'
            )
        }
        js = (
            'js/main.js',
            'podfile/js/filewidget.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')


class BroadcasterAdmin(admin.ModelAdmin):
    form = BroadcasterAdminForm
    list_display = ('name', 'slug', 'building', 'url', 'status',
                    'is_restricted')
    readonly_fields = ["slug"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(building__sites=get_current_site(
                request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "building":
            kwargs["queryset"] = Building.objects.filter(
                    sites=Site.objects.get_current())
        if (db_field.name) == "video_on_hold":
            kwargs["queryset"] = Video.objects.filter(
                    sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {
            "all": (
                'bootstrap-4/css/bootstrap.min.css',
                'bootstrap-4/css/bootstrap-grid.css',
                'css/pod.css'
            )
        }
        js = (
            'js/main.js',
            'podfile/js/filewidget.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')


admin.site.register(Building, BuildingAdmin)
admin.site.register(Broadcaster, BroadcasterAdmin)
