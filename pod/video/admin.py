from django.apps import apps
from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from pod.video.models import Video
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline
from pod.video.forms import VideoForm
from pod.video.forms import ChannelForm
from pod.video.forms import ThemeForm
from pod.video.forms import TypeForm
from pod.video.forms import DisciplineForm
from pod.completion.admin import ContributorInline
from pod.completion.admin import DocumentInline
from pod.completion.admin import OverlayInline
from pod.completion.admin import TrackInline
if apps.is_installed('pod.filepicker'):
    FILEPICKER = True

# Register your models here.


class VideoAdmin(admin.ModelAdmin):

    form = VideoForm
    inlines = [
        ContributorInline,
        DocumentInline,
        TrackInline,
        OverlayInline
    ]

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


class ThemeAdmin(admin.ModelAdmin):
    form = ThemeForm
    list_display = ('title', 'channel')
    list_filter = ['channel']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('channel', 'title')

    class Media:
        js = ('js/jquery.tools.min.js',)

admin.site.register(Channel, ChannelAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(Video, VideoAdmin)