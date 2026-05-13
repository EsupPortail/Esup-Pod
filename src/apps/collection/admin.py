"""
Esup-Pod - Admin configuration for the collection app.
"""

from django.contrib import admin
from .models import Channel, Theme, ThemeItem, Playlist, PlaylistItem, Favorite


class ThemeItemInline(admin.TabularInline):
    """
    Inline admin for ThemeItem to manage videos within a theme.
    """

    model = ThemeItem
    extra = 1


class PlaylistItemInline(admin.TabularInline):
    """
    Inline admin for PlaylistItem to manage videos within a playlist.
    """

    model = PlaylistItem
    extra = 1


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Channel model.
    """

    list_display = ("title", "slug", "owner", "is_public", "created_at")
    search_fields = ("title", "description", "owner__username", "slug")
    list_filter = ("is_public", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("collaborators",)


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Theme model.
    """

    list_display = ("title", "slug", "channel", "parent", "created_at")
    search_fields = ("title", "description", "slug")
    list_filter = ("created_at",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ThemeItemInline]


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Playlist model.
    """

    list_display = (
        "title",
        "slug",
        "owner",
        "is_public",
        "created_at",
    )
    search_fields = ("title", "description", "owner__username", "slug")
    list_filter = ("is_public", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PlaylistItemInline]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Favorite model.
    """

    list_display = ("user", "video", "added_at")
    search_fields = ("user__username", "video__title")
    list_filter = ("added_at",)
