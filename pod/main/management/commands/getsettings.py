from typing import List
from django.core.management.base import BaseCommand
import re
import os
import fnmatch
import importlib


class Command(BaseCommand):
    help = 'Get all settings for the specified app and compare it to configuration file'

    def add_arguments(self, parser):
        parser.add_argument('app_name', type=str)

    def handle(self, *args, **options):
        files_names = fnmatch.filter(os.listdir("pod/" + options["app_name"]), '*.py')
        global_settings_list = []
        for f in files_names:
            print(" - %s" % f)
            mod = importlib.import_module(
                '.'.join(['pod', options["app_name"], f.replace(".py", "")])
            )
            items = dir(mod)
            settings_list = [item for item in items if item.isupper() and len(item) > 1]
            global_settings_list += settings_list
        global_settings_list = list(dict.fromkeys(global_settings_list))
        global_settings_list.sort()
        self.print_log(options["app_name"], global_settings_list)
        mk_settings = []
        with open(os.path.join("pod", "custom", "ConfigurationPod.md"), "r") as  mk_file:
            for line in mk_file:
                match = re.search(r'- (?P<set>\w+) (=|:)?.*', line)
                if match:
                    settings = match.group('set')
                    if settings.isupper() and settings not in mk_settings:
                        mk_settings.append(settings)
        mk_settings.sort()
        self.print_log("Configuration setting", mk_settings)
        new_settings = list(set(global_settings_list) - set(mk_settings))
        new_settings.sort()
        self.print_log("New settings", new_settings)
        # raise CommandError('Poll "%s" does not exist' % poll_id)
        # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))

    def print_log(self, title: str, data: List[str]) -> None:
        print(20 * "-")
        print(f"{title} :")
        print("\n    - " + "\n    - ".join(data))
        # print(20 * "-")