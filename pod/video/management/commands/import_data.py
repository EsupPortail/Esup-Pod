from django.utils import translation
from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
import json


class Command(BaseCommand):
    args = 'Channel Theme Type User Discipline'
    help = 'Import from V1'

    def add_arguments(self, parser):
        parser.add_argument('type_to_import')

    def handle(self, *args, **options):
        # Activate a fixed locale fr
        translation.activate('fr')
        if options['type_to_import'] and \
            options['type_to_import'] in \
            ['Channel', 'Theme', 'Type', 'User', 'Discipline', 'FlatPage']:
            type_to_import = options['type_to_import']
            filepath = "/home/pod/django_projects/import/" + \
                type_to_import + ".json"
            f = open(filepath, 'r')
            filedata = f.read()
            f.close()
            newdata = ""
            if type_to_import == 'Channel':
                newdata = filedata.replace("pods.channel", "video.channel")
            if type_to_import == 'Theme':
                newdata = filedata.replace("pods.theme", "video.theme")
            if type_to_import == 'Type':
                newdata = filedata.replace("pods.type", "video.type")
                newdata = newdata.replace("headband", "icon")
            if type_to_import == 'User':
                newdata = filedata.replace("", "")
            if type_to_import == 'FlatPage':
                newdata = filedata.replace("", "")
            if type_to_import == 'Discipline':
                newdata = filedata.replace(
                    "pods.discipline", "video.discipline")
                newdata = newdata.replace("headband", "icon")
            f = open(filepath, 'w')
            f.write(newdata)
            f.close()

            with open(filepath, "r") as infile:
                data = serializers.deserialize("json", infile)
                for obj in data:
                    obj.save()
        else:
            print(
                "******* Warning: you must give some arguments: %s *******" % self.args)

"""
SAVE FROM PODV1

from pods.models import Channel
from pods.models import Theme
from pods.models import Type
from pods.models import User
from pods.models import Discipline
from django.core import serializers

jsonserializer = serializers.get_serializer("json")
json_serailizer = jsonserializer()

with open("Channel.json", "w") as out:
    json_serailizer.serialize(Channel.objects.all(), stream=out)

with open("Theme.json", "w") as out:
    json_serailizer.serialize(Theme.objects.all(), stream=out)

with open("Type.json", "w") as out:
    json_serailizer.serialize(Type.objects.all(), stream=out)

with open("User.json", "w") as out:
    json_serailizer.serialize(User.objects.all(), stream=out)

with open("Discipline.json", "w") as out:
    json_serailizer.serialize(Discipline.objects.all(), stream=out)

"""
