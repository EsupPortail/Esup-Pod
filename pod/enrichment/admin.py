from django.apps import apps
from django.contrib import admin
from pod.enrichment.models import Enrichment
from pod.enrichment.forms import EnrichmentAdminForm
FILEPICKER = False
if apps.is_installed('pod.filepicker'):
    FILEPICKER = True


class EnrichmentInline(admin.TabularInline):
    model = Enrichment
    extra = 0

    def has_add_permission(self, request):
        return False


class EnrichmentAdmin(admin.ModelAdmin):

    form = EnrichmentAdminForm
    list_display = ('title', 'type', 'video',)

    class Media:
        js = ('js/jquery-3.3.1.min.js', 'js/jquery.overlay.js',)


if FILEPICKER:
    admin.site.register(Enrichment, EnrichmentAdmin)
else:
    admin.site.register(Enrichment)
