from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from pod.video.models import Video
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline
from pod.video.forms import VideoForm
from pod.completion.admin import ContributorInline
from pod.completion.admin import DocumentInline
from pod.completion.admin import OverlayInline
try:
    __import__('pod.filepicker')
    FILEPICKER = True
except:
    FILEPICKER = False
    pass

# Register your models here.


class VideoAdmin(admin.ModelAdmin):

    form = VideoForm
    inlines = [
        ContributorInline,
        DocumentInline,
        OverlayInline
    ]

    class Media:
        js = ('js/jquery.tools.min.js',)


class ChannelAdmin(TranslationAdmin):
    list_display = ('title', 'visible',)
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('owners', 'users',)
    list_editable = ('visible', )
    ordering = ('title',)


class TypeAdmin(TranslationAdmin):
    prepopulated_fields = {'slug': ('title',)}


class DisciplineAdmin(TranslationAdmin):
    prepopulated_fields = {'slug': ('title',)}


class ThemeAdmin(TranslationAdmin):
    list_display = ('title', 'channel')
    list_filter = ['channel']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('channel', 'title')


admin.site.register(Channel, ChannelAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Theme, ThemeAdmin)
if FILEPICKER:
    admin.site.register(Video, VideoAdmin)
else:
    admin.site.register(Video)
