from django.contrib import admin

from .models import Building
from .models import Broadcaster

from .forms import BuildingAdminForm
from .forms import BroadcasterAdminForm

# Register your models here.


class BuildingAdmin(admin.ModelAdmin):
    form = BuildingAdminForm
    list_display = ('name', 'gmapurl')

    class Media:
        css = {
            "all": (
                'css/podfile.css',
                'bootstrap-4/css/bootstrap-grid.css',
            )
        }
        js = (
            'js/filewidget.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')


class BroadcasterAdmin(admin.ModelAdmin):
    form = BroadcasterAdminForm

    list_display = ('name', 'slug', 'url', 'status', 'is_restricted')
    readonly_fields = ["slug"]

    class Media:
        css = {
            "all": (
                'css/podfile.css',
                'bootstrap-4/css/bootstrap-grid.css',
            )
        }
        js = (
            'js/filewidget.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')


admin.site.register(Building, BuildingAdmin)
admin.site.register(Broadcaster, BroadcasterAdmin)
