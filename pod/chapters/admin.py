from django.contrib import admin
from pod.chapters.models import Chapter


class ChapterAdmin(admin.ModelAdmin):

    list_display = ('title', 'video',)
    list_display_links = ('title',)
admin.site.register(Chapter, ChapterAdmin)


class ChapterInline(admin.TabularInline):

    model = Chapter
    extra = 0
