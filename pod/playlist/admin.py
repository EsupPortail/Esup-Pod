from django.contrib import admin
from pod.playlist.models import Playlist
from pod.playlist.models import PlaylistElement


class PlaylistAdmin(admin.ModelAdmin):

    list_display = ('title', 'owner', 'visible',)
    list_display_links = ('title',)
    list_editable = ('visible',)
    ordering = ('title', 'id',)
    list_filter = ['visible']


admin.site.register(Playlist, PlaylistAdmin)


class PlaylistElementAdmin(admin.ModelAdmin):

    list_display = ('playlist', 'video', 'position',)
    list_display_links = ('playlist',)
    list_editable = ('position',)
    ordering = ('playlist__title', 'id',)

    class Media:
        css = {
            "all": (
                'css/pod.css',
            )
        }


admin.site.register(PlaylistElement, PlaylistElementAdmin)
