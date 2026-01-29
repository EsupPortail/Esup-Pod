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
        output += "# %s\n\n" % self.data[0]["header"][self.language]
        output += self.get_information()
        output += self.get_configuration("pod")
        output += self.get_configuration("apps")
        output_dir = os.path.join(settings.BASE_DIR, "docs")
        md_filename = os.path.join(
            output_dir, f"CONFIGURATION_{self.language.upper()}.md"
        )
        open(md_filename, "w").close()
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(output)
        self.stdout.write(self.style.SUCCESS("Successfully export configuration"))

    def get_information(self) -> str:
        """Get information section from configuration.json."""
        msg = "## %s\n" % self.data[0]["information"]["title"][self.language]
        for line in self.data[0]["information"]["description"][self.language]:
            if line != "":
                msg += "%s<br>\n" % line
            else:
                msg += "\n"
        msg += "\n"
        msg += self.get_settings(self.data[0]["information"]["settings"])
        return msg

    def get_configuration(self, app) -> str:
        """Get the "configuration_$app section from configuration.json."""
        msg = "\n## %s\n" % (
            self.data[0]["configuration_%s" % app]["title"][self.language]
        )
        descs = self.data[0]["configuration_%s" % app]["description"]
        for _key, desc in descs.items():
            msg += "\n### %s\n\n" % desc["title"][self.language]
            desc_list = desc["description"].get(self.language, [])
            for line in desc_list:
                if line != "":
                    msg += "%s<br>\n" % line
                else:
                    msg += "\n"
            if desc["description"] and len(desc_list) > 0:
                msg += "\n"
            msg += self.get_settings(desc["settings"])
        msg += self.get_settings(self.data[0]["configuration_%s" % app]["settings"])
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
                    endline = "<br>\n"
                    line = line.strip()
                msg += "  >> %s%s" % (line, endline)
        return msg
