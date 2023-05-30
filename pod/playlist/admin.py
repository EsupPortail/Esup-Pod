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
    )

@admin.register(PlaylistContent)
class PlaylistContentAdmin(admin.ModelAdmin):
    """PlaylistContent admin page."""

    ...
