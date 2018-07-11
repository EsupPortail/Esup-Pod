from django.utils import translation
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from django.apps import apps
from pod.video.models import Video
try:
    from pod.authentication.models import Owner
except ImportError:
    pass
    # from django.contrib.auth.models import User as Owner
import os
import json

AUTHENTICATION = True if apps.is_installed('pod.authentication') else False

BASE_DIR = getattr(
    settings, 'BASE_DIR', '/home/pod/django_projects/podv2/pod')


class Command(BaseCommand):
    args = 'Channel Theme Type User Discipline'
    help = 'Import from V1'
    valid_args = ['Channel', 'Theme', 'Type', 'User', 'Discipline', 'FlatPage',
                  'UserProfile', 'Pod', 'tags']

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
                if type_to_import in ('Channel', 'Theme', 'Type', 'User',
                                      'Discipline', 'FlatPage', 'UserProfile',
                                      'Pod'):
                    data = serializers.deserialize("json", infile)
                    for obj in data:
                        if AUTHENTICATION and type_to_import == 'UserProfile':
                            owner = Owner.objects.get(
                                user_id=obj.object.user_id)
                            owner.auth_type = obj.object.auth_type
                            owner.affiliation = obj.object.affiliation
                            owner.commentaire = obj.object.commentaire
                            # todo image
                            owner.save()
                        else:
                            print(obj, obj.object.id)
                            obj.object.headband = None
                            obj.save()
                if type_to_import in ('tags'):
                    data = json.load(infile)
                    for obj in data:
                        self.add_tag_to_video(obj, data[obj])
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
        if type_to_import in ('User', 'FlatPage', 'tags'):
            newdata = filedata
        if type_to_import == 'UserProfile':
            newdata = filedata.replace(
                "core.userprofile", "authentication.owner"
            ).replace("\"image\":", "\"userpicture\":")
        if type_to_import == 'Pod':
            newdata = filedata.replace(
                "pods.pod",
                "video.video"
            )
        return newdata

    def add_tag_to_video(self, video_id, list_tag):
        video = Video.objects.get(id=video_id)
        video.tags = ', '.join(list_tag)
        video.save()


"""
SAVE FROM PODV1

from pods.models import Channel
from pods.models import Theme
from pods.models import Type
from pods.models import User
from pods.models import Discipline
from pods.models import Pod
from core.models import UserProfile
from django.contrib.auth.models import User
from django.contrib.flatpages.models import FlatPage

from django.core import serializers
jsonserializer = serializers.get_serializer("json")
json_serializer = jsonserializer()

with open("Channel.json", "w") as out:
    json_serializer.serialize(Channel.objects.all(), indent=2, stream=out)

with open("Theme.json", "w") as out:
    json_serializer.serialize(Theme.objects.all(), indent=2, stream=out)

with open("Type.json", "w") as out:
    json_serializer.serialize(Type.objects.all(), indent=2, stream=out)

>>> owners = set(Channel.objects.all().values_list("owners", flat=True))
>>> users = set(Channel.objects.all().values_list("users", flat=True))
>>> list_user = owners.union(users)

with open("User.json", "w") as out:
    json_serializer.serialize(User.objects.filter(id__in=list_user), indent=2,
        stream=out)

with open("Discipline.json", "w") as out:
    json_serializer.serialize(Discipline.objects.all(), indent=2, stream=out)

with open("FlatPage.json", "w") as out:
    json_serializer.serialize(FlatPage.objects.all(), indent=2, stream=out)

with open("UserProfile.json", "w") as out:
    json_serializer.serialize(UserProfile.objects.all(), indent=2,
        stream=out, fields=(
        'user','auth_type', 'affiliation', 'commentaire', 'image'))

podowner = set(Pod.objects.all().values_list("owner", flat=True))
with open("User.json", "w") as out:
     json_serializer.serialize(User.objects.filter(id__in=podowner), indent=2,
      stream=out)

video_fields = ('video', 'allow_donwloading', 'is_360', 'title', 'slug',
    'owner', 'date_added', 'date_evt', 'cursus', 'main_lang', 'description',
    'duration', 'type', 'discipline', 'channel', 'theme', 'is_draft',
    'is_restricted', 'password')
with open("Pod.json", "w") as out:
    json_serializer.serialize(
        Pod.objects.all().order_by("id"), stream=out, indent=2,
        fields=video_fields)

list_tag = {}
for p in Pod.objects.all():
   list_tag["%s" %p.id] = []
   for t in p.tags.all():
     list_tag["%s" %p.id].append(t.name)
with open("tags.json", "w") as out:
     out.write(json.dumps(list_tag, indent=2))

# todo
'chapter',
'completion',

"""
