from django.conf import settings
from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from js_asset import static
from sorl.thumbnail import get_thumbnail

from pod.live.forms import BuildingAdminForm, EventAdminForm, BroadcasterAdminForm
from pod.live.models import (
    Building,
    Event,
    Broadcaster,
    HeartBeat,
    LiveTranscriptRunningTask,
    Video,
)

DEFAULT_EVENT_THUMBNAIL = getattr(
    settings, "DEFAULT_EVENT_THUMBNAIL", "img/default-event.svg"
)

# Register your models here.
USE_PODFILE = getattr(settings, "USE_PODFILE", False)


class HeartBeatAdmin(admin.ModelAdmin):
    list_display = ("viewkey", "user", "event", "last_heartbeat")


class BuildingAdmin(admin.ModelAdmin):
    form = BuildingAdminForm
    list_display = ("name", "gmapurl")
    search_fields = ["name"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(request))
        return qs

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ("sites",)
            self.exclude = exclude
        form = super(BuildingAdmin, self).get_form(request, obj, **kwargs)
        return form

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
            "js/main.js",
            "podfile/js/filewidget.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )


class BroadcasterAdmin(admin.ModelAdmin):
    form = BroadcasterAdminForm
    list_display = (
        "name",
        "slug",
        "building",
        "url",
        "status",
        "is_recording_admin",
        "is_restricted",
        "piloting_conf",
        "main_lang",
    )
    list_filter = ["building"]

    def get_fields(self, request, obj=None):
        fields = (
            "name",
            "building",
            "description",
            "poster",
            "url",
            "status",
            "enable_add_event",
            "enable_viewer_count",
            "is_restricted",
            "public",
            "manage_groups",
            "piloting_implementation",
            "piloting_conf",
            "slug",
            "main_lang",
            "transcription_file",
        )
        if obj is None:
            return fields
        fields += ("qrcode",)
        return fields

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ["slug", "transcription_file"]
        return ["slug", "qrcode", "transcription_file"]

    def get_autocomplete_fields(self, request):
        return ["building"]

    def get_form(self, request, obj=None, **kwargs):
        form = super(BroadcasterAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields["piloting_conf"].widget.attrs.update(
            {"data-url": reverse("live:ajax_get_mandatory_parameters") + "?impl_name="}
        )
        kwargs["help_texts"] = {"qrcode": _("QR code to record immediately an event")}
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(building__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "building":
            kwargs["queryset"] = Building.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def qrcode(self, obj):
        return obj.qrcode

    qrcode.short_description = _("QR Code")
    qrcode.allow_tags = True

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
            "js/admin_broadcaster.js",
            "podfile/js/filewidget.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )


class PasswordFilter(admin.SimpleListFilter):
    title = _("password")
    parameter_name = "password"

    def lookups(self, request, model_admin):
        return (
            ("Yes", _("Yes")),
            ("No", _("No")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "No":
            queryset = queryset.exclude(
                pk__in=[event.id for event in queryset if event.password]
            )
        elif value == "Yes":
            queryset = queryset.exclude(
                pk__in=[event.id for event in queryset if not event.password]
            )
        return queryset


class EventAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        ModelForm = super(EventAdmin, self).get_form(request, obj, **kwargs)

        class ModelFormMetaClass(ModelForm):
            def __new__(cls, *args, **kwargs):
                kwargs["request"] = request
                return ModelForm(*args, **kwargs)

        return ModelFormMetaClass

    def get_broadcaster_admin(self, instance):
        return instance.broadcaster.name

    get_broadcaster_admin.short_description = _("Broadcaster")

    def is_auto_start_admin(self, instance):
        return instance.is_auto_start

    is_auto_start_admin.short_description = _("Auto start admin")
    is_auto_start_admin.boolean = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "video_on_hold":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_thumbnail_admin(self, instance):
        if instance.thumbnail and instance.thumbnail.file_exist():
            im = get_thumbnail(
                instance.thumbnail.file, "100x100", crop="center", quality=72
            )
            thumbnail_url = im.url
        else:
            thumbnail_url = static(DEFAULT_EVENT_THUMBNAIL)
        return format_html(
            '<img style="max-width:100px" '
            'src="%s" alt="%s" loading="lazy">'
            % (
                thumbnail_url,
                instance.title.replace("{", "").replace("}", "").replace('"', "'"),
            )
        )

    get_thumbnail_admin.short_description = _("Thumbnails")
    get_thumbnail_admin.list_filter = True

    form = EventAdminForm
    list_display = [
        "title",
        "owner",
        "start_date",
        "end_date",
        "get_broadcaster_admin",
        "is_draft",
        "is_restricted",
        "password",
        "is_auto_start_admin",
        "is_recording_stopped",
        "get_thumbnail_admin",
        "enable_transcription",
    ]
    fields = [
        "title",
        "description",
        "owner",
        "additional_owners",
        "start_date",
        "end_date",
        "type",
        "broadcaster",
        "iframe_url",
        "iframe_height",
        "aside_iframe_url",
        "is_draft",
        "password",
        "is_restricted",
        "restrict_access_to_groups",
        "is_auto_start",
        "video_on_hold",
        "enable_transcription",
    ]
    search_fields = [
        "title",
        "broadcaster__name",
    ]

    list_filter = [
        "start_date",
        "is_draft",
        "is_restricted",
        "is_auto_start",
        PasswordFilter,
        ("broadcaster__building", admin.RelatedOnlyFieldListFilter),
    ]
    autocomplete_fields = ["video_on_hold"]

    get_broadcaster_admin.admin_order_field = "broadcaster"
    is_auto_start_admin.admin_order_field = "is_auto_start"

    if USE_PODFILE:
        fields.append("thumbnail")

    class Media:
        css = {
            "all": (
                # "css/pod.css",
                # "bootstrap/dist/css/bootstrap-grid.min.css",
                # "bootstrap/dist/css/bootstrap.min.css",
            )
        }
        js = (
            "podfile/js/filewidget.js",
            "js/main.js",
            "js/validate-date_delete-field.js",
            "bootstrap/dist/js/bootstrap.min.js",
        )


admin.site.register(Building, BuildingAdmin)
admin.site.register(Broadcaster, BroadcasterAdmin)
admin.site.register(HeartBeat, HeartBeatAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(LiveTranscriptRunningTask)
