"""Create configuration file."""

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

    def add_arguments(self, parser):
        """Add 'language' argument."""
        parser.add_argument(
            "language",
            type=str,
            help="give the language to export the configuration: fr or en",
        )

    def handle(self, *args, **options):
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
        output += "\n# %s \n" % self.data[0]["header"][self.language]
        output += self.get_information()
        output += self.get_configuration("pod")
        output += self.get_configuration("apps")

        md_filename = os.path.join("./", "CONFIGURATION_%s.md" % self.language.upper())
        open(md_filename, "w").close()  # erase it
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(output)

        self.stdout.write(self.style.SUCCESS("Successfully export configuration"))

    def get_information(self):
        msg = "\n"
        msg += "\n## %s \n" % self.data[0]["information"]["title"][self.language]
        for line in self.data[0]["information"]["description"][self.language]:
            if line != "":
                msg += "\n%s<br>" % line
            else:
                msg += "\n"
        msg += self.get_settings(self.data[0]["information"]["settings"])
        return msg

    def get_configuration(self, app):
        msg = "\n"
        msg += "\n## %s \n" % (
            self.data[0]["configuration_%s" % app]["title"][self.language]
        )
        descs = self.data[0]["configuration_%s" % app]["description"]
        for key, desc in descs.items():
            msg += "\n\n### %s" % desc["title"][self.language]
            for line in desc["description"].get(self.language, []):
                if line != "":
                    msg += "\n%s<br>" % line
                else:
                    msg += "\n"
            msg += self.get_settings(desc["settings"])

        msg += self.get_settings(self.data[0]["configuration_%s" % app]["settings"])
        return msg

    def get_settings(self, settings):
        """Format settings into md."""
        msg = ""
        for key, value in settings.items():
            msg += "\n\n - `%s`" % key
            # Ensure that multi line code will properly be displayed
            if str(value["default_value"]).startswith("```"):
                formatted = value["default_value"].replace("\n", "\n  ")
                value["default_value"] = "\n\n  %s" % formatted
            else:
                value["default_value"] = " `%s`" % value["default_value"]
            msg += "\n\n  > %s%s\n" % (_("default value:"), value["default_value"])
            code = False
            for line in value["description"][self.language]:
                if line.startswith("`"):
                    msg += "\n  >>\n  >> %s" % line
                    code = not code
                    continue
                endline = "" if code else "<br>"
                if line != "":
                    msg += "\n  >> %s %s" % (line, endline)
                else:
                    msg += "\n"
        return msg
