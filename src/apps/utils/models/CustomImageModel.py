import os
import mimetypes
from django.db import models
from django.utils.translation import gettext_lazy as _ 
from django.utils.text import slugify
from django.conf import settings

FILES_DIR = getattr(settings, "FILES_DIR", "files")

def get_upload_path_files(instance, filename) -> str:
    fname, dot, extension = filename.rpartition(".")
    try:
        fname.index("/")
        return os.path.join(
            FILES_DIR,
            "%s/%s.%s"
            % (
                os.path.dirname(fname),
                slugify(os.path.basename(fname)),
                extension,
            ),
        )
    except ValueError:
        return os.path.join(FILES_DIR, "%s.%s" % (slugify(fname), extension))
    
class CustomImageModel(models.Model):
    """Esup-Pod custom image Model."""

    file = models.ImageField(
        _("Image"),
        null=True,
        upload_to=get_upload_path_files,
        blank=True,
        max_length=255,
    )

    @property
    def file_type(self) -> str:
        filetype = mimetypes.guess_type(self.file.path)[0]
        if filetype is None:
            fname, dot, extension = self.file.path.rpartition(".")
            filetype = extension.lower()
        return filetype

    file_type.fget.short_description = _("Get the file type")

    @property
    def file_size(self) -> int:
        return os.path.getsize(self.file.path)

    file_size.fget.short_description = _("Get the file size")

    @property
    def name(self) -> str:
        return os.path.basename(self.file.path)

    name.fget.short_description = _("Get the file name")

    def file_exist(self) -> bool:
        return self.file and os.path.isfile(self.file.path)

    def __str__(self) -> str:
        return "%s (%s, %s)" % (self.name, self.file_type, self.file_size)