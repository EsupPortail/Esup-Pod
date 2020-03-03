from django.conf import settings
from django.contrib import admin
from pod.completion.models import Contributor
from pod.completion.models import Document
from pod.completion.models import Overlay
from pod.completion.models import Track
from pod.completion.forms import DocumentAdminForm
from pod.completion.forms import TrackAdminForm
FILEPICKER = False
if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True


class ContributorInline(admin.TabularInline):
    model = Contributor
    readonly_fields = ('video', 'name', 'email_address', 'role', 'weblink',)
    extra = 0

    def has_add_permission(self, request):
        return False


class ContributorAdmin(admin.ModelAdmin):

    list_display = ('name', 'role', 'video',)
    list_display_links = ('name',)
    list_filter = ('role',)
    search_fields = ['id', 'name', 'role', 'video__title']

    class Media:
        css = {
            "all": (
                'css/pod.css',
            )
        }


admin.site.register(Contributor, ContributorAdmin)


class DocumentInline(admin.TabularInline):
    model = Document
    readonly_fields = ('video', 'document',)
    extra = 0

    def has_add_permission(self, request):
        return False


class DocumentAdmin(admin.ModelAdmin):

    if FILEPICKER:
        form = DocumentAdminForm
    list_display = ('document', 'video',)
    list_display_links = ('document',)
    search_fields = ['id', 'document__name', 'video__title']

    class Media:
        css = {
            "all": (
                'bootstrap-4/css/bootstrap.min.css',
                'bootstrap-4/css/bootstrap-grid.css',
                'css/pod.css'
            )
        }
        js = (
            'podfile/js/filewidget.js',
            'js/main.js',
            'feather-icons/feather.min.js',
            'bootstrap-4/js/bootstrap.min.js')


admin.site.register(Document, DocumentAdmin)


class TrackInline(admin.TabularInline):
    model = Track
    readonly_fields = ('video', 'kind', 'lang', 'src',)
    extra = 0

    def has_add_permission(self, request):
        return False


class TrackAdmin(admin.ModelAdmin):

    if FILEPICKER:
        form = TrackAdminForm
    list_display = ('src', 'kind', 'video',)
    list_display_links = ('src',)
    list_filter = ('kind',)
    search_fields = ['id', 'src__name', 'kind', 'video__title']

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


admin.site.register(Track, TrackAdmin)


class OverlayInline(admin.TabularInline):
    model = Overlay
    readonly_fields = ('video', 'title', 'time_start',
                       'time_end', 'content', 'position', 'background',)
    exclude = ('slug',)
    extra = 0

    def has_add_permission(self, request):
        return False


class OverlayAdmin(admin.ModelAdmin):

    list_display = ('title', 'video',)
    list_display_links = ('title',)
    search_fields = ['id', 'title', 'video__title']

    class Media:
        css = {
            "all": (
                'css/pod.css',
            )
        }


admin.site.register(Overlay, OverlayAdmin)
