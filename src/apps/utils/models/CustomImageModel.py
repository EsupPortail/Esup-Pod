"""
Esup-Pod - Custom image model utilities.
"""

import mimetypes
import os

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

FILES_DIR = getattr(settings, "FILES_DIR", "files")


class CustomImageModel(models.Model):
    """Esup-Pod custom image Model."""

    @staticmethod
    def get_upload_path_files(instance, filename) -> str:
        """
        Generate the upload path for image files by slugifying the filename
        to ensure local filesystem compatibility.
        """
        fname, dot, extension = filename.rpartition(".")
        if "/" in fname:
            return os.path.join(
                FILES_DIR,
                "%s/%s.%s"
                % (
                    os.path.dirname(fname),
                    slugify(os.path.basename(fname)),
                    extension,
                ),
            )
        return os.path.join(FILES_DIR, "%s.%s" % (slugify(fname), extension))

    file = models.ImageField(
        _("Image"),
        null=True,
        upload_to="get_upload_path_files",
        blank=True,
        max_length=255,
    )

    @property
    def file_type(self) -> str:
        """
        Identify the file type using mimetypes or falling back to the extension.
        """
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
        return os.path.getsize(self.file.path)

    file_size.fget.short_description = _("Get the file size")

    @property
    def name(self) -> str:
        """
        Extract the base name of the file.
        """
        return os.path.basename(self.file.path)

    name.fget.short_description = _("Get the file name")

    def file_exist(self) -> bool:
        """
        Verify if the file actually exists on the filesystem.
        """
        return self.file and os.path.isfile(self.file.path)

    def __str__(self) -> str:
        """
        Return a string representation including name, type, and size.
        """
        return "%s (%s, %s)" % (self.name, self.file_type, self.file_size)
