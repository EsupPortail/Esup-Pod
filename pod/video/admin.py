from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from modeltranslation.admin import TranslationAdmin
from .models import Video
from .models import Channel
from .models import Theme
from .models import Type
from .models import Discipline
from .models import VideoRendition
from .models import EncodingVideo
from .models import EncodingAudio
from .models import EncodingLog
from .models import EncodingStep
from .models import PlaylistVideo
from .models import Notes, AdvancedNotes, NoteComments
from .models import ViewCount
from .models import VideoToDelete
from .models import VideoVersion
from .transcript import start_transcript

from .forms import VideoForm, VideoVersionForm
from .forms import ChannelForm
from .forms import ThemeForm
from .forms import TypeForm
from .forms import DisciplineForm

from pod.completion.admin import ContributorInline
from pod.completion.admin import DocumentInline
from pod.completion.admin import OverlayInline
from django.contrib.sites.models import Site
from pod.completion.admin import TrackInline
from django.contrib.sites.shortcuts import get_current_site
from pod.chapter.admin import ChapterInline

from pod.main.tasks import task_start_transcript

# Ordering user by username !
User._meta.ordering = ["username"]
# SET USE_ESTABLISHMENT_FIELD
USE_ESTABLISHMENT_FIELD = getattr(
    settings, 'USE_ESTABLISHMENT_FIELD', False)

TRANSCRIPT = getattr(settings, 'USE_TRANSCRIPTION', False)

USE_OBSOLESCENCE = getattr(
    settings, "USE_OBSOLESCENCE", False)

CELERY_TO_ENCODE = getattr(settings, 'CELERY_TO_ENCODE', False)


def url_to_edit_object(obj):
    url = reverse(
        'admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name),
        args=[obj.id])
    return format_html('<a href="{}">{}</a>', url, obj.username)

# Register your models here.


