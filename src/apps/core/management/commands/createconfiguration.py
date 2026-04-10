"""Esup-Pod configuration file generator.

Launch with `python3 manage.py createconfiguration $lang`
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import translation
from django.utils.translation import gettext as _
import json
import os

from django.conf import settings


class Command(BaseCommand):
    """Export configuration.json to markdown."""

    help = "Export configuration to markdown"
    language = "fr"
    data = []

    def add_arguments(self, parser) -> None:
        """Add 'language' argument."""
        parser.add_argument(
            "language",
            type=str,
            help="give the language to export the configuration: fr or en",
        )

    def handle(self, *args, **options) -> None:
        """Handle the createconfiguration command call."""
        self.language = options["language"].lower()
        if self.language not in ["fr", "en"]:
            raise CommandError("Langage must be fr or en")
        translation.activate(self.language)
        filename = os.path.join(
            settings.BASE_DIR, "src", "apps", "core", "configuration.json"
        )
        with open(filename, "r", encoding="utf-8") as json_file:
            self.data = json.load(json_file)

        output = ""
        output += self.get_configuration("apps")

        output_dir = os.path.join(settings.BASE_DIR, "docs")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        md_filename = os.path.join(
            output_dir, f"CONFIGURATION_{self.language.upper()}.md"
        )

        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(output)
        self.stdout.write(self.style.SUCCESS("Successfully export configuration"))

    def get_configuration(self, app) -> str:
        """Get the "configuration_$app" section from configuration.json."""
        config_key = "configuration_%s" % app
        if config_key not in self.data[0]:
            return ""

        root_config = self.data[0][config_key]

        # Title of main section
        msg = "# %s\n" % (
            root_config.get("title", {}).get(self.language, "Configuration")
        )

        descs = root_config.get("description", {})

        # Iterate over subsections (apps: authentication, core, etc.)
        for _key, desc in descs.items():
            msg += "\n## %s\n\n" % desc.get("title", {}).get(
                self.language, _key.capitalize()
            )

            desc_list = desc.get("description", {}).get(self.language, [])
            for line in desc_list:
                if line != "":
                    msg += "%s\n" % line
                else:
                    msg += "\n"

            if desc_list and len(desc_list) > 0:
                msg += "\n"

            msg += self.get_settings(desc.get("settings", {}))

        # Top level settings if any
        msg += self.get_settings(root_config.get("settings", {}))
        return msg

    def get_settings(self, settings) -> str:
        """Format settings into md."""
        msg = ""
        for key in sorted(settings.keys()):
            value = settings[key]
            msg += "* `%s`\n" % key
            raw_val = value.get("default_value", value.get("default", "None"))
            if str(raw_val).startswith("```"):
                formatted = str(raw_val).replace("\n", "\n  ")
                display_val = "\n\n  %s\n" % formatted
            else:
                display_val = " `%s`" % raw_val
            msg += "  > %s%s\n" % (_("default value:"), display_val)
            if "description" in value and self.language in value["description"]:
                msg += self.get_description(value["description"][self.language])
            else:
                msg += "  >> No description available.\n"
        return msg

    def get_description(self, description) -> str:
        """Get a setting description in MD format."""
        msg = ""
        code = False
        if isinstance(description, str):
            description = [description]
        for line in description:
            if line == "":
                msg += "  >>\n"
            else:
                if line.startswith("```"):
                    code = not code
                    if code:
                        msg += "  >>\n  >> %s\n" % line
                    else:
                        msg += "  >> %s\n  >>\n" % line
                    continue

                if code:
                    endline = "\n"
                else:
                    endline = "\n"
                    line = line.strip()
                msg += "  >> %s%s" % (line, endline)
        return msg
