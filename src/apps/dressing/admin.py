"""
Esup-Pod - Dressing administrator interface.
"""

from django.contrib import admin
from src.apps.dressing.models import Dressing


@admin.register(Dressing)
class DressingAdmin(admin.ModelAdmin):
    """
    Admin interface for Dressing model.

    Controls watermarks, opening/ending credits and access permissions
    for video dressings (habillage).
    """

    list_display = ("id", "title", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title",)
    filter_horizontal = ("owners", "users", "allow_to_groups", "videos")
    raw_id_fields = ("watermark", "opening_credits", "ending_credits")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "owners",
                    "users",
                    "allow_to_groups",
                )
            },
        ),
        (
            "Watermark",
            {
                "fields": ("watermark", "position", "opacity"),
            },
        ),
        (
            "Credits",
            {
                "fields": ("opening_credits", "ending_credits"),
            },
        ),
        (
            "Videos",
            {
                "fields": ("videos",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
