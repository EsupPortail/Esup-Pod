"""
Esup-Pod - Admin configuration for utils app.
"""

from django.contrib import admin
from src.apps.utils.models.CustomImageModel import CustomImageModel


@admin.register(CustomImageModel)
class CustomImageModelAdmin(admin.ModelAdmin):
    """
    Admin configuration for CustomImageModel.
    """

    list_display = ("id", "file", "file_type", "file_size")
    search_fields = ("file",)
