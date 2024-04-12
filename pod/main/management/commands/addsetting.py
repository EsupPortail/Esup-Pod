from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import json
import os

VERSION = getattr(settings, "VERSION", "")


class Command(BaseCommand):
    help = "Add setting to specific app"

    def add_arguments(self, parser):
        parser.add_argument(
            "app_name",
            type=str,
            help="the name of the app to add the setting, use pod for a global setting",
        )
        parser.add_argument("setting_name", type=str, help="the name of the setting")

    def get_setting(self, options, config_part):
        data = app_settings = settings = []
        filename = os.path.join("pod", "main", "configuration.json")
        with open(filename, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        if options["app_name"] == "pod":
            app_settings = data[0]["configuration_pod"]["description"]
            app_name = config_part
        else:
            app_settings = data[0]["configuration_apps"]["description"]
            app_name = options["app_name"]

        try:
            settings = app_settings[app_name]["settings"]
        except KeyError:
            raise CommandError(
                'Application name "%s" not found in configuration file' % app_name
            )

        if settings.get(options["setting_name"]):
            self.stdout.write(self.style.WARNING(20 * "*"))
            self.stdout.write(
                self.style.WARNING("Setting found in json file, you will modify it!")
            )
            setting_json = json.dumps(
                settings[options["setting_name"]],
                sort_keys=False,
                indent=2,
                ensure_ascii=False,
            )
            self.stdout.write(self.style.SUCCESS(setting_json))
            self.stdout.write(self.style.WARNING(20 * "*"))
            return settings[options["setting_name"]]
        else:
            return {}

    def get_configuration_pod(self):
        filename = os.path.join("pod", "main", "configuration.json")
        with open(filename, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
        return data[0]["configuration_pod"]["description"].keys()

    def save_setting(self, options, config_part, setting):
        filename = os.path.join("pod", "main", "configuration.json")
        with open(filename, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        if options["app_name"] == "pod":
            data[0]["configuration_pod"]["description"][config_part]["settings"][
                options["setting_name"]
            ] = setting
        else:
            data[0]["configuration_apps"]["description"][options["app_name"]]["settings"][
                options["setting_name"]
            ] = setting
        os.remove(filename)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, sort_keys=True, indent=4, ensure_ascii=False)

    def fix_default_value(self, default_value):
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
        if not isinstance(default_value, bool) and default_value.isdigit():
            default_value = int(default_value)
        return default_value

    def get_description(self, previous_description):
        if previous_description != [""]:
            print("(--> Type enter directly to keep previous value!)")
        description = [""]
        while True:
            user_input = input()
            # 👇️ if user pressed Enter without a value, break out of loop
            if user_input == "":
                break
            else:
                description.append(user_input)
        if description == [""]:
            description = previous_description
        return description

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting name "%s"' % options["setting_name"])
        )
        self.stdout.write(self.style.SUCCESS('App name "%s"' % options["app_name"]))

        config_part = "main"
        if options["app_name"] == "pod":
            list_conf = self.get_configuration_pod()
            print("Here is available configuration: %s" % ", ".join(list_conf))
            config_part = input(
                "Give configuration part in available configuration, "
                + "leave blank to use main: "
            )
            if config_part == "":
                config_part = "main"
            if config_part not in list_conf:
                self.stdout.write(self.style.ERROR("Configuration not available!"))
                return

        setting = self.get_setting(options, config_part)

        pod_version_init = input(
            "Pod initial version (leave blank to put current version: %s): " % VERSION
        )
        if pod_version_init == "":
            pod_version_init = VERSION

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
            "pod_version_end": pod_version_end,
            "default_value": default_value,
            "description": {"en": description_en, "fr": description_fr},
        }
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

        self.save_setting(options, config_part, setting)

        self.stdout.write(self.style.SUCCESS("End!"))
