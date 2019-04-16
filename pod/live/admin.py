from django.contrib import admin

from .models import Building
from .models import Broadcaster

from .forms import BuildingForm

# Register your models here.


class BuildingAdmin(admin.ModelAdmin):
    change_form_template = 'progressbarupload/change_form.html'
    add_form_template = 'progressbarupload/change_form.html'

    form = BuildingForm
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
    list_display = ('name', 'slug', 'url', 'status', 'is_restricted')
    readonly_fields = ["slug"]


admin.site.register(Building, BuildingAdmin)
admin.site.register(Broadcaster, BroadcasterAdmin)
