from django.core.management.base import BaseCommand
from django.conf import settings

import json
import os


class Command(BaseCommand):
    help = "Compare settings in code vs configuration.json"

    IGNORED_PREFIXES = (
        "DJANGO",
        "DATABASES",
        "TEMPLATES",
        "INSTALLED_APPS",
        "MIDDLEWARE",
        "AUTH_",
        "CORS_",
        "CSRF_",
        "LOGGING",
        "MESSAGE_",
        "SECURE_",
        "SESSION_",
        "STATIC",
        "TEST",
        "WSGI",
        "ADMIN",
        "DEFAULT",
        "EMAIL",
        "SERVER_EMAIL",
        "FILE_UPLOAD",
        "INTERNAL_IPS",
        "LANGUAGES",
        "LOCALE",
        "MANAGERS",
        "MEDIA",
        "MIGRATION",
        "ROOT_URLCONF",
        "SECRET_KEY",
        "SIGNING_KEY",
        "SILENCED_SYSTEM_CHECKS",
        "SITE_ID",
        "TIME_ZONE",
        "USE_I18N",
        "USE_L10N",
        "USE_TZ",
        "X_FRAME_OPTIONS",
        "ABSOLUTE_URL",
        "ALLOWED_HOSTS",
        "APPEND_SLASH",
        "ASGI",
        "BASE_DIR",
        "CACHES",
        "DEBUG",
        "LOGIN",
        "LOGOUT",
        "PASSWORD",
        "REST_FRAMEWORK",
        "SIMPLE_JWT",
    )

    def handle(self, *args, **options):
        all_live_settings = dir(settings)
        local_settings_list = [
            item
            for item in all_live_settings
            if (
                not item.startswith("__")
                and item.isupper()
                and not item.startswith(self.IGNORED_PREFIXES)
            )
        ]
        local_settings_list.sort()
        self.print_log("Active Django Settings (Filtered)", local_settings_list)
        conf_path = os.path.join(
            settings.BASE_DIR, "src", "apps", "core", "configuration.json"
        )
        if not os.path.exists(conf_path):
            self.stdout.write(self.style.ERROR(f"File not found: {conf_path}"))
            return
        with open(conf_path, "r") as json_file:
            data = json.load(json_file)
        json_settings = []
        if "configuration_pod" in data[0]:
            pod_settings = data[0]["configuration_pod"].get("description", {})
            for keys in pod_settings.keys():
                settings_keys = list(pod_settings[keys]["settings"].keys())
                json_settings.extend(settings_keys)
        if "configuration_apps" in data[0]:
            app_settings = data[0]["configuration_apps"].get("description", {})
            for keys in app_settings.keys():
                settings_keys = list(app_settings[keys]["settings"].keys())
                json_settings.extend(settings_keys)
        new_settings = list(set(local_settings_list) - set(json_settings))
        new_settings.sort()
        self.print_log(
            "Settings in Code but MISSING in configuration.json", new_settings
        )

    def print_log(self, title: str, data: list[str]) -> None:
        print(20 * "-")
        print(f"{title}:")
        if not data:
            print("\n    (None)")
        else:
            print("\n    - " + "\n    - ".join(data[:20]))
            if len(data) > 20:
                print(f"    ... and {len(data) - 20} more.")
