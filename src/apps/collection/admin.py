"""
Esup-Pod - Admin configuration for the collection app.
"""

from django.contrib import admin
from .models import Channel, Theme, ThemeItem, Playlist, PlaylistItem, Favorite


class ThemeItemInline(admin.TabularInline):
    """Inline admin for ThemeItem to manage videos within a theme."""

    model = ThemeItem
    extra = 0
    raw_id_fields = ("video",)
    readonly_fields = ("added_at",)
    show_change_link = True


class PlaylistItemInline(admin.TabularInline):
    """Inline admin for PlaylistItem to manage videos within a playlist."""

    model = PlaylistItem
    extra = 0
    raw_id_fields = ("video",)
    show_change_link = True


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    """Admin configuration for the Channel model."""

    list_display = ("title", "slug", "owner", "is_public", "created_at")
    search_fields = ("title", "description", "owner__username", "slug")
    list_filter = ("is_public", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("collaborators",)
    raw_id_fields = ("owner",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    """Admin configuration for the Theme model."""

    list_display = ("title", "slug", "channel", "parent", "created_at")
    search_fields = ("title", "description", "slug", "channel__title")
    list_filter = ("created_at",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ThemeItemInline]
    raw_id_fields = ("channel", "parent")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ThemeItem)
class ThemeItemAdmin(admin.ModelAdmin):
    """Admin configuration for ThemeItem (video in a theme)."""

    list_display = ("theme", "video", "added_at")
    search_fields = ("theme__title", "video__title")
    raw_id_fields = ("theme", "video")
    readonly_fields = ("added_at",)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Admin configuration for the Playlist model."""

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
    raw_id_fields = ("owner",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(PlaylistItem)
class PlaylistItemAdmin(admin.ModelAdmin):
    """Admin configuration for PlaylistItem (video in a playlist)."""

    list_display = ("playlist", "video", "position")
    search_fields = ("playlist__title", "video__title")
    raw_id_fields = ("playlist", "video")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin configuration for the Favorite model."""

    list_display = ("user", "video", "added_at")
    search_fields = ("user__username", "video__title")
    list_filter = ("added_at",)
    raw_id_fields = ("user", "video")
    readonly_fields = ("added_at",)
    date_hierarchy = "added_at"
