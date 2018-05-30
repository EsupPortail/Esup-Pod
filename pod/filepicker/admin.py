"""
Custom Admin for filepicker
Use custom models for Image and File

django-file-picker : 0.9.1.
"""
from django.contrib import admin
from pod.filepicker.models import CustomFileModel
from pod.filepicker.models import CustomImageModel
from pod.filepicker.models import UserDirectory


class UserDirectoryAdmin(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.name == 'Home':
            return ('parent',)
        else:
            return ()

    list_display = ('name', 'owner',)
    list_display_links = ('name',)
    list_filter = ('owner',)
    ordering = ('name', 'owner',)


admin.site.register(UserDirectory, UserDirectoryAdmin)


class CustomImageModelAdmin(admin.ModelAdmin):

    list_display = ('name', 'file_type', 'created_by',)
    list_display_links = ('name',)
    list_filter = ('name', 'created_by',)
    ordering = ('name', 'created_by',)
    readonly_fields = ('file_size', 'file_type',)


admin.site.register(CustomImageModel, CustomImageModelAdmin)


class CustomFileModelAdmin(admin.ModelAdmin):

    list_display = ('name', 'file_type', 'created_by',)
    list_display_links = ('name',)
    list_filter = ('name', 'created_by',)
    ordering = ('name', 'created_by',)
    readonly_fields = ('file_size', 'file_type',)


admin.site.register(CustomFileModel, CustomFileModelAdmin)
