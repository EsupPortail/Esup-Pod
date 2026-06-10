"""
Esup-Pod - Custom image model utilities.
"""

import mimetypes
import os

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from .paths import get_upload_path_files


class CustomImageModel(models.Model):
    """Custom image model."""

    file = models.ImageField(
        _("Image"),
        null=True,
        upload_to=get_upload_path_files,
        blank=True,
        max_length=255,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Created by"),
    )

    @property
    def file_type(self) -> str:
        """
        Identify the file type using mimetypes or falling back to the extension.
        """
        if not self.file or not os.path.isfile(self.file.path):
            return ""
        filetype = mimetypes.guess_type(self.file.path)[0]
        if filetype is None:
            fname, dot, extension = self.file.path.rpartition(".")
            filetype = extension.lower()
        return filetype

    file_type.fget.short_description = _("Get the file type")

    @property
    def file_size(self) -> int:
        """
        Retrieve the file size in bytes from the filesystem.
        """
        if not self.file or not os.path.isfile(self.file.path):
            return 0
        return os.path.getsize(self.file.path)

    file_size.fget.short_description = _("Get the file size")

    @property
    def name(self) -> str:
        """
        Extract the base name of the file.
        """
        if not self.file or not os.path.isfile(self.file.path):
            return ""
        return os.path.basename(self.file.path)

    name.fget.short_description = _("Get the file name")

    def file_exist(self) -> bool:
        """
        Verify if the file actually exists on the filesystem.
        """
        return bool(self.file and os.path.isfile(self.file.path))

    def delete(self, *args, **kwargs) -> None:
        """Delete CustomImageModel instance and remove file from disk."""
        if self.file and self.file_exist():
            try:
                os.remove(self.file.path)
            except OSError:
                pass
        super().delete(*args, **kwargs)

    def __str__(self) -> str:
        """
        Return a string representation including name, type, and size.
        """
        if self.file and self.file_exist():
            return "%s (%s, %s)" % (self.name, self.file_type, self.file_size)
        return "CustomImageModel (No file)"
