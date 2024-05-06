"""Esup-Pod configuration file generator.

Launch with `python3 manage.py createconfiguration $lang`
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import translation
from django.utils.translation import gettext as _
import json
import os


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
        filename = os.path.join("pod", "main", "configuration.json")
        with open(filename, "r", encoding="utf-8") as json_file:
            self.data = json.load(json_file)
        # header, information, configuration_pod, configuration_apps
        output = ""
        output += "# %s\n\n" % self.data[0]["header"][self.language]
        output += self.get_information()
        output += self.get_configuration("pod")
        output += self.get_configuration("apps")

        md_filename = os.path.join("./", "CONFIGURATION_%s.md" % self.language.upper())
        open(md_filename, "w").close()  # erase it
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
        for key, value in settings.items():
            msg += "* `%s`\n" % key
            # Ensure that multi line code will properly be displayed
            if str(value["default_value"]).startswith("```"):
                formatted = value["default_value"].replace("\n", "\n  ")
                value["default_value"] = "\n\n  %s\n" % formatted
            else:
                value["default_value"] = " `%s`" % value["default_value"]
            msg += "  > %s%s\n" % (_("default value:"), value["default_value"])
            msg += self.get_description(value["description"][self.language])

        return msg

    def get_description(self, description: list) -> str:
        """Get a setting description in MD format."""
        msg = ""
        code = False
        for line in description:
            if line == "":
                msg += "  >>\n"
            else:
                if line.startswith("```"):
                    code = not code
                    if code:
                        # Add a blank line before each code block
                        msg += "  >>\n  >> %s\n" % line
                    else:
                        # Add a blank line after each code block
                        msg += "  >> %s\n  >>\n" % line
                    continue

                if code:
                    endline = "\n"
                else:
                    endline = "<br>\n"
                    # Auto remove surrounding spaces.
                    line = line.strip()

                msg += "  >> %s%s" % (line, endline)
        return msg
