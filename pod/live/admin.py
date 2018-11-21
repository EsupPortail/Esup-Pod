from django.contrib import admin

from .models import Building
from .models import Broadcaster

# Register your models here.


class BuildingAdmin(admin.ModelAdmin):
    list_display = ('name', 'gmapurl')


class BroadcasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'status', 'is_restricted')


admin.site.register(Building, BuildingAdmin)
admin.site.register(Broadcaster, BroadcasterAdmin)
