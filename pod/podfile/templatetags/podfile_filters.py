import os

from django import template
from django.core.files.storage import default_storage

ICON_LISTE = [
    "css",
    "default",
    "doc",
    "docx",
    "gif",
    "html",
    "jpg",
    "js",
    "mkv",
    "mp3",
    "mp4",
    "odp",
    "ods",
    "odt",
    "pdf",
    "png",
    "ppt",
    "pptx",
    "psd",
    "swf",
    "txt",
    "vtt",
    "xls",
    "xlsx",
    "zip",
]

register = template.Library()


@register.filter(name="file_exists")
def file_exists(filepath):
    if default_storage.exists(filepath):
        return filepath
    else:
        index = filepath.rfind("/")
        new_filepath = filepath[:index] + "/image.png"
        return new_filepath


@register.filter(name="file_extension")
def file_extension(filename):
    """Return a normalized extension without the leading dot."""
    return os.path.splitext(str(filename))[1].removeprefix(".").lower()


@register.filter(name="file_basename")
def file_basename(filename):
    """Return the complete file name, including its extension."""
    return os.path.basename(str(filename))


@register.filter(name="icon_exists")
def icon_exists(filename):
    extension = file_extension(filename)
    if extension in ICON_LISTE:
        return extension
    else:
        return "default"
