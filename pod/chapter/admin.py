from django.contrib import admin
from pod.chapter.models import Chapter


class ChapterAdmin(admin.ModelAdmin):

    list_display = ('title', 'video',)
    list_display_links = ('title',)
    search_fields = ['id', 'title', 'video__title']

    class Media:
        css = {
            "all": (
                'css/pod.css',
            )
        }


admin.site.register(Chapter, ChapterAdmin)


class ChapterInline(admin.TabularInline):

    model = Chapter
    extra = 0
