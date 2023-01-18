from django.core.management.base import BaseCommand, CommandError
import json
import os


class Command(BaseCommand):
    help = "Export configuration to markdown"
    language = "fr"
    data = []

    def add_arguments(self, parser):
        parser.add_argument(
            "language",
            type=str,
            help="give the language to export the configuration : fr or en",
        )

    def handle(self, *args, **options):
        self.language = options["language"]
        if self.language not in ["fr", "en"]:
            raise CommandError("Langage must be fr or en")
        filename = os.path.join("pod", "custom", "configuration.json")
        with open(filename, "r", encoding="utf-8") as json_file:
            self.data = json.load(json_file)
        # header, information, configuration_pod, configuration_apps
        output = ""
        output += "# %s \n" % self.data[0]["header"][self.language]
        output += self.get_information()
        output += self.get_configuration("pod")
        output += self.get_configuration("apps")

        md_filename = os.path.join("pod", "custom", "configuration_%s.md" % self.language)
        open(md_filename, "w").close()  # erase it
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(output)

        self.stdout.write(self.style.SUCCESS("Successfully export configuration"))

    def get_information(self):
        msg = "\n"
        msg += "## %s \n" % self.data[0]["information"]["title"][self.language]
        for line in self.data[0]["information"]["description"][self.language]:
            if line != "":
                msg += "\n%s <br/>" % line
            else:
                msg += "\n"
        msg += self.get_settings(self.data[0]["information"]["settings"])
        return msg

    def get_configuration(self, app):
        msg = "\n"
        msg += "## %s \n" % self.data[0]["configuration_%s" % app]["title"][self.language]
        descs = self.data[0]["configuration_%s" % app]["description"]
        for key, desc in descs.items():
            msg += "\n### %s \n" % desc["title"][self.language]
            for line in desc["description"].get(self.language, []):
                if line != "":
                    msg += "\n%s <br/>" % line
                else:
                    msg += "\n"
            msg += self.get_settings(desc["settings"])

        msg += self.get_settings(self.data[0]["configuration_%s" % app]["settings"])
        return msg

    def get_settings(self, settings):
        msg = "\n"
        for key, value in settings.items():
            msg += "\n\n - %s " % key
            msg += "\n> default value : %s <br>" % value["default_value"]
            code = False
            for line in value["description"][self.language]:
                if line.startswith("`"):
                    msg += "\n>> %s" % line
                    code = not code
                    continue
                endline = "" if code else "<br>"
                if line != "":
                    msg += "\n>> %s %s" % (line, endline)
                else:
                    msg += "\n"
        return msg
