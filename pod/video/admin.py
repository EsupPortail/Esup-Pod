from django.apps import apps
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

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
from pod.video.models import EncodingStep
from pod.video.models import PlaylistVideo

from pod.video.forms import VideoForm
from pod.video.forms import ChannelForm
from pod.video.forms import ThemeForm
from pod.video.forms import TypeForm
from pod.video.forms import DisciplineForm
from pod.completion.admin import ContributorInline
from pod.completion.admin import DocumentInline
from pod.completion.admin import OverlayInline
from pod.completion.admin import TrackInline
from pod.enrichment.admin import EnrichmentInline
if apps.is_installed('pod.filepicker'):
    FILEPICKER = True

# Ordering user by username !
User._meta.ordering = ["username"]


def url_to_edit_object(obj):
    url = reverse(
        'admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name),
        args=[obj.id])
    return format_html('<a href="{}">{}</a>', url, obj.username)

# Register your models here.


class VideoSuperAdminForm(VideoForm):
    is_staff = True
    is_superuser = True


class VideoAdminForm(VideoForm):
    is_staff = True
    is_superuser = False


class VideoAdmin(admin.ModelAdmin):
    change_form_template = 'progressbarupload/change_form.html'
    add_form_template = 'progressbarupload/change_form.html'

    list_display = ('id', 'title', 'get_owner_by_name', 'type', 'date_added',
                    'viewcount', 'is_draft', 'is_restricted',
                    'password', 'duration_in_time', 'encoding_in_progress',
                    'get_encoding_step', 'get_thumbnail_admin')
    list_display_links = ('id', 'title')
    list_filter = ('date_added', 'channel', 'type', 'is_draft')
    list_editable = ('is_draft', 'is_restricted')
    search_fields = ['id', 'title', 'video',
                     'owner__username', 'owner__first_name',
                     'owner__last_name']
    list_per_page = 20
    filter_horizontal = ('discipline', 'channel', 'theme',)
    readonly_fields = ('duration', 'encoding_in_progress',
                       'get_encoding_step')

    inlines = [
        ContributorInline,
        DocumentInline,
        TrackInline,
        OverlayInline,
        EnrichmentInline
    ]

    def get_owner_by_name(self, obj):
        owner = obj.owner
        url = url_to_edit_object(owner)
        return u'%s %s (%s)' % (owner.first_name, owner.last_name, url)

    get_owner_by_name.allow_tags = True
    get_owner_by_name.short_description = _('Owner')

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            kwargs['form'] = VideoSuperAdminForm
        else:
            kwargs['form'] = VideoAdminForm
        form = super(VideoAdmin, self).get_form(request, obj, **kwargs)
        return form

    class Media:
        js = ('js/jquery-3.3.1.min.js', 'js/jquery.overlay.js',)


class ChannelSuperAdminForm(ChannelForm):
    is_staff = True
    is_superuser = True
    admin_form = True


class ChannelAdminForm(ChannelForm):
    is_staff = True
    is_superuser = False
    admin_form = True


class ChannelAdmin(admin.ModelAdmin):

    def get_owners(self, obj):
        owners = []
        for owner in obj.owners.all():
            url = url_to_edit_object(owner)
            owners.append('%s %s (%s)' % (
                owner.first_name, owner.last_name, url))
        return ', '.join(owners)

    get_owners.allow_tags = True
    get_owners.short_description = _('Owners')

    list_display = ('title', 'get_owners', 'visible',)
    filter_horizontal = ('owners', 'users',)
    list_editable = ('visible', )
    ordering = ('title',)
    list_filter = ['visible']

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            kwargs['form'] = ChannelSuperAdminForm
        else:
            kwargs['form'] = ChannelAdminForm
        form = super(ChannelAdmin, self).get_form(request, obj, **kwargs)
        return form

    class Media:
        js = ('js/jquery-3.3.1.min.js', 'js/jquery.overlay.js',)


class ThemeAdmin(admin.ModelAdmin):
    form = ThemeForm
    list_display = ('title', 'channel')
    list_filter = ['channel']
    ordering = ('channel', 'title')

    class Media:
        js = ('js/jquery-3.3.1.min.js', 'js/jquery.overlay.js',)


class TypeAdmin(TranslationAdmin):
    form = TypeForm
    prepopulated_fields = {'slug': ('title',)}

    class Media:
        js = ('js/jquery-3.3.1.min.js', 'js/jquery.overlay.js',)


class DisciplineAdmin(TranslationAdmin):
    form = DisciplineForm
    prepopulated_fields = {'slug': ('title',)}

    class Media:
        js = ('js/jquery-3.3.1.min.js', 'js/jquery.overlay.js',)


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


class EncodingStepAdmin(admin.ModelAdmin):
    list_display = ('video',)
    readonly_fields = ('video', 'num_step', 'desc_step')


admin.site.register(Channel, ChannelAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(EncodingVideo, EncodingVideoAdmin)
admin.site.register(EncodingAudio, EncodingAudioAdmin)
admin.site.register(VideoRendition, VideoRenditionAdmin)
admin.site.register(EncodingLog, EncodingLogAdmin)
admin.site.register(EncodingStep, EncodingStepAdmin)
admin.site.register(PlaylistVideo, PlaylistVideoAdmin)
