from django.core.management.base import BaseCommand, CommandError
from typing import List
import urllib.request
import json
import os

__CONFIGURATION_POD_URL__ = "https://raw.githubusercontent.com/EsupPortail/Esup-Pod/__pod_version__/pod/main/configuration.json"


class Command(BaseCommand):
    help = 'Compare configuration from specified version'

    def add_arguments(self, parser):
        parser.add_argument('pod_version', type=str)

    def handle(self, *args, **options):
        configuration_url = __CONFIGURATION_POD_URL__.replace(
            '__pod_version__',
            options['pod_version']
        )
        url_configuration = []
        try:
            response = urllib.request.urlopen(configuration_url)
            configuration_url_data = json.loads(response.read().decode())
            url_configuration = self.get_all_settings(configuration_url_data)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                raise CommandError(
                    'The configuration file for %s was not found' % options['pod_version']
                )
            raise CommandError(f'A HTTPError was thrown: {err.code} {err.reason}')
        local_configuration = []
        with open(os.path.join("pod", "main", "configuration.json"), "r") as json_file:
            configuration_local_data = json.load(json_file)
            local_configuration = self.get_all_settings(configuration_local_data)
        local_missing = self.get_local_missing(url_configuration, local_configuration)
        url_missing = self.get_url_missing(url_configuration, local_configuration)

        self.print_log(
            "New configuration from %s not in local" % options['pod_version'],
            local_missing
        )
        self.print_log(
            "Configuration found in local file but missing in %s version of pod" % options['pod_version'],
            url_missing
        )

        self.stdout.write(self.style.SUCCESS('End compare configuration'))

    def print_log(self, title: str, data: List[str]) -> None:
        print(20 * "-")
        print(f"{title} :")
        print("\n    - " + "\n    - ".join(data))

    def get_local_missing(self, url_configuration, local_configuration):
        local_missing = []
        for key in url_configuration:
            if key not in local_configuration:
                local_missing.append(key)
        return local_missing

    def get_url_missing(self, url_configuration, local_configuration):
        url_missing = []
        for key in local_configuration:
            if key not in url_configuration:
                url_missing.append(key)
        return url_missing

    def get_all_settings(self, data):
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
