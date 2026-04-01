"""
Esup-Pod - Django management command to compare runtime settings defined in code
against those documented in `configuration.json`.

Launch with `python3 manage.py comparesettings`

Returns:
    - ERROR if undocumented settings are detected.
    - WARNING if configuration.json contains extra entries.
    - SUCCESS if configuration is fully documented.
"""

import sys
import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """
    Management command to audit and compare code settings against JSON documentation.
    """

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
        "SPECTACULAR_SETTINGS",
    )

    def handle(self, *args, **options):
        """Executes the comparison logic between runtime settings and configuration.json."""
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
        conf_path = os.path.join(
            settings.BASE_DIR, "src", "apps", "core", "configuration.json"
        )
        if not os.path.exists(conf_path):
            self.stdout.write(self.style.ERROR(f"File not found: {conf_path}"))
            sys.exit(1)

        with open(conf_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        json_settings = []
        if "configuration_apps" in data[0]:
            app_settings = data[0]["configuration_apps"].get("description", {})
            for app in app_settings.values():
                json_settings.extend(app.get("settings", {}).keys())

            # Also check top level settings if any
            json_settings.extend(data[0]["configuration_apps"].get("settings", {}).keys())

        missing_in_json = sorted(list(set(local_settings_list) - set(json_settings)))
        extra_in_json = sorted(list(set(json_settings) - set(local_settings_list)))

        if missing_in_json:
            self.stdout.write(
                self.style.ERROR(
                    f"\nMissing in configuration.json ({len(missing_in_json)}):"
                )
            )
            for s in missing_in_json:
                self.stdout.write(f"   - {s}")
            self.stdout.write(
                self.style.ERROR(
                    "\nSettings audit failed. Please use 'addsetting' command."
                )
            )
            sys.exit(1)
        else:
            if extra_in_json:
                self.stdout.write(
                    self.style.WARNING(f"\nExtra in JSON (not in code): {extra_in_json}")
                )
            self.stdout.write(
                self.style.SUCCESS(
                    "\nAll code settings are documented in configuration.json"
                )
            )
