from django.contrib import admin
from pod.chapter.models import Chapter
from django.contrib.sites.shortcuts import get_current_site


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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(video__sites=get_current_site(
                request))
        return qs


admin.site.register(Chapter, ChapterAdmin)


class ChapterInline(admin.TabularInline):

    model = Chapter
    extra = 0
