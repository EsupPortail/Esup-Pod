from django.contrib import admin
from pod.completion.models import Contributor

class ContributorAdmin(admin.TabularInline):
	model = Contributor
	extra = 0

admin.site.register(Contributor)

