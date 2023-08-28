"""Esup-Pod playlist admin"""
from django.contrib import admin

from .models import Playlist, PlaylistContent


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Playlist admin page."""

    date_hierarchy = "date_updated"
    list_display = (
        "id",
        "name",
        "owner",
        "visibility",
        "date_updated",
        "date_created",
        "autoplay",
    )
    list_display_links = ("id", "name")
    list_filter = (
        "date_created",
        "date_updated",
        "visibility",
        "autoplay",
    )
    search_fields = [
        "name",
        "owner__username",
        "owner__first_name",
        "owner__last_name",
    ]


@admin.register(PlaylistContent)
class PlaylistContentAdmin(admin.ModelAdmin):
    """PlaylistContent admin page."""

    date_hierarchy = "date_added"
    list_display = (
        "id",
        "playlist",
        "video",
        "date_added",
        "rank",
    )
    list_display_links = ("id", )
    list_filter = (
        "video",
        "playlist",
    )
