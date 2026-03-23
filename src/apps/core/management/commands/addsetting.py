"""
Esup-Pod - Django management command to add or update a setting inside a specific
application configuration stored in `configuration.json`.

Launch with `python3 manage.py addsetting <app_name> <setting_name>`
"""

import os
import json

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings as django_settings


class Command(BaseCommand):
    """
    Management command to interactively add or update settings in the global
    configuration.json file.
    """

    help = "Add setting to specific app configuration"

    def add_arguments(self, parser):
        """
        Defines the required arguments: app_name and setting_name.
        """
        parser.add_argument(
            "app_name", type=str, help="Name of the app (e.g., authentication, core)"
        )
        parser.add_argument(
            "setting_name", type=str, help="Name of the setting (e.g., MY_NEW_SETTING)"
        )

    def get_setting(self, options):
        """
        Retrieves the current value of a setting from configuration.json if it exists.
        """
        filename = os.path.join(
            django_settings.BASE_DIR, "src", "apps", "core", "configuration.json"
        )
        with open(filename, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        app_name = options["app_name"]

        # We only look in configuration_apps -> description
        if app_name not in data[0]["configuration_apps"]["description"]:
            raise CommandError(
                'Application name "%s" not found in configuration file' % app_name
            )

        app_settings = data[0]["configuration_apps"]["description"][app_name].get(
            "settings", {}
        )

        if app_settings.get(options["setting_name"]):
            self.stdout.write(self.style.WARNING(20 * "*"))
            self.stdout.write(
                self.style.WARNING("Setting found in json file, you will modify it!")
            )
            setting_json = json.dumps(
                app_settings[options["setting_name"]],
                sort_keys=False,
                indent=2,
                ensure_ascii=False,
            )
            self.stdout.write(self.style.SUCCESS(setting_json))
            self.stdout.write(self.style.WARNING(20 * "*"))
            return app_settings[options["setting_name"]]
        else:
            return {}

    def save_setting(self, options, setting):
        """
        Writes the updated setting back to the configuration.json file.
        """
        filename = os.path.join(
            django_settings.BASE_DIR, "src", "apps", "core", "configuration.json"
        )
        with open(filename, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        app_name = options["app_name"]
        if "settings" not in data[0]["configuration_apps"]["description"][app_name]:
            data[0]["configuration_apps"]["description"][app_name]["settings"] = {}

        data[0]["configuration_apps"]["description"][app_name]["settings"][
            options["setting_name"]
        ] = setting

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, sort_keys=True, indent=2, ensure_ascii=False)

    def fix_default_value(self, default_value):
        """
        Interactively prompts the user for a default value and performs basic
        type conversion (bool, int).
        """
        msg = "Default value (leave blank to keep previous value: %s): " % default_value
        if default_value == "":
            msg = "Default value: "
        input_value = input(msg)
        if input_value != "":
            default_value = input_value
        if default_value == "False":
            default_value = False
        if default_value == "True":
            default_value = True
        if not isinstance(default_value, bool) and str(default_value).isdigit():
            default_value = int(default_value)
        return default_value

    def get_description(self, previous_description):
        """
        Prompts the user for a multi-line description.
        """
        if previous_description != [""]:
            print("(--> Type enter directly to keep previous value!)")
        description = [""]
        while True:
            user_input = input()
            if user_input == "":
                break
            else:
                description.append(user_input)
        if description == [""]:
            description = previous_description
        return description

    def handle(self, *args, **options):
        """
        Main execution logic for the command. Collects data and saves it.
        """
        self.stdout.write(
            self.style.SUCCESS('Setting name "%s"' % options["setting_name"])
        )
        self.stdout.write(self.style.SUCCESS('App name "%s"' % options["app_name"]))

        setting = self.get_setting(options)

        current_version = getattr(django_settings, "POD_VERSION", "5.0.0")

        pod_version_init = input(
            "Pod initial version (leave blank to put current version: %s): "
            % current_version
        )
        if pod_version_init == "":
            pod_version_init = current_version

        pod_version_end = input(
            "Pod last version (i.e: 2.9.0, deprecated or not use anymore): "
        )

        default_value = self.fix_default_value(setting.get("default_value", ""))

        print("Add a english description (leave blank and type enter to leave):")
        previous_value = (
            setting["description"].get("en", [""]) if setting.get("description") else [""]
        )
        description_en = self.get_description(previous_value)

        print("Add a french description (leave blank and type enter to leave):")
        previous_value = (
            setting["description"].get("fr", [""]) if setting.get("description") else [""]
        )
        description_fr = self.get_description(previous_value)

        setting = {
            "pod_version_init": pod_version_init,
            "default_value": default_value,
            "description": {"en": description_en, "fr": description_fr},
        }
        if pod_version_end:
            setting["pod_version_end"] = pod_version_end

        setting_json = json.dumps(
            {options["setting_name"]: setting},
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        self.stdout.write(self.style.SUCCESS(setting_json))
        confirm = input("Save it to config file? y/n: ")
        if confirm != "y":
            self.stdout.write(self.style.ERROR("Not saving, End!"))
            return
        self.save_setting(options, setting)
        self.stdout.write(self.style.SUCCESS("End!"))
