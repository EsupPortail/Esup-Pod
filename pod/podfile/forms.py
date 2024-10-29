"""Podfile forms definitions."""

from django import forms
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat
from django.core.exceptions import ValidationError

from .models import UserFolder
from .models import CustomFileModel
from .models import CustomImageModel


FILE_ALLOWED_EXTENSIONS = getattr(
    settings,
    "FILE_ALLOWED_EXTENSIONS",
    (
        "doc",
        "docx",
        "odt",
        "pdf",
        "xls",
        "xlsx",
        "ods",
        "ppt",
        "pptx",
        "txt",
        "html",
        "htm",
        "vtt",
        "srt",
    ),
)
IMAGE_ALLOWED_EXTENSIONS = getattr(
    settings,
    "IMAGE_ALLOWED_EXTENSIONS",
    ("jpg", "jpeg", "bmp", "png", "gif", "tiff", "webp"),
)
FILE_MAX_UPLOAD_SIZE = getattr(settings, "FILE_MAX_UPLOAD_SIZE", 10)


@deconstructible
class FileSizeValidator(object):
    message = _(
        "The current file %(size)s, which is too large. "
        "The maximum file size is %(allowed_size)s."
    )
    code = "invalid_max_size"

    def __init__(self, *args, **kwargs) -> None:
        self.max_size = FILE_MAX_UPLOAD_SIZE * 1024 * 1024  # MO

    def __call__(self, value) -> None:
        # Check the file size
        filesize = len(value)
        if self.max_size and filesize > self.max_size:
            raise ValidationError(
                self.message,
                code=self.code,
                params={
                    "size": filesizeformat(filesize),
                    "allowed_size": filesizeformat(self.max_size),
                },
            )


class UserFolderForm(forms.ModelForm):
    class Meta:
        model = UserFolder
        fields = ("name",)


class CustomFileModelForm(forms.ModelForm):
    fileattrs = {
        "class": "form-control-file ms-2",
        "accept": ".%s" % ", .".join(map(str, FILE_ALLOWED_EXTENSIONS)),
        "data-maxsize": FILE_MAX_UPLOAD_SIZE * 1024 * 1024,
    }

    def __init__(self, *args, **kwargs):
        super(CustomFileModelForm, self).__init__(*args, **kwargs)
        self.fields["folder"].widget = forms.HiddenInput()
        valid_ext = FileExtensionValidator(FILE_ALLOWED_EXTENSIONS)
        self.fields["file"].validators = [valid_ext, FileSizeValidator]
        self.fields["file"].widget.attrs["class"] = self.fileattrs["class"]
        self.fields["file"].widget.attrs["accept"] = self.fileattrs["accept"]
        self.fields["file"].widget.attrs["data-maxsize"] = self.fileattrs["data-maxsize"]

    class Meta:
        model = CustomFileModel
        fields = ("file", "folder")
        labels = {
            "file": _("Choose File"),
        }


class CustomImageModelForm(forms.ModelForm):
    fileattrs = {
        "class": "form-control-file ms-2",
        "accept": ".%s" % ", .".join(map(str, IMAGE_ALLOWED_EXTENSIONS)),
        "data-maxsize": FILE_MAX_UPLOAD_SIZE * 1024 * 1024,
    }

    def __init__(self, *args, **kwargs) -> None:
        super(CustomImageModelForm, self).__init__(*args, **kwargs)
        self.fields["folder"].widget = forms.HiddenInput()
        valid_ext = FileExtensionValidator(IMAGE_ALLOWED_EXTENSIONS)
        self.fields["file"].validators = [valid_ext, FileSizeValidator]
        self.fields["file"].widget.attrs["class"] = self.fileattrs["class"]
        self.fields["file"].widget.attrs["accept"] = self.fileattrs["accept"]
        self.fields["file"].widget.attrs["data-maxsize"] = self.fileattrs["data-maxsize"]

    class Meta:
        model = CustomImageModel
        fields = ("file", "folder")
        labels = {
            "file": _("Choose image file"),
        }
