from django.conf import settings
from django.contrib import admin
from .models import Enrichment, EnrichmentGroup, EnrichmentVtt
from .forms import EnrichmentAdminForm, EnrichmentVttAdminForm
FILEPICKER = False
if getattr(settings, 'USE_PODFILE', False):
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


if FILEPICKER:
    admin.site.register(Enrichment, EnrichmentAdmin)
else:
    admin.site.register(Enrichment)


class EnrichmentGroupAdmin(admin.ModelAdmin):
    list_display = ('video', 'get_groups')
    # readonly_fields = ('video', )

    def get_groups(self, obj):
        return "\n".join([g.name for g in obj.groups.all()])


class EnrichmentVttAdmin(admin.ModelAdmin):

    form = EnrichmentVttAdminForm
    list_display = ('video', 'src', 'get_file_name')
    readonly_fields = ('video', )

    def get_file_name(self, obj):
        return obj.src.file.name

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


admin.site.register(EnrichmentGroup, EnrichmentGroupAdmin)
admin.site.register(EnrichmentVtt, EnrichmentVttAdmin)
