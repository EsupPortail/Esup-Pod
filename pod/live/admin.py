"""Esup-Pod Live administration."""

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.views.autocomplete import AutocompleteJsonView
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail import get_thumbnail
from django.templatetags.static import static

from pod.live.cache_config import (
    INCOMPATIBLE_LIVE_CACHE_WARNING,
    has_incompatible_live_cache,
)
from pod.live.forms import (
    BuildingAdminForm,
    EventAdminForm,
    BroadcasterAdminForm,
    RunnerManagerAutocompleteSelect,
    runner_manager_label,
)
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


@admin.register(HeartBeat)
class HeartBeatAdmin(admin.ModelAdmin):
    list_display = ("viewkey", "user", "event", "last_heartbeat")


@admin.register(Building)
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


class RunnerManagerAutocompleteJsonView(AutocompleteJsonView):
    """Include inactivity in manager search results for broadcaster forms only."""

    def serialize_result(self, obj, to_field_name):
        """Keep standard autocomplete IDs and permissions with contextual labels."""
        result = super().serialize_result(obj, to_field_name)
        if self.source_field.model is Broadcaster and self.source_field.name in (
            "runner_manager",
            "secondary_runner_manager",
        ):
            result["text"] = runner_manager_label(obj)
        return result


@admin.register(Broadcaster)
class BroadcasterAdmin(admin.ModelAdmin):
    """Configure broadcasters."""

    form = BroadcasterAdminForm
    list_display = (
        "name",
        "slug",
        "building",
        "stream_mode",
        "runner_manager",
        "secondary_runner_manager",
        "source_id",
        "url",
        "status",
        "is_recording_admin",
        "is_restricted",
        "piloting_conf",
        "main_lang",
    )
    list_filter = [
        "building",
        "stream_mode",
        "runner_manager",
        "secondary_runner_manager",
    ]

    def get_fields(self, request, obj=None):
        """Expose broadcaster settings and add its QR code when editing an existing entry."""
        fields = (
            "name",
            "building",
            "description",
            "poster",
            "stream_mode",
            "runner_manager",
            "secondary_runner_manager",
            "source_id",
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
        """Protect generated broadcaster fields and the QR code from direct edits."""
        if obj is None:
            return ["slug", "transcription_file"]
        return ["slug", "qrcode", "transcription_file"]

    def get_autocomplete_fields(self, request):
        """Enable building and Live manager searches in the administration form."""
        return ["building", "runner_manager", "secondary_runner_manager"]

    def get_urls(self):
        """Register the manager autocomplete used only by broadcaster forms."""
        return [
            path(
                "runner-manager-autocomplete/",
                self.admin_site.admin_view(
                    RunnerManagerAutocompleteJsonView.as_view(admin_site=self.admin_site)
                ),
                name="live_broadcaster_runner_manager_autocomplete",
            ),
        ] + super().get_urls()

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        """Warn about incompatible caches and existing inactive Live managers."""
        if has_incompatible_live_cache():
            self.message_user(
                request, INCOMPATIBLE_LIVE_CACHE_WARNING, level=messages.WARNING
            )
        if obj is not None and obj.is_runner_live:
            for field in ("runner_manager", "secondary_runner_manager"):
                manager = getattr(obj, field)
                if manager is not None and not manager.is_active:
                    self.message_user(
                        request,
                        _(
                            '%(field)s: the assigned manager "%(manager)s" '
                            "is marked as inactive."
                        )
                        % {
                            "field": obj._meta.get_field(field).verbose_name,
                            "manager": manager.name,
                        },
                        level=messages.WARNING,
                    )
        return super().render_change_form(request, context, add, change, form_url, obj)

    def get_form(self, request, obj=None, **kwargs):
        """Configure both manager widgets and the piloting parameter lookup URL."""
        form = super(BroadcasterAdmin, self).get_form(request, obj, **kwargs)
        for field in ("runner_manager", "secondary_runner_manager"):
            form.base_fields[field].widget.can_delete_related = False
        form.base_fields["piloting_conf"].widget.attrs.update(
            {"data-url": reverse("live:ajax_get_mandatory_parameters") + "?impl_name="}
        )
        kwargs["help_texts"] = {"qrcode": _("QR code to record immediately an event")}
        return form

    def get_queryset(self, request):
        """Limit non-superusers to broadcasters belonging to the current site."""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(building__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restrict building and manager choices to the administrator's allowed site."""
        if db_field.name == "building":
            kwargs["queryset"] = Building.objects.filter(sites=Site.objects.get_current())
        if db_field.name in ("runner_manager", "secondary_runner_manager"):
            kwargs["widget"] = RunnerManagerAutocompleteSelect(
                db_field, self.admin_site, using=kwargs.get("using")
            )
        if (
            db_field.name in ("runner_manager", "secondary_runner_manager")
            and not request.user.is_superuser
        ):
            from pod.video_encode_transcript.models import RunnerManager

            kwargs["queryset"] = RunnerManager.objects.filter(
                site=get_current_site(request)
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description=_("QR code"))
    def qrcode(self, obj):
        """Display the broadcaster's generated QR code in its administration form."""
        return obj.qrcode

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


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        ModelForm = super(EventAdmin, self).get_form(request, obj, **kwargs)

        class ModelFormMetaClass(ModelForm):
            def __new__(cls, *args, **kwargs):
                kwargs["request"] = request
                return ModelForm(*args, **kwargs)

        return ModelFormMetaClass

    @admin.display(
        description=_("Broadcaster"),
        ordering="broadcaster",
    )
    def get_broadcaster_admin(self, instance):
        return instance.broadcaster.name

    @admin.display(
        description=_("Auto start admin"),
        boolean=True,
        ordering="is_auto_start",
    )
    def is_auto_start_admin(self, instance):
        return instance.is_auto_start

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "video_on_hold":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description=_("Thumbnails"))
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


admin.site.register(LiveTranscriptRunningTask)
