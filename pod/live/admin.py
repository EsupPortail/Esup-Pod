from django.contrib import admin

from .models import Building
from .models import Broadcaster

# Register your models here.


class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'gmapurl')


class BroadcasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'url', 'status', 'is_restricted')
    readonly_fields = ["slug"]


admin.site.register(Building, BuildingAdmin)
admin.site.register(Broadcaster, BroadcasterAdmin)
