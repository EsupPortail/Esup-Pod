from django.contrib import admin
from pod.video.models import Video
from pod.video.forms import VideoForm

# Register your models here.


class VideoAdmin(admin.ModelAdmin):

    form = VideoForm

    class Media:
        js = ('js/jquery.tools.min.js',)


admin.site.register(Video, VideoAdmin)
