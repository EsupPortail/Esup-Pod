from django import template
from django.core.files.storage import default_storage

# import os

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
    "pdf",
    "png",
    "ppt",
    "pptx",
    "psd",
    "swf",
    "txt",
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


@register.filter(name="icon_exists")
def icon_exists(filename):
    fname, dot, extension = filename.rpartition(".")
    # print(fname, extension)
    if extension in ICON_LISTE:
        return extension
    else:
        return "default"
