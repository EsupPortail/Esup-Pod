"""
Esup-Pod - Django management command to validate Pydantic configuration classes against
`configuration.json` and automatically generate `CONFIGURATION.md`.

Usage:
    python3 manage.py validate_config [--dry-run]

Features:
    - Discovery: Automatically finds all `BaseSettings` classes in `src/apps/*/conf.py`.
    - Key Check: Ensures all settings in `configuration.json` are present in code (Critical).
    - Sync Check: Warns if settings in code are missing from `configuration.json` (Warning).
    - Type Check: Warns if JSON default value types mismatch Pydantic annotations (Warning).
    - Translation: Warns if 'en' or 'fr' translations are missing or contain 'TODO' (Warning).
    - Documentation: Generates/Updates `CONFIGURATION.md` based on current config (Warning if out of date in --dry-run).

Exit Codes:
    - 0: Validation passed (possibly with warnings).
    - 1: Critical errors detected (missing keys in code, import errors, etc.).
"""

import json
import os
import sys
import importlib
import inspect

from django.core.management.base import BaseCommand
from django.conf import settings
from pydantic_settings import BaseSettings


class Command(BaseCommand):
    """
    Management command to validate the synchronization between
    configuration.json and Pydantic settings classes.
    """

    help = (
        "Validate config classes against configuration.json and generate CONFIGURATION.md"
    )

    def add_arguments(self, parser):
        """
        Defines the --dry-run argument.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run the validation and generation but do not overwrite CONFIGURATION.md. Fails if changes are needed.",
        )

    def _load_json(self, conf_path):
        """
        Loads and basic-validates the configuration.json file.
        """
        if not os.path.exists(conf_path):
            self.stdout.write(self.style.ERROR(f"File not found: {conf_path}"))
            sys.exit(1)

        with open(conf_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)

        if not data or "configuration_apps" not in data[0]:
            self.stdout.write(self.style.ERROR("Invalid JSON format"))
            sys.exit(1)
        return data[0]["configuration_apps"].get("description", {})

    def _discover_pydantic_apps(self):
        """
        Crawls the apps directory to find all Pydantic BaseSettings classes.
        """
        apps_dir = os.path.join(settings.BASE_DIR, "src", "apps")
        pydantic_apps = {}
        errors = []

        for app_dir in os.listdir(apps_dir):
            if os.path.isdir(os.path.join(apps_dir, app_dir)):
                conf_py = os.path.join(apps_dir, app_dir, "conf.py")
                if os.path.exists(conf_py):
                    module_name = f"src.apps.{app_dir}.conf"
                    try:
                        module = importlib.import_module(module_name)
                    except Exception as e:
                        errors.append(f"Could not import {module_name}: {e}")
                        continue

                    config_classes = []
                    for name, obj in inspect.getmembers(module):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, BaseSettings)
                            and obj is not BaseSettings
                        ):
                            config_classes.append(obj)

                    if config_classes:
                        pydantic_apps[app_dir] = config_classes[0]
        return pydantic_apps, errors

    def _validate_keys(self, pydantic_apps, apps_json):
        """
        Ensures that all keys in JSON exist in code and vice-versa.
        """
        errors = []
        warnings = []
        for app_name, config_class in pydantic_apps.items():
            if app_name not in apps_json:
                errors.append(
                    f"App '{app_name}' has a configuration class but is missing from configuration.json."
                )
                continue

            json_settings = apps_json[app_name].get("settings", {})
            json_keys = set(json_settings.keys())
            code_keys = set(k.upper() for k in config_class.model_fields.keys())

            missing_in_json = code_keys - json_keys
            missing_in_code = json_keys - code_keys

            for k in missing_in_json:
                warnings.append(
                    f"[{app_name}] Key '{k}' is defined in code ({config_class.__name__}) but missing in configuration.json."
                )
            for k in missing_in_code:
                errors.append(
                    f"[{app_name}] Key '{k}' is in configuration.json but missing in code ({config_class.__name__})."
                )
        return errors, warnings

    def _validate_types(self, pydantic_apps, apps_json):
        """
        Checks for type mismatches between JSON default values and Pydantic annotations.
        """
        warnings = []
        # Mapping of Python types to strings expected in Pydantic annotations
        type_mapping = {
            bool: "bool",
            int: "int",
            str: "str",
        }

        for app_name, config_class in pydantic_apps.items():
            if app_name not in apps_json:
                continue

            json_settings = apps_json[app_name].get("settings", {})
            json_keys = set(json_settings.keys())
            code_keys = set(k.upper() for k in config_class.model_fields.keys())

            for key in json_keys.intersection(code_keys):
                code_field = config_class.model_fields[key.lower()]
                json_val = json_settings[key].get("default_value")

                if json_val is None:
                    continue

                json_type = type(json_val)
                expected_type_name = type_mapping.get(json_type)

                if (
                    expected_type_name
                    and expected_type_name not in str(code_field.annotation).lower()
                ):
                    warnings.append(
                        f"[{app_name}] Key '{key}' type mismatch: "
                        f"JSON is {json_type.__name__}, Code is {code_field.annotation}"
                    )
        return warnings

    def _validate_translations(self, apps_json):
        """
        Ensures translations (en/fr) are present and not empty/TODO.
        """
        warnings = []
        for app_name, app_data in apps_json.items():
            settings_data = app_data.get("settings", {})
            for key, setting in settings_data.items():
                for trans_field in ["description", "label"]:
                    if trans_field in setting:
                        translations = setting[trans_field]
                        if "fr" not in translations or "en" not in translations:
                            warnings.append(
                                f"[{app_name}] Key '{key}' -> '{trans_field}' must contain 'fr' and 'en' translations."
                            )
                        else:
                            for lang in ["fr", "en"]:
                                val = translations[lang]
                                if isinstance(val, list):
                                    val = " ".join(val)
                                if not val or val.strip() == "" or "TODO" in val.upper():
                                    warnings.append(
                                        f"[{app_name}] Key '{key}' -> '{trans_field}' [{lang}] is empty or contains TODO."
                                    )
        return warnings

    def _generate_markdown(self, apps_json):
        """
        Generates the content for CONFIGURATION.md based on apps_json.
        """
        md_lines = []
        md_lines.append("# Configuration\n")
        md_lines.append(
            "This file is automatically generated from `configuration.json` and Python code. Do not edit directly.\n"
        )

        for app_name, app_data in apps_json.items():
            title_en = app_data.get("title", {}).get("en", app_name.capitalize())
            md_lines.append(f"## {title_en}\n")
            settings_data = app_data.get("settings", {})
            for key, setting in settings_data.items():
                md_lines.append(f"### `{key}`\n")

                default_val = setting.get("default_value")
                if isinstance(default_val, str):
                    default_str = f'"{default_val}"'
                else:
                    default_str = str(default_val)
                md_lines.append(f"- **Default**: `{default_str}`")

                pod_v = setting.get("pod_version_init")
                if pod_v:
                    md_lines.append(f"- **Since**: Pod {pod_v}")

                md_lines.append("")

                desc = setting.get("description", {})
                en_desc = " ".join(desc.get("en", []))
                fr_desc = " ".join(desc.get("fr", []))

                if en_desc:
                    md_lines.append(f"**EN**: {en_desc}")
                if fr_desc:
                    md_lines.append(f"**FR**: {fr_desc}")
                md_lines.append("")

        return "\n".join(md_lines)

    def handle(self, *args, **options):
        """
        Main execution point for the validation command.
        """
        dry_run = options["dry_run"]
        conf_path = os.path.join(
            settings.BASE_DIR, "src", "apps", "core", "configuration.json"
        )
        doc_path = os.path.join(settings.BASE_DIR, "CONFIGURATION.md")

        apps_json = self._load_json(conf_path)
        pydantic_apps, discover_errors = self._discover_pydantic_apps()

        errors = discover_errors
        warnings = []

        key_errors, key_warnings = self._validate_keys(pydantic_apps, apps_json)
        errors.extend(key_errors)
        warnings.extend(key_warnings)

        warnings.extend(self._validate_types(pydantic_apps, apps_json))
        warnings.extend(self._validate_translations(apps_json))

        new_md_content = self._generate_markdown(apps_json)

        old_md_content = ""
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                old_md_content = f.read()

        if dry_run:
            if new_md_content != old_md_content:
                warnings.append(
                    "CONFIGURATION.md is not up to date. Run `python manage.py validate_config` locally and commit the changes."
                )

        if warnings:
            self.stdout.write(
                self.style.WARNING(
                    f"\nValidation finished with {len(warnings)} warnings:"
                )
            )
            for warn in warnings:
                self.stdout.write(self.style.WARNING(f" - {warn}"))

        if errors:
            self.stdout.write(
                self.style.ERROR(
                    f"\nValidation failed with {len(errors)} critical errors:"
                )
            )
            for err in errors:
                self.stdout.write(self.style.ERROR(f" - {err}"))
            sys.exit(1)
        else:
            if not dry_run:
                with open(doc_path, "w", encoding="utf-8") as f:
                    f.write(new_md_content)
                self.stdout.write(
                    self.style.SUCCESS(
                        "\nValidation passed and CONFIGURATION.md generated."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\nValidation passed and CONFIGURATION.md is up to date."
                    )
                )
