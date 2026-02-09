from django.contrib import admin
from src.apps.video.models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'status', 'created_at', 'file_size_mb')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'owner__username', 'owner__email')
    readonly_fields = ('slug', 'duration', 'created_at', 'updated_at')

    def file_size_mb(self, obj):
        if obj.video_file and hasattr(obj.video_file, 'size'):
            return f"{obj.video_file.size / (1024 * 1024):.2f} MB"
        return "N/A"
    file_size_mb.short_description = "Size (MB)"
