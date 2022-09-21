from django.conf import settings
from django.contrib import admin
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.forms import Textarea
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from js_asset import static
from sorl.thumbnail import get_thumbnail

from pod.live.forms import BuildingAdminForm, EventAdminForm, BroadcasterAdminForm
from pod.live.models import Building, Event, Broadcaster, HeartBeat, Video

DEFAULT_EVENT_THUMBNAIL = getattr(
    settings, "DEFAULT_EVENT_THUMBNAIL", "img/default-event.svg"
)

# Register your models here.

FILEPICKER = False
if getattr(settings, "USE_PODFILE", False):
    FILEPICKER = True


class HeartBeatAdmin(admin.ModelAdmin):
    list_display = ("viewkey", "user", "broadcaster", "last_heartbeat")


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
    )
    readonly_fields = ["slug"]
    autocomplete_fields = ["building", "video_on_hold"]
    list_filter = ["building"]

    def get_form(self, request, obj=None, **kwargs):
        kwargs["widgets"] = {
            "piloting_conf": Textarea(
                attrs={
                    "placeholder": "{\n 'server_url':'...',\n \
                        'application':'...',\n 'livestream':'...',\n}"
                }
            )
        }
        return super().get_form(request, obj, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(building__sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "building":
            kwargs["queryset"] = Building.objects.filter(sites=Site.objects.get_current())
        if (db_field.name) == "video_on_hold":
            kwargs["queryset"] = Video.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
            'src="%s" alt="%s" loading="lazy"/>'
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
        "get_thumbnail_admin",
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

    get_broadcaster_admin.admin_order_field = "broadcaster"
    is_auto_start_admin.admin_order_field = "is_auto_start"

    if FILEPICKER:
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
