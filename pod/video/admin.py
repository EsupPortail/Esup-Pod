"""Admin pages for Esup-Pod Video items."""
from django.conf import settings
from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.html import format_html
from django.utils.html import mark_safe
from django.utils.translation import ugettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from .models import Video
from .models import UpdateOwner
from .models import Channel
from .models import Theme
from .models import Type
from .models import Discipline
from .models import Notes, AdvancedNotes, NoteComments
from .models import ViewCount
from .models import VideoToDelete
from .models import VideoVersion
from .models import Category


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

# Ordering user by username !
User._meta.ordering = ["username"]
# SET USE_ESTABLISHMENT_FIELD
USE_ESTABLISHMENT_FIELD = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)

USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)

if USE_TRANSCRIPTION:
    from ..video_encode_transcript import transcript

    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")

USE_OBSOLESCENCE = getattr(settings, "USE_OBSOLESCENCE", False)

CELERY_TO_ENCODE = getattr(settings, "CELERY_TO_ENCODE", False)

ACTIVE_VIDEO_COMMENT = getattr(settings, "ACTIVE_VIDEO_COMMENT", False)


def url_to_edit_object(obj):
    url = reverse(
        "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.model_name),
        args=[obj.id],
    )
    title = format_html('<a href="{}">{}</a>', url, obj.username)
    return mark_safe(title)


