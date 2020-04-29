from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from django.contrib.flatpages.admin import FlatpageForm
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from modeltranslation.admin import TranslationAdmin
from pod.main.models import LinkFooter


SITE_ID = getattr(settings, 'SITE_ID', 1)
content_widget = {}
for key, value in settings.LANGUAGES:
    content_widget['content_%s' % key.replace(
        '-', '_')] = CKEditorWidget(config_name='complete')


class PageForm(FlatpageForm):

    class Meta:
        model = FlatPage
        fields = '__all__'
        widgets = content_widget

# CustomFlatPage admin panel


class CustomFlatPageAdmin(TranslationAdmin):
    list_display = ('title', 'url')
    form = PageForm
    fieldsets = (
        (None, {'fields': ('url', 'title', 'content')}),
        (_('Advanced options'), {
            'classes': ('collapse', ),
            'fields': (
                'enable_comments',
                'registration_required',
                'template_name',
                'sites'
            ),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ('sites',)
        else:
            return ()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(
                request))
        return qs

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.sites.add(Site.objects.get(id=SITE_ID))
        obj.save()


class LinkFooterAdmin(TranslationAdmin):
    list_display = ('title', 'url', )

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            exclude = ()
            exclude += ('sites',)
            self.exclude = exclude
        form = super(LinkFooterAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(sites=get_current_site(
                request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "page":
            kwargs["queryset"] = FlatPage.objects.filter(
                    sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Unregister the default FlatPage admin and register CustomFlatPageAdmin.
admin.site.unregister(FlatPage)
admin.site.register(FlatPage, CustomFlatPageAdmin)
admin.site.register(LinkFooter, LinkFooterAdmin)
