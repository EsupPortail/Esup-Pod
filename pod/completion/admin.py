from django.contrib import admin
from pod.completion.models import Contributor
from pod.completion.models import Document
from pod.completion.models import Overlay
from pod.completion.forms import DocumentForm
try:
	__import__('pod.filepicker')
	FILEPICKER = True
except:
	FILEPICKER = False
	pass


class ContributorInline(admin.TabularInline):
    model = Contributor
    extra = 0


class DocumentInline(admin.TabularInline):
    model = Document
    if FILEPICKER:
    	form = DocumentForm
    extra = 0


class DocumentAdmin(admin.ModelAdmin):

    form = DocumentForm

    class Media:
        js = ('js/jquery.tools.min.js',)


class OverlayInline(admin.TabularInline):
    model = Overlay
    extra = 0

admin.site.register(Contributor)
if FILEPICKER:
	admin.site.register(Document, DocumentAdmin)
else:
	admin.site.register(Document)
admin.site.register(Overlay)