class EncodedFilter(admin.SimpleListFilter):
    title = _("Encoded?")
    parameter_name = "encoded"

    def lookups(self, request, model_admin):
        return (
            ("Yes", _("Yes")),
            ("No", _("No")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            queryset = queryset.exclude(
                pk__in=[vid.id for vid in queryset if not vid.encoded]
            )
        elif value == "No":
            queryset = queryset.exclude(
                pk__in=[vid.id for vid in queryset if vid.encoded]
            )
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
    list_display = (
        "id",
        "title",
        "get_owner_by_name",
        "type",
        "date_added",
        "viewcount",
        "is_draft",
        "is_restricted",
        "password",
        "duration_in_time",
        "encoding_in_progress",
        "get_encoding_step",
        "get_thumbnail_admin",
    )
    list_display_links = ("id", "title")
    list_filter = (
        "date_added",
        ("channel", admin.RelatedOnlyFieldListFilter),
        ("type", admin.RelatedOnlyFieldListFilter),
        "is_draft",
        "encoding_in_progress",
        EncodedFilter,
        # "owner",
    )
    autocomplete_fields = [
        "owner",
        "additional_owners",
        "discipline",
        "channel",
        "theme",
        "restrict_access_to_groups",
    ]
    # Ajout de l'attribut 'date_delete'
    if USE_OBSOLESCENCE:
        list_filter = list_filter + ("date_delete",)
        list_display = list_display + ("date_delete",)

    list_editable = ("is_draft", "is_restricted")
    search_fields = [
        "id",
        "title",
        "video",
        "owner__username",
        "owner__first_name",
        "owner__last_name",
    ]
    list_per_page = 20
    filter_horizontal = (
        "discipline",
        "channel",
        "theme",
    )
    readonly_fields = ("duration", "encoding_in_progress", "get_encoding_step")

    inlines = []

    inlines += [
        VideoVersionInline,
        ContributorInline,
        DocumentInline,
        TrackInline,
        OverlayInline,
    ]

    inlines += [ChapterInline]

    def get_owner_establishment(self, obj):
        owner = obj.owner
        return owner.owner.establishment

    get_owner_establishment.short_description = _("Establishment")

    # Ajout de l'attribut 'establishment'
    if USE_ESTABLISHMENT_FIELD:
        list_filter = list_filter + ("owner__owner__establishment",)
        list_display = list_display + ("get_owner_establishment",)
        search_fields.append(
            "owner__owner__establishment",
        )

    def get_owner_by_name(self, obj):
        owner = obj.owner
        url = url_to_edit_object(owner)
        title = "%s %s (%s)" % (owner.first_name, owner.last_name, url)
        return mark_safe(title)

    get_owner_by_name.allow_tags = True
    get_owner_by_name.short_description = _("Owner")

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            kwargs["form"] = VideoSuperAdminForm
        else:
            kwargs["form"] = VideoAdminForm

        exclude = ()
        if not getattr(settings, "ACTIVE_VIDEO_COMMENT", False):
            exclude += ("disable_comment",)

        if obj and (obj.encoding_in_progress or not obj.encoded):
            exclude += (
                "video",
                "owner",
            )
        if not USE_TRANSCRIPTION:
            exclude += ("transcript",)
        if request.user.is_staff is False or obj is None or USE_OBSOLESCENCE is False:
            exclude += ("date_delete",)
        if not request.user.is_superuser:
            exclude += ("sites",)
        self.exclude = exclude
        form = super(VideoAdmin, self).get_form(request, obj, **kwargs)
        return form

    if USE_TRANSCRIPTION:
        actions = ["encode_video", "transcript_video", "draft_video"]
    else:
        actions = ["encode_video", "draft_video"]

    def draft_video(self, request, queryset):
        for item in queryset:
            item.is_draft = True
            item.save()

    draft_video.short_description = _("Set as draft")

    def encode_video(self, request, queryset):
        for item in queryset:
            item.launch_encode = True
            item.save()

    encode_video.short_description = _("Encode selected")

    def transcript_video(self, request, queryset):
        for item in queryset:
            if item.get_video_mp3() and not item.encoding_in_progress:
                transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
                transcript_video(item.id)

    transcript_video.short_description = _("Transcript selected")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(request))
        return qs

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["max_duration_date_delete"] = getattr(
            settings, "MAX_DURATION_DATE_DELETE", 10
        )
        return super(VideoAdmin, self).change_view(
            request, object_id, form_url, extra_context
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.sites.add(get_current_site(request))
            obj.save()

    class Media:
        css = {
            "all": (
                # "bootstrap/dist/css/bootstrap.min.css",
                # "bootstrap/dist/css/bootstrap-grid.min.css",
                # "css/pod.css",
            )
        }
        js = (
            "podfile/js/filewidget.js",
            "js/main.js",
            "js/validate-date_delete-field.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )


class updateOwnerAdmin(admin.ModelAdmin):
    """Handle an admin page to change owner of several videos."""

    change_list_template = "videos/change_video_owner.html"

    def changelist_view(self, request, extra_context=None):
        """View for the change_video_owner admin page."""
        extra_context = extra_context or {}
        return super(updateOwnerAdmin, self).changelist_view(
            request, extra_context=extra_context
        )

    def has_add_permission(self, request, obj=None):
        """Manage create new instance link from admin interface.

        if return False, no add link

        Args:
            request (Request): Http request
            obj (dict, optional): Defaults to None.

        Returns:
            bool: add or remove add link
        """
        return False


class ChannelSuperAdminForm(ChannelForm):
    is_staff = True
    is_superuser = True
    admin_form = True

    class Meta(object):
        model = Channel
        fields = "__all__"
        widgets = {
            "owners": widgets.AutocompleteSelectMultiple(
                Channel._meta.get_field("owners"),
                admin.site,
                attrs={"style": "width: 20em"},
            ),
            "users": widgets.AutocompleteSelectMultiple(
                Channel._meta.get_field("users"),
                admin.site,
                attrs={"style": "width: 20em"},
            ),
            "allow_to_groups": widgets.AutocompleteSelectMultiple(
                Channel._meta.get_field("allow_to_groups"),
                admin.site,
                attrs={"style": "width: 20em"},
            ),
        }


class ChannelAdminForm(ChannelForm):
    is_staff = True
    is_superuser = False
    admin_form = True

    class Meta(object):
        model = Channel
        fields = "__all__"
        widgets = {
            "owners": widgets.AutocompleteSelectMultiple(
                Channel._meta.get_field("owners"),
                admin.site,
                attrs={"style": "width: 20em"},
            ),
            "users": widgets.AutocompleteSelectMultiple(
                Channel._meta.get_field("users"),
                admin.site,
                attrs={"style": "width: 20em"},
            ),
            "allow_to_groups": widgets.AutocompleteSelectMultiple(
                Channel._meta.get_field("allow_to_groups"),
                admin.site,
                attrs={"style": "width: 20em"},
            ),
        }


class ChannelAdmin(admin.ModelAdmin):
    search_fields = ["title"]

    def get_owners(self, obj):
        owners = []
        for owner in obj.owners.all():
            url = url_to_edit_object(owner)
            title = "%s %s (%s)" % (owner.first_name, owner.last_name, url)
            owners.append(mark_safe(title))
        titles = ", ".join(owners)
        return mark_safe(titles)

    get_owners.allow_tags = True
    get_owners.short_description = _("Owners")

    list_display = (
        "title",
        "get_owners",
        "visible",
    )
    filter_horizontal = (
        "owners",
        "users",
    )
    list_editable = ("visible",)
    ordering = ("title",)
    list_filter = ["visible"]

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ("site",)
        else:
            return ()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.site = get_current_site(request)
            obj.save()

    def get_form(self, request, obj=None, **kwargs):
        if request.user.is_superuser:
            kwargs["form"] = ChannelSuperAdminForm
        else:
            kwargs["form"] = ChannelAdminForm

        form = super(ChannelAdmin, self).get_form(request, obj, **kwargs)
        return form

    class Media:
        css = {
            "all": (
                # "bootstrap/dist/css/bootstrap.min.css",
                # "bootstrap/dist/css/bootstrap-grid.min.css",
                # "css/pod.css",
            )
        }
        js = (
            "js/main.js",
            "podfile/js/filewidget.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(site=get_current_site(request))
        return qs


class ThemeAdmin(admin.ModelAdmin):
    form = ThemeForm
    list_display = ("title", "channel")
    list_filter = (("channel", admin.RelatedOnlyFieldListFilter),)
    ordering = ("channel", "title")
    search_fields = ["title"]
    autocomplete_fields = ["parentId", "channel"]

    class Media:
        css = {
            "all": (
                # "bootstrap/dist/css/bootstrap.min.css",
                # "bootstrap/dist/css/bootstrap-grid.min.css",
                # "css/pod.css",
            )
        }
        js = (
            "js/main.js",
            "podfile/js/filewidget.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(channel__site=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "parentId":
            kwargs["queryset"] = Theme.objects.filter(
                channel__site=Site.objects.get_current()
            )
        if (db_field.name) == "channel":
            kwargs["queryset"] = Channel.objects.filter(site=Site.objects.get_current())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TypeAdmin(TranslationAdmin):
    form = TypeForm
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ["title"]

    class Media:
        css = {
            "all": (
                # "bootstrap/dist/css/bootstrap.min.css",
                # "bootstrap/dist/css/bootstrap-grid.min.css",
                # "css/pod.css",
            )
        }
        js = (
            "js/main.js",
            "podfile/js/filewidget.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ("sites",)
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
            qs = qs.filter(sites=get_current_site(request))
        return qs


class DisciplineAdmin(TranslationAdmin):
    form = DisciplineForm
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ["title"]

    class Media:
        css = {
            "all": (
                # "bootstrap/dist/css/bootstrap-grid.min.css",
                # "bootstrap/dist/css/bootstrap.min.css",
                # "css/pod.css",
            )
        }
        js = (
            "js/main.js",
            "podfile/js/filewidget.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ("site",)
            self.exclude = exclude
        form = super(DisciplineAdmin, self).get_form(request, obj, **kwargs)
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            obj.site = get_current_site(request)
            obj.save()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(site=get_current_site(request))
        return qs


class NotesAdmin(admin.ModelAdmin):
    list_display = ("video", "user")
    autocomplete_fields = ["video", "user"]

    # class Media:
    #     css = {"all": ("css/pod.css",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "user":
            kwargs["queryset"] = User.objects.filter(
                owner__sites=Site.objects.get_current()
            )
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AdvancedNotesAdmin(admin.ModelAdmin):
    list_display = ("video", "user", "timestamp", "status", "added_on", "modified_on")
    search_fields = ["note"]
    autocomplete_fields = ["user", "video"]

    # class Media:
    #     css = {"all": ("css/pod.css",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "user":
            kwargs["queryset"] = User.objects.filter(
                owner__sites=Site.objects.get_current()
            )
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class NoteCommentsAdmin(admin.ModelAdmin):
    autocomplete_fields = ["user", "parentNote", "parentCom"]
    search_fields = ["comment"]
    list_display = ("parentNote", "user", "added_on", "modified_on")

    # class Media:
    #     css = {"all": ("css/pod.css",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(parentNote__video__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "user":
            kwargs["queryset"] = User.objects.filter(
                owner__sites=Site.objects.get_current()
            )
        if (db_field.name) == "parentNote":
            kwargs["queryset"] = AdvancedNotes.objects.filter(
                video__owner__owner__sites=Site.objects.get_current()
            )
        if (db_field.name) == "parentCom":
            kwargs["queryset"] = NoteComments.objects.filter(
                parentNote__video__owner__owner__sites=Site.objects.get_current()
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class VideoToDeleteAdmin(admin.ModelAdmin):
    list_display = ("date_deletion", "get_videos")
    list_filter = ["date_deletion"]
    autocomplete_fields = ["video"]

    def get_videos(self, obj):
        return obj.video.count()

    get_videos.short_description = "video"


class ViewCountAdmin(admin.ModelAdmin):
    list_display = ("video", "date", "count")
    readonly_fields = ("video", "date", "count")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(request))
        return qs


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "videos_count")
    readonly_fields = ("slug",)
    # list_filter = ["owner"]

    def videos_count(self, obj):
        return len(obj.video.all())

    videos_count.short_description = "Videos"


admin.site.register(Channel, ChannelAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(Discipline, DisciplineAdmin)
admin.site.register(Theme, ThemeAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(UpdateOwner, updateOwnerAdmin)
admin.site.register(Notes, NotesAdmin)
admin.site.register(AdvancedNotes, AdvancedNotesAdmin)
admin.site.register(NoteComments, NoteCommentsAdmin)
admin.site.register(VideoToDelete, VideoToDeleteAdmin)
admin.site.register(ViewCount, ViewCountAdmin)
admin.site.register(Category, CategoryAdmin)
