from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from pod.video.models import Video
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline
from pod.video.models import VideoRendition
from pod.video.models import EncodingVideo
from pod.video.models import EncodingAudio
from pod.video.models import EncodingLog
from pod.video.models import PlaylistVideo

from pod.video.forms import VideoForm
from pod.video.forms import ChannelForm
from pod.video.forms import ThemeForm
from pod.video.forms import TypeForm
from pod.video.forms import DisciplineForm


# Register your models here.


class VideoAdmin(admin.ModelAdmin):
    form = VideoForm

    class Media:
        js = ('js/jquery.tools.min.js',)


class ChannelAdmin(TranslationAdmin):
    form = ChannelForm
    list_display = ('title', 'visible',)
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('owners', 'users',)
    list_editable = ('visible', )
    ordering = ('title',)

    class Media:
        js = ('js/jquery.tools.min.js',)


class TypeAdmin(TranslationAdmin):
    form = TypeForm
    prepopulated_fields = {'slug': ('title',)}

    class Media:
        js = ('js/jquery.tools.min.js',)


class DisciplineAdmin(TranslationAdmin):
    form = DisciplineForm
    prepopulated_fields = {'slug': ('title',)}

    class Media:
        js = ('js/jquery.tools.min.js',)


class ThemeAdmin(TranslationAdmin):
    form = ThemeForm
    list_display = ('title', 'channel')
    list_filter = ['channel']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('channel', 'title')

    class Media:
        js = ('js/jquery.tools.min.js',)


class EncodingVideoAdmin(admin.ModelAdmin):
    list_display = ('video', 'get_resolution', 'encoding_format')

    def get_resolution(self, obj):
        return obj.rendition.resolution
    get_resolution.short_description = 'resolution'


class EncodingAudioAdmin(admin.ModelAdmin):
    list_display = ('name', 'video', 'encoding_format')


class PlaylistVideoAdmin(admin.ModelAdmin):
    list_display = ('name', 'video', 'encoding_format')


class VideoRenditionAdmin(admin.ModelAdmin):
    list_display = (
        'resolution', 'video_bitrate', 'audio_bitrate', 'encode_mp4')


class EncodingLogAdmin(admin.ModelAdmin):
    list_display = ('video',)
    readonly_fields = ('video', 'log')


admin.site.register(Channel, ChannelAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(EncodingVideo, EncodingVideoAdmin)
admin.site.register(EncodingAudio, EncodingAudioAdmin)
admin.site.register(VideoRendition, VideoRenditionAdmin)
admin.site.register(EncodingLog, EncodingLogAdmin)
admin.site.register(PlaylistVideo, PlaylistVideoAdmin)
