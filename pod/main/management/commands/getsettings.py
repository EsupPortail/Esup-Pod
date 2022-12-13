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
            data = dir(mod)
            settings_list = []
            for d in data:
                if d.isupper() and len(d) > 1:
                    settings_list.append(d)
            global_settings_list += settings_list
        global_settings_list = list(dict.fromkeys(global_settings_list))
        global_settings_list.sort()
        print(20 * "-")
        print(options["app_name"] + " :")
        print("\n    - " + "\n    - ".join(global_settings_list))
        print(20 * "-")
        mk_file = open(os.path.join("pod", "custom", "ConfigurationPod.md"), "r")
        mk_settings = []
        for line in mk_file:
            match = re.search(r'- (?P<set>\w+) (=|:)?.*', line)
            if match:
                settings = match.group('set')
                if settings not in mk_settings:
                    mk_settings.append(settings)
        mk_settings.sort()
        print("Configuration settings :")
        print("\n    - " + "\n    - ".join(mk_settings))
        new_settings = list(set(global_settings_list) - set(mk_settings))
        new_settings.sort()
        print(20 * "-")
        print("New settings :")
        print("\n    - " + "\n    - ".join(new_settings))
        print(20 * "-")
        # raise CommandError('Poll "%s" does not exist' % poll_id)
        # self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