class EncodedFilter(admin.SimpleListFilter):
    title = _('Encoded ?')
    parameter_name = 'encoded'

    def lookups(self, request, model_admin):
        return (
            ('Yes', _('Yes')),
            ('No', _('No')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'Yes':
            queryset = queryset.exclude(
                    pk__in=[vid.id for vid in queryset if not vid.encoded])
        elif value == 'No':
            queryset = queryset.exclude(
                    pk__in=[vid.id for vid in queryset if vid.encoded])
        return queryset


class VideoSuperAdminForm(VideoForm):
    is_staff = True
    is_superuser = True
    is_admin = True
    admin_form = True


class VideoAdminForm(VideoForm):
    is_staff = True
    is_superuser = False
    is_admin = True
    admin_form = True


class VideoVersionInline(admin.StackedInline):
    model = VideoVersion
    form = VideoVersionForm
    can_delete = False


class VideoAdmin(admin.ModelAdmin):
    change_form_template = 'progressbarupload/change_form.html'
    add_form_template = 'progressbarupload/change_form.html'

    list_display = ('id', 'title', 'get_owner_by_name', 'type', 'date_added',
                    'viewcount', 'is_draft', 'is_restricted',
                    'password', 'duration_in_time', 'encoding_in_progress',
                    'get_encoding_step', 'get_thumbnail_admin')
    list_display_links = ('id', 'title')
    list_filter = ('date_added', ('channel', admin.RelatedOnlyFieldListFilter),
                   ('type', admin.RelatedOnlyFieldListFilter), 'is_draft',
                   'encoding_in_progress', EncodedFilter)
    # Ajout de l'attribut 'date_delete'
    if USE_OBSOLESCENCE:
        list_filter = list_filter + ("date_delete",)
        list_display = list_display + ("date_delete",)

    list_editable = ('is_draft', 'is_restricted')
    search_fields = ['id', 'title', 'video',
                     'owner__username', 'owner__first_name',
                     'owner__last_name']
    list_per_page = 20
    filter_horizontal = ('discipline', 'channel', 'theme',)
    readonly_fields = ('duration', 'encoding_in_progress',
                       'get_encoding_step')

    inlines = []

    inlines += [
        VideoVersionInline,
        ContributorInline,
        DocumentInline,
        TrackInline,
        OverlayInline
    ]

    inlines += [
        ChapterInline
    ]

    def get_owner_establishment(self, obj):
        owner = obj.owner
        return owner.owner.establishment
    get_owner_establishment.short_description = _('Establishment')

    # Ajout de l'attribut 'establishment'
    if USE_ESTABLISHMENT_FIELD:
        list_filter = list_filter + ("owner__owner__establishment",)
        list_display = list_display + ("get_owner_establishment",)
        search_fields.append("owner__owner__establishment",)

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
        exclude = ()
        if obj and obj.encoding_in_progress:
            exclude += ('video', 'owner',)
        if not TRANSCRIPT:
            exclude += ('transcript',)
        if (request.user.is_staff is False
                or obj is None
                or USE_OBSOLESCENCE is False):
            exclude += ('date_delete',)
        if not request.user.is_superuser:
            exclude += ('sites',)
        self.exclude = exclude
        form = super(VideoAdmin, self).get_form(request, obj, **kwargs)
        return form

    actions = ['encode_video', 'transcript_video']

    def encode_video(self, request, queryset):
        for item in queryset:
            item.launch_encode = True
            item.save()
    encode_video.short_description = _('Encode selected')

    def transcript_video(self, request, queryset):
        for item in queryset:
            if item.get_video_mp3() and not item.encoding_in_progress:
                if CELERY_TO_ENCODE:
                    task_start_transcript.delay(item.id)
                else:
                    start_transcript(item.id)
    transcript_video.short_description = _('Transcript selected')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(
                request))
        return qs

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['max_duration_date_delete'] = getattr(
                settings, 'MAX_DURATION_DATE_DELETE', 10)
        return super(VideoAdmin, self).change_view(
                request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.sites.add(get_current_site(request))
            obj.save()

    class Media:
        css = {
            "all": (
                'css/pod.css',
                'bootstrap-4/css/bootstrap.min.css',
                'bootstrap-4/css/bootstrap-grid.css'
            )
        }
        js = (
            'podfile/js/filewidget.js',
            'js/main.js',
            'js/validate-date_delete-field.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')


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

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ('sites',)
        else:
            return ()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.sites.add(get_current_site(request))
            obj.save()

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            kwargs['form'] = ChannelSuperAdminForm
        else:
            kwargs['form'] = ChannelAdminForm

        form = super(ChannelAdmin, self).get_form(request, obj, **kwargs)
        return form

    class Media:
        css = {
            "all": (
                'bootstrap-4/css/bootstrap.min.css',
                'bootstrap-4/css/bootstrap-grid.css',
                'css/pod.css'
            )
        }
        js = (
            'js/main.js',
            'podfile/js/filewidget.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(
                request))
        return qs


class ThemeAdmin(admin.ModelAdmin):
    form = ThemeForm
    list_display = ('title', 'channel')
    list_filter = (('channel', admin.RelatedOnlyFieldListFilter),)
    ordering = ('channel', 'title')

    class Media:
        css = {
            "all": (
                'bootstrap-4/css/bootstrap.min.css',
                'bootstrap-4/css/bootstrap-grid.css',
                'css/pod.css'
            )
        }
        js = (
            'js/main.js',
            'podfile/js/filewidget.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(channel__sites=get_current_site(
                request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "parentId":
            kwargs["queryset"] = Theme.objects.filter(
                    channel__sites=Site.objects.get_current())
        if (db_field.name) == "channel":
            kwargs["queryset"] = Channel.objects.filter(
                    sites=Site.objects.get_current())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TypeAdmin(TranslationAdmin):
    form = TypeForm
    prepopulated_fields = {'slug': ('title',)}

    class Media:
        css = {
            "all": (
                'bootstrap-4/css/bootstrap.min.css',
                'bootstrap-4/css/bootstrap-grid.css',
                'css/pod.css'
            )
        }
        js = (
            'js/main.js',
            'podfile/js/filewidget.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ('sites',)
            self.exclude = exclude
        form = super(TypeAdmin, self).get_form(request, obj, **kwargs)
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.sites.add(get_current_site(request))
            obj.save()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(
                request))
        return qs


class DisciplineAdmin(TranslationAdmin):
    form = DisciplineForm
    prepopulated_fields = {'slug': ('title',)}

    class Media:
        css = {
            "all": (
                'bootstrap-4/css/bootstrap-grid.css',
                'bootstrap-4/css/bootstrap.min.css',
                'css/pod.css'
            )
        }
        js = (
            'js/main.js',
            'podfile/js/filewidget.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ('sites',)
            self.exclude = exclude
        form = super(DisciplineAdmin, self).get_form(request, obj, **kwargs)
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.sites.add(get_current_site(request))
            obj.save()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(
                request))
        return qs


class EncodingVideoAdmin(admin.ModelAdmin):
    list_display = ('video', 'get_resolution', 'encoding_format')

    def get_resolution(self, obj):
        return obj.rendition.resolution
    get_resolution.short_description = 'resolution'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(
                request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(
                    sites=Site.objects.get_current())
        if (db_field.name) == "rendition":
            kwargs["queryset"] = VideoRendition.objects.filter(
                    sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class EncodingAudioAdmin(admin.ModelAdmin):
    list_display = ('name', 'video', 'encoding_format')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(
                request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(
                    sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PlaylistVideoAdmin(admin.ModelAdmin):
    list_display = ('name', 'video', 'encoding_format')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(
                request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(
                    sites=Site.objects.get_current())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class VideoRenditionAdmin(admin.ModelAdmin):
    list_display = (
        'resolution', 'video_bitrate', 'audio_bitrate', 'encode_mp4')

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ('sites',)
            self.exclude = exclude
        form = super(VideoRenditionAdmin, self).get_form(
            request, obj, **kwargs)
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.sites.add(get_current_site(request))
            obj.save()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(
                request))
        return qs


class EncodingLogAdmin(admin.ModelAdmin):
    list_display = ('video',)
    readonly_fields = ('video', 'log')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(
                request))
        return qs


class EncodingStepAdmin(admin.ModelAdmin):
    list_display = ('video',)
    readonly_fields = ('video', 'num_step', 'desc_step')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(
                request))
        return qs


class NotesAdmin(admin.ModelAdmin):
    list_display = ('video', 'user')

    class Media:
        css = {
            "all": (
                'css/pod.css',
            )
        }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(
                request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "user":
            kwargs["queryset"] = User.objects.filter(
                    owner__sites=Site.objects.get_current())
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(
                    sites=Site.objects.get_current())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AdvancedNotesAdmin(admin.ModelAdmin):
    list_display = ('video', 'user', 'timestamp',
                    'status', 'added_on', 'modified_on')

    class Media:
        css = {
            "all": (
                'css/pod.css',
            )
        }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(
                request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "user":
            kwargs["queryset"] = User.objects.filter(
                    owner__sites=Site.objects.get_current())
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(
                    sites=Site.objects.get_current())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class NoteCommentsAdmin(admin.ModelAdmin):
    list_display = ('parentNote', 'user', 'added_on', 'modified_on')

    class Media:
        css = {
            "all": (
                'css/pod.css',
            )
        }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(parentNote__video__sites=get_current_site(
                request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "user":
            kwargs["queryset"] = User.objects.filter(
                    owner__sites=Site.objects.get_current())
        if (db_field.name) == "parentNote":
            kwargs["queryset"] = AdvancedNotes.objects.filter(
                    video__owner__owner__sites=Site.objects.get_current())
        if (db_field.name) == "parentCom":
            kwargs["queryset"] = NoteComments. \
                objects.filter(
                parentNote__video__owner__owner__sites=Site.
                    objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class VideoToDeleteAdmin(admin.ModelAdmin):
    list_display = ('date_deletion', 'get_videos')
    list_filter = ['date_deletion']

    def get_videos(self, obj):
        return obj.video.count()
    get_videos.short_description = 'video'


class ViewCountAdmin(admin.ModelAdmin):
    list_display = ('video', 'date', 'count')
    readonly_fields = ('video', 'date', 'count')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(
                request))
        return qs


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
admin.site.register(Notes, NotesAdmin)
admin.site.register(AdvancedNotes, AdvancedNotesAdmin)
admin.site.register(NoteComments, NoteCommentsAdmin)
admin.site.register(VideoToDelete, VideoToDeleteAdmin)
admin.site.register(ViewCount, ViewCountAdmin)
