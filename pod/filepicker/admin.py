"""
Custom Admin for filepicker
Use custom models for Image and File

django-file-picker : 0.9.1.
"""
from django.contrib import admin
from pod.filepicker.models import CustomFileModel
from pod.filepicker.models import CustomImageModel
from pod.filepicker.models import UserDirectory

admin.site.register(CustomImageModel)
admin.site.register(CustomFileModel)
admin.site.register(UserDirectory)
