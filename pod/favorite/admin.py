"""Esup-Pod Favorite video admin."""
from django.contrib import admin
from .models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Favorite video admin page."""

    date_hierarchy = "date_added"
    list_display = (
        "id",
        "video",
        "owner",
        "date_added",
        "rank",
    )
    list_filter = ("owner", "date_added", "rank")
    search_fields = ("video__title", "owner__username")
