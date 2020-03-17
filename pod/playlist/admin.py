from django.contrib import admin
from pod.playlist.models import Playlist
from pod.playlist.models import PlaylistElement
from django.contrib.sites.shortcuts import get_current_site


class PlaylistAdmin(admin.ModelAdmin):

    list_display = ('title', 'owner', 'visible',)
    list_display_links = ('title',)
    list_editable = ('visible',)
    ordering = ('title', 'id',)
    list_filter = ['visible']

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term)
        if not request.user.is_superuser:
            queryset = queryset.filter(owner__owner__sites=get_current_site(
                request))
        return queryset, use_distinct


admin.site.register(Playlist, PlaylistAdmin)


class PlaylistElementAdmin(admin.ModelAdmin):

    list_display = ('playlist', 'video', 'position',)
    list_display_links = ('playlist',)
    list_editable = ('position',)
    ordering = ('playlist__title', 'id',)

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(
            request, queryset, search_term)
        if not request.user.is_superuser:
            queryset = queryset.filter(
                playlist__owner__owner__sites=get_current_site(
                    request))
        return queryset, use_distinct

    class Media:
        css = {
            "all": (
                'css/pod.css',
            )
        }


admin.site.register(PlaylistElement, PlaylistElementAdmin)
