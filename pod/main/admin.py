"""Esup-Pod main admin page."""

from tinymce.widgets import TinyMCE
from django.contrib import admin
from django import forms
from django.contrib.flatpages.admin import FlatpageForm
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from modeltranslation.admin import TranslationAdmin
from pod.main.models import LinkFooter, Configuration
from pod.main.models import AdditionalChannelTab
from pod.main.models import Block


SITE_ID = getattr(settings, "SITE_ID", 1)
content_widget = {}
for key, value in settings.LANGUAGES:
    content_widget["content_%s" % key.replace("-", "_")] = TinyMCE()


class PageForm(FlatpageForm):
    class Meta:
        model = FlatPage
        fields = "__all__"
        widgets = content_widget


@admin.register(AdditionalChannelTab)
class AdditionalChannelTabAdmin(TranslationAdmin):
    """Create translation for additional Channel Tab Field."""

    list_display = ("name",)


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "description")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class CustomFlatPageAdmin(TranslationAdmin):
    list_display = ("title", "url")
    form = PageForm
    fieldsets = (
        (None, {"fields": ("url", "title", "content")}),
        (
            _("Advanced options"),
            {
                "classes": ("collapse",),
                "fields": (
                    "enable_comments",
                    "registration_required",
                    "template_name",
                    "sites",
                ),
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ("sites",)
        else:
            return ()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(request))
        return qs

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.sites.add(Site.objects.get(id=SITE_ID))
        obj.save()


@admin.register(LinkFooter)
class LinkFooterAdmin(TranslationAdmin):
    list_display = (
        "title",
        "url",
    )

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ("sites",)
            self.exclude = exclude
        form = super(LinkFooterAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Exclude sites fields in admin for non-superuser."""
        if (db_field.name) == "page":
            kwargs["queryset"] = FlatPage.objects.filter(sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class BlockAdminForm(forms.ModelForm):
    """The form for Block administration in the Django admin panel."""

    class Meta:
        """Metadata class defining the associated model and fields."""

        model = Block
        fields = "__all__"


@admin.register(Block)
class BlockAdmin(TranslationAdmin):
    """The admin configuration for the Block model in the Django admin panel."""

    list_display = (
        "title",
        "page",
        "type",
        "data_type",
    )

    def get_form(self, request, obj=None, **kwargs):
        """
        Get the form to be used in the Django admin.

        Args:
            request: The Django request object.
            obj: The Block object being edited, or None if creating a new one.
            **kwargs: Additional keyword arguments.

        Returns:
            Type[forms.ModelForm]: The form class to be used in the admin.
        """
        form = super().get_form(request, obj, **kwargs)

        return form


# Unregister the default FlatPage admin and register CustomFlatPageAdmin.
admin.site.unregister(FlatPage)
admin.site.register(FlatPage, CustomFlatPageAdmin)
