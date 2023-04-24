from django.contrib import admin
from .models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    date_hierarchy = "date_added"
    list_display = (
        "id",
        "video",
        "owner",
        "date_added",
        "rank",
    )
    list_filter = ("id", "owner", "date_added")
    search_fields = ("video__title", "owner__username")
