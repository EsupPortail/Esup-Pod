"""
Esup-pod comparesettings command
"""

from django.core.management.base import BaseCommand

# import re
import os
import importlib
import json

__OLD_SETTINGS__ = [
    "BBB_NUMBER_DAYS_BEFORE_DELETE",
    "BBB_NUMBER_MAX_LIVES",
    "BBB_SERVER_URL",
    "BBB_USERNAME_FORMAT",
    "BBB_VERSION_IS_23",
    "DEFAULT_BBB_PATH",
    "DEFAULT_BBB_PLUGIN",
    "DEFAULT_BBB_TYPE_ID",
]


class Command(BaseCommand):
    help = "Get all settings for the specified app and compare it to configuration file"

    def handle(self, *args, **options):
        mod = importlib.import_module(".".join(["pod", "custom", "settings_local"]))
        items = dir(mod)
        settings_list = [
            item
            for item in items
            if (not item.startswith("__") and item.isupper() and len(item) > 1)
        ]
        local_settings_list = list(dict.fromkeys(settings_list))
        local_settings_list.sort()
        self.print_log("Settings local", local_settings_list)
        json_settings = self.get_all_settings()
        json_settings += __OLD_SETTINGS__
        new_settings = list(set(local_settings_list) - set(json_settings))
        new_settings.sort()
        self.print_log("Local setting not in global configuration file : ", new_settings)
        # raise CommandError('Poll "%s" does not exist' % poll_id)
        # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))

    def print_log(self, title: str, data: list[str]) -> None:
        print(20 * "-")
        print(f"{title}:")
        print("\n    - " + "\n    - ".join(data))
        # print(20 * "-")

    def get_all_settings(self):
        with open(os.path.join("pod", "main", "configuration.json"), "r") as json_file:
            data = json.load(json_file)
        json_settings = []
        pod_settings = data[0]["configuration_pod"]["description"]
        for keys in pod_settings.keys():
            keys_settings = pod_settings[keys]["settings"]
            json_settings += keys_settings.keys()
        app_settings = data[0]["configuration_apps"]["description"]
        for keys in app_settings.keys():
            keys_settings = app_settings[keys]["settings"]
            json_settings += keys_settings.keys()
        return json_settings
