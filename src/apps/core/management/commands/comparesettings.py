from django.core.management.base import BaseCommand
from django.conf import settings

import json
import os


class Command(BaseCommand):
    help = "Compare settings in code vs configuration.json"

    def handle(self, *args, **options):
        all_live_settings = dir(settings)
        local_settings_list = [
            item for item in all_live_settings
            if (not item.startswith("__") and item.isupper())
        ]
        local_settings_list.sort()
        self.print_log("Active Django Settings", local_settings_list)
        conf_path = os.path.join(settings.BASE_DIR, "src", "apps", "core", "configuration.json")
        with open(conf_path, "r") as json_file:
            data = json.load(json_file)
        json_settings = []
        if "configuration_pod" in data[0]:
            pod_settings = data[0]["configuration_pod"]["description"]
            for keys in pod_settings.keys():
                json_settings += pod_settings[keys]["settings"].keys()
        if "configuration_apps" in data[0]:
            app_settings = data[0]["configuration_apps"]["description"]
            for keys in app_settings.keys():
                json_settings += app_settings[keys]["settings"].keys()
        new_settings = list(set(local_settings_list) - set(json_settings))
        new_settings.sort()
        self.print_log("Settings in Code but MISSING in configuration.json", new_settings)

    def print_log(self, title: str, data: list[str]) -> None:
        print(20 * "-")
        print(f"{title}:")
        print("\n    - " + "\n    - ".join(data[:20]))
        if len(data) > 20:
            print(f"    ... and {len(data) - 20} more.")
