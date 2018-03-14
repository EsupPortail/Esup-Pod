"""
Custom Model for filepicker
Override File and Image models from file_picker

django-file-picker : 0.9.1.
"""
from django.conf import settings
from django.db import models
from file_picker.uploads.models import BaseFileModel
from pod.authentication.models import Owner

import os


def get_upload_path(instance, filename):
    user_hash = Owner.objects.get(user=instance.created_by).hashkey
    return 'files/{0}/{1}'.format(user_hash, filename)


class CustomFileModel(BaseFileModel):
    file = models.FileField(upload_to=get_upload_path)


class CustomImageModel(BaseFileModel):
    file = models.ImageField(upload_to=get_upload_path)
