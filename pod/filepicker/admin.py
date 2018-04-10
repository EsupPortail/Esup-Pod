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

    list_display = ('name', 'owner')
    ordering = ('owner',)

admin.site.register(UserDirectory, UserDirectoryAdmin)


admin.site.register(CustomImageModel)
admin.site.register(CustomFileModel)
