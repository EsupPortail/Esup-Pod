from django.contrib import admin
from pod.playlist.models import Playlist
from pod.playlist.models import PlaylistElement
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from pod.video.models import Video


class PlaylistAdmin(admin.ModelAdmin):

    list_display = ('title', 'owner', 'visible',)
    list_display_links = ('title',)
    list_editable = ('visible',)
    ordering = ('title', 'id',)
    list_filter = ['visible']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "owner":
            kwargs["queryset"] = User.objects.filter(
                    owner__sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(owner__owner__sites=get_current_site(
                request))
        return qs


admin.site.register(Playlist, PlaylistAdmin)


class PlaylistElementAdmin(admin.ModelAdmin):

    list_display = ('playlist', 'video', 'position',)
    list_display_links = ('playlist',)
    list_editable = ('position',)
    ordering = ('playlist__title', 'id',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(playlist__owner__owner__sites=get_current_site(
                request))
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if (db_field.name) == "playlist":
            kwargs["queryset"] = Playlist.objects.filter(
                    owner__owner__sites=Site.objects.get_current())
        if (db_field.name) == "video":
            kwargs["queryset"] = Video.objects.filter(
                    sites=Site.objects.get_current())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {
            "all": (
                'css/pod.css',
            )
        }


admin.site.register(PlaylistElement, PlaylistElementAdmin)
