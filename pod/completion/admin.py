from django.contrib import admin
from pod.completion.models import Contributor
from pod.completion.models import Document
from pod.completion.models import Overlay
from pod.completion.models import Track
from pod.completion.forms import DocumentForm
from pod.completion.forms import TrackForm
try:
    __import__('pod.filepicker')
    FILEPICKER = True
except ImportError:
    FILEPICKER = False
    pass


class ContributorInline(admin.TabularInline):
    model = Contributor
    readonly_fields = ('video', 'name', 'email_address', 'role', 'weblink',)
    extra = 0

    def has_add_permission(self, request):
        return False


class DocumentInline(admin.TabularInline):
    model = Document
    readonly_fields = ('video', 'document',)
    extra = 0

    def has_add_permission(self, request):
        return False


class DocumentAdmin(admin.ModelAdmin):

    form = DocumentForm

    class Media:
        js = ('js/jquery.tools.min.js',)


class TrackInline(admin.TabularInline):
    model = Track
    readonly_fields = ('video', 'kind', 'lang', 'src',)
    extra = 0

    def has_add_permission(self, request):
        return False


class TrackAdmin(admin.ModelAdmin):

    form = TrackForm

    class Media:
        js = ('js/jquery.tools.min.js',)


class OverlayInline(admin.TabularInline):
    model = Overlay
    readonly_fields = ('video', 'title', 'time_start',
                       'time_end', 'content', 'position', 'background',)
    exclude = ('slug',)
    extra = 0

    def has_add_permission(self, request):
        return False


admin.site.register(Contributor)
if FILEPICKER:
    admin.site.register(Document, DocumentAdmin)
    admin.site.register(Track, TrackAdmin)
else:
    admin.site.register(Document)
    admin.site.register(Track)
admin.site.register(Overlay)
