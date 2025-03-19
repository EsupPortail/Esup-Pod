"""
Esup-pod getsettings command
"""

from django.core.management.base import BaseCommand

# import re
import os
import fnmatch
import importlib
import json


class Command(BaseCommand):
    help = "Get all settings for the specified app and compare it to configuration file"

    def add_arguments(self, parser):
        parser.add_argument("app_name", type=str)

    def handle(self, *args, **options):
        files_names = fnmatch.filter(os.listdir("pod/" + options["app_name"]), "*.py")
        global_settings_list = []
        for f in files_names:
            if "settings" in str(f):
                continue
            print(" - %s" % f)
            mod = importlib.import_module(
                ".".join(["pod", options["app_name"], f.replace(".py", "")])
            )
            items = dir(mod)
            settings_list = [
                item
                for item in items
                if (not item.startswith("__") and item.isupper() and len(item) > 1)
            ]
            global_settings_list += settings_list
        global_settings_list = list(dict.fromkeys(global_settings_list))
        global_settings_list.sort()
        self.print_log(options["app_name"], global_settings_list)
        with open(os.path.join("pod", "main", "configuration.json"), "r") as json_file:
            data = json.load(json_file)
        json_settings = []
        pod_settings = data[0]["configuration_pod"]["description"]
        for keys in pod_settings.keys():
            keys_settings = pod_settings[keys]["settings"]
            json_settings += keys_settings.keys()
        app_settings = data[0]["configuration_apps"]["description"]
        app_settings = app_settings[options["app_name"]]["settings"]
        self.print_log(
            "Configuration json setting for %s" % options["app_name"], app_settings.keys()
        )
        json_settings += app_settings.keys()
        new_settings = list(set(global_settings_list) - set(json_settings))
        new_settings.sort()
        self.print_log("New settings from JSON", new_settings)
        # raise CommandError('Poll "%s" does not exist' % poll_id)
        # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))

    def print_log(self, title: str, data: list[str]) -> None:
        print(20 * "-")
        print(f"{title}:")
        print("\n    - " + "\n    - ".join(data))
        # print(20 * "-")
