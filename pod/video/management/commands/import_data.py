from django.utils import translation
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from django.apps import apps
try:
    from pod.authentication.models import Owner
except ImportError:
    pass
    # from django.contrib.auth.models import User as Owner

AUTHENTICATION = True if apps.is_installed('pod.authentication') else False

import os

BASE_DIR = getattr(
    settings, 'BASE_DIR', '/home/pod/django_projects/podv2/pod')


class Command(BaseCommand):
    args = 'Channel Theme Type User Discipline'
    help = 'Import from V1'
    valid_args = ['Channel', 'Theme', 'Type', 'User', 'Discipline', 'FlatPage',
                  'UserProfile', 'Pod']

    def add_arguments(self, parser):
        parser.add_argument('import')

    def handle(self, *args, **options):
        # Activate a fixed locale fr
        translation.activate('fr')
        if options['import'] and options['import'] in self.valid_args:
            type_to_import = options['import']
            filepath = os.path.join(BASE_DIR, '../../import/',
                                    type_to_import + ".json")
            print(type_to_import, filepath)
            self.migrate_to_v2(filepath, type_to_import)
            with open(filepath, "r") as infile:
                data = serializers.deserialize("json", infile)
                for obj in data:
                    if AUTHENTICATION and type_to_import == 'UserProfile':
                        owner = Owner.objects.get(user_id=obj.object.user_id)
                        owner.auth_type = obj.object.auth_type
                        owner.affiliation = obj.object.affiliation
                        owner.commentaire = obj.object.commentaire
                        # todo image
                        owner.save()
                    else:
                        obj.save()
        else:
            print(
                "******* Warning: you must give some arguments: %s *******"
                % self.valid_args)

    def migrate_to_v2(self, filepath, type_to_import):
        f = open(filepath, 'r')
        filedata = f.read()
        f.close()
        newdata = self.get_new_data(type_to_import, filedata)
        f = open(filepath, 'w')
        f.write(newdata)
        f.close()

    def get_new_data(self, type_to_import, filedata):
        newdata = ""
        if type_to_import in ('Channel', 'Theme', 'Type', 'Discipline'):
            newdata = filedata.replace(
                "pods." + type_to_import.lower(),
                "video." + type_to_import.lower()
            )
        if type_to_import in ('Type', 'Discipline'):
            newdata = newdata.replace("headband", "icon")
        if type_to_import in ('User', 'FlatPage'):
            newdata = filedata
        if type_to_import == 'UserProfile':
            newdata = filedata.replace(
                "core.userprofile", "authentication.owner"
            ).replace("\"image\":", "\"userpicture\":")
        if type_to_import == 'Pod':
            newdata = filedata.replace(
                "pods.Pod",
                "video.Video"
            )
        return newdata


"""
SAVE FROM PODV1

from pods.models import Channel
from pods.models import Theme
from pods.models import Type
from pods.models import User
from pods.models import Discipline
from pods.models import Pod
from django.contrib.flatpages.models import FlatPage

from django.core import serializers
jsonserializer = serializers.get_serializer("json")
json_serializer = jsonserializer()

with open("Channel.json", "w") as out:
    json_serializer.serialize(Channel.objects.all(), stream=out)

with open("Theme.json", "w") as out:
    json_serializer.serialize(Theme.objects.all(), stream=out)

with open("Type.json", "w") as out:
    json_serializer.serialize(Type.objects.all(), stream=out)

with open("User.json", "w") as out:
    json_serializer.serialize(User.objects.all(), stream=out)

with open("Discipline.json", "w") as out:
    json_serializer.serialize(Discipline.objects.all(), stream=out)

with open("FlatPage.json", "w") as out:
    json_serializer.serialize(FlatPage.objects.all(), stream=out)

from core.models import UserProfile
with open("UserProfile.json", "w") as out:
    json_serializer.serialize(UserProfile.objects.all(), stream=out, fields=(\
        'user','auth_type', 'affiliation', 'commentaire', 'image'))

video_fields = ('video', 'allow_donwloading', 'is_360', 'title', 'slug', 
    'owner', 'date_added', 'date_evt', 'cursus', 'main_lang', 'description', 
    'duration', 'type', 'tags', 'discipline', 'channel', 'theme', 'is_draft',
    'is_restricted', 'password')
with open("Pod.json", "w") as out:
    json_serializer.serialize(
        Pod.objects.all(), stream=out, fields=video_fields)

"""
