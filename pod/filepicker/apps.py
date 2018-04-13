from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class FilePickerConfig(AppConfig):
    name = 'pod.filepicker'

    def ready(self):
        autodiscover_modules('file_pickers')
