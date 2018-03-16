"""
Custom Admin for filepicker
Use custom models for Image and File

django-file-picker : 0.9.1.
"""
from django.contrib import admin
from .models import CustomFileModel, CustomImageModel
from file_picker.uploads.models import Image, File

admin.site.unregister(Image)
admin.site.unregister(File)
admin.site.register(CustomImageModel)
admin.site.register(CustomFileModel)
