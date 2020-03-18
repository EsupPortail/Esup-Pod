from django.contrib import admin

from .models import Building
from .models import Broadcaster

from pod.live.forms import BuildingAdminForm
from .forms import BroadcasterAdminForm
from django.contrib.sites.shortcuts import get_current_site


# Register your models here.


class BuildingSuperAdminForm(BuildingAdminForm):
    is_staff = True
    is_superuser = True
    admin_form = True


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
        if request.user.is_superuser:
            kwargs['form'] = BuildingSuperAdminForm
        else:
            kwargs['form'] = BuildingAdminForm
        form = super(BuildingAdmin, self).get_form(request, obj, **kwargs)
        return form

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
