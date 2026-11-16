from django.contrib import admin
from .models import CutVideo


@admin.register(CutVideo)
class CutVideoAdmin(admin.ModelAdmin):
    def start_seconds(self, obj):
        return obj.start.strftime("%H:%M:%S")

    def end_seconds(self, obj):
        return obj.end.strftime("%H:%M:%S")

    list_display = ("video", "start_seconds", "end_seconds")

    def has_add_permission(self, request, obj=None):
        return False
