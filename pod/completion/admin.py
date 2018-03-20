from django.contrib import admin
from pod.completion.models import Contributor
from pod.completion.models import Document

class ContributorAdmin(admin.TabularInline):
	model = Contributor
	extra = 0

class DocumentAdmin(admin.TabularInline):
	model = Document
	extra = 0

admin.site.register(Contributor)
admin.site.register(Document)

