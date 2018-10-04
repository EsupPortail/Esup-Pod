from django.utils import translation
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from django.apps import apps
from pod.video.models import Video
from pod.completion.models import Document, Track
from pod.enrichment.models import Enrichment
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File

try:
    from pod.authentication.models import Owner
except ImportError:
    pass
    # from django.contrib.auth.models import User as Owner
import os
import json
import wget
import webvtt
import codecs

if getattr(settings, 'USE_PODFILE', False):
    FILEPICKER = True
    from pod.podfile.models import CustomFileModel, CustomImageModel
    from pod.podfile.models import UserFolder
else:
    FILEPICKER = False
    from pod.main.models import CustomFileModel

AUTHENTICATION = True if apps.is_installed('pod.authentication') else False

BASE_DIR = getattr(
    settings, 'BASE_DIR', '/home/pod/django_projects/podv2/pod')

VIDEO_ID_TO_EXCLUDE = getattr(
    settings, 'VIDEO_ID_TO_EXCLUDE', [])

FROM_URL = getattr(settings, 'FROM_URL', "https://pod.univ-lille1.fr/media/")


class Command(BaseCommand):
    args = 'Channel Theme Type User Discipline Pod tags Chapter Contributor...'
    help = 'Import from V1'
    valid_args = ['Channel', 'Theme', 'Type', 'User', 'Discipline', 'FlatPage',
                  'UserProfile', 'Pod', 'tags', 'Chapter', 'Contributor',
                  'Overlay', 'docpods', 'trackpods', 'enrichpods']

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
                                      'Pod', 'Chapter', 'Contributor',
                                      'Overlay'):
                    data = serializers.deserialize("json", infile)
                    for obj in data:
                        self.save_object(type_to_import, obj)
                if type_to_import in (
                        'tags', 'docpods', 'trackpods', 'enrichpods'):
                    data = json.load(infile)
                    for obj in data:
                        if int(obj) not in VIDEO_ID_TO_EXCLUDE:
                            self.add_data_to_video(
                                type_to_import,
                                obj,
                                data[obj])
        else:
            print(
                "******* Warning: you must give some arguments: %s *******"
                % self.valid_args)

    def save_object(self, type_to_import, obj):
        if AUTHENTICATION and type_to_import == 'UserProfile':
            owner = Owner.objects.get(
                user_id=obj.object.user_id)
            owner.auth_type = obj.object.auth_type
            owner.affiliation = obj.object.affiliation
            owner.commentaire = obj.object.commentaire
            # todo image
            owner.save()
        else:
            # print(obj, obj.object.id, obj.object.video.id)
            if (type_to_import == 'Pod'
                    and obj.object.id in VIDEO_ID_TO_EXCLUDE):
                print(obj.object.id, " are exclude")
            else:
                try:
                    if (
                        not hasattr(obj.object, 'video') or
                        (
                            hasattr(obj.object, 'video') and
                            obj.object.video.id not in VIDEO_ID_TO_EXCLUDE
                        )
                    ):
                        obj.object.headband = None
                        obj.save()
                    else:
                        print("video ", obj.object.video.id, " are exclude")
                except ObjectDoesNotExist as e:
                    print("Objects related does not exist %s" % e)

    def migrate_to_v2(self, filepath, type_to_import):
        f = open(filepath, 'r')
        filedata = f.read()
        f.close()
        newdata = self.get_new_data(type_to_import, filedata)
        f = open(filepath, 'w')
        f.write(newdata)
        f.close()

    def Channel(self, filedata):
        return filedata.replace(
            "pods.channel",
            "video.channel"
        )

    def Theme(self, filedata):
        return filedata.replace(
            "pods.theme",
            "video.theme"
        )

    def Type(self, filedata):
        return filedata.replace(
            "pods.type",
            "video.type"
        ).replace("headband", "icon")

    def Discipline(self, filedata):
        return filedata.replace(
            "pods.discipline",
            "video.discipline"
        ).replace("headband", "icon")

    def Pod(self, filedata):
        return filedata.replace(
            "pods.pod",
            "video.video"
        )

    def Chapter(self, filedata):
        return filedata.replace(
            "pods.chapterpods",
            "chapter.chapter"
        ).replace(
            "\"time\"",
            "\"time_start\""
        )

    def Contributor(self, filedata):
        return filedata.replace(
            "pods.contributorpods",
            "completion.contributor"
        )

    def Overlay(self, filedata):
        return filedata.replace(
            "pods.overlaypods",
            "completion.overlay"
        )

    def get_new_data(self, type_to_import, filedata):
        newdata = filedata
        type_import = {
            "Channel": self.Channel,
            "Theme": self.Theme,
            "Type": self.Type,
            "Discipline": self.Discipline,
            "Pod": self.Pod,
            "Chapter": self.Chapter,
            "Contributor": self.Contributor,
            "Overlay": self.Overlay,
        }
        if type_import.get(type_to_import):
            func = type_import.get(type_to_import)
            return func(filedata)
        if type_to_import == 'UserProfile':
            newdata = filedata.replace(
                "core.userprofile", "authentication.owner"
            ).replace("\"image\":", "\"userpicture\":")

        return newdata

    def add_data_to_video(self, type_to_import, obj, data):
        if type_to_import in ('docpods',):
            self.add_doc_to_video(obj, data)
        if type_to_import in ('tags',):
            self.add_tag_to_video(obj, data)
        if type_to_import in ('trackpods',):
            self.add_track_to_video(obj, data)
        if type_to_import in ('enrichpods',):
            self.add_enrich_to_video(obj, data)

    def add_tag_to_video(self, video_id, list_tag):
        try:
            video = Video.objects.get(id=video_id)
            video.tags = ', '.join(list_tag)
            video.save()
        except ObjectDoesNotExist:
            print(video_id, " does not exist")

    def add_doc_to_video(self, video_id, list_doc):
        print(video_id, list_doc)
        try:
            video = Video.objects.get(id=video_id)
            for doc in list_doc:
                new_file = self.download_doc(doc)
                print("\n", new_file)
                document = self.create_and_save_doc(new_file, video)
                Document.objects.create(video=video, document=document)
        except ObjectDoesNotExist:
            print(video_id, " does not exist")

    def add_track_to_video(self, video_id, list_doc):
        print(video_id, list_doc)
        try:
            video = Video.objects.get(id=video_id)
            for doc in list_doc:
                new_file = self.download_doc(doc["src"])
                print("\n", new_file)
                fname, dot, extension = new_file.rpartition('.')
                if extension == "srt":
                    new_file = self.convert_to_vtt(new_file)
                else:
                    if extension != "vtt":
                        print("************ WARNING !!!!! ************")
                        print(video_id, list_doc)
                        print("************ ************")
                        new_file = ""
                if new_file != "":
                    document = self.create_and_save_doc(new_file, video)
                    Track.objects.create(video=video, src=document,
                                         kind=doc["kind"], lang=doc["lang"])
        except ObjectDoesNotExist:
            print(video_id, " does not exist")

    def convert_to_vtt(self, new_file):
        try:
            webvtt.from_srt(new_file).save(new_file[:-3] + "vtt")
            new_file = new_file[:-3] + "vtt"
            return new_file
        except UnicodeDecodeError:
            print("************ codecs ***********")
            with codecs.open(new_file,
                             "r",
                             encoding="latin-1") as sourceFile:
                with codecs.open(new_file[:-3] + "txt",
                                 "w",
                                 "utf-8") as targetFile:
                    contents = sourceFile.read()
                    targetFile.write(contents)
            webvtt.from_srt(
                new_file[:-3] + "txt").save(new_file[:-3] + "vtt")
            new_file = new_file[:-3] + "vtt"
            return new_file
        except webvtt.errors.MalformedFileError:
            print("************ "
                  "The file does not have a valid format. !!!!! "
                  "************")
            print(new_file)
            print("************ ************")
        return ""

    def add_enrich_to_video(self, video_id, list_doc):
        print(video_id)
        try:
            video = Video.objects.get(id=video_id)
            for doc in list_doc:
                image = None
                if doc["type"] == "image" and doc["image"] != "":
                    new_file = self.download_doc(doc["image"])
                    image = self.create_and_save_image(
                        new_file, video) if new_file != "" else None
                document = None
                if doc["type"] == "document" and doc["document"] != "":
                    new_file = self.download_doc(doc["document"])
                    document = self.create_and_save_doc(
                        new_file, video) if new_file != "" else None

                Enrichment.objects.create(
                    video=video, title=doc["title"],
                    stop_video=doc["stop_video"], start=doc["start"],
                    end=doc["end"], type=doc["type"], image=image,
                    document=document, richtext=doc["richtext"],
                    weblink=doc["weblink"], embed=doc["embed"]
                )

        except ObjectDoesNotExist:
            print(video_id, " does not exist")

    def download_doc(self, doc):
        source_url = FROM_URL + doc
        dest_file = os.path.join(
            settings.MEDIA_ROOT,
            'tempfile',
            os.path.basename(doc)
        )
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        new_file = wget.download(source_url, dest_file)
        return new_file

    def create_and_save_doc(self, new_file, video):
        if FILEPICKER:
            homedir, created = UserFolder.objects.get_or_create(
                name='home',
                owner=video.owner)
            videodir, created = UserFolder.objects.get_or_create(
                name='%s' % video.slug,
                owner=video.owner)
            document = CustomFileModel(
                folder=videodir,
                created_by=video.owner
            )
            document.file.save(
                os.path.basename(new_file),
                File(open(new_file, "rb")),
                save=True)
            document.save()
        else:
            document = CustomFileModel()
            document.file.save(
                os.path.basename(new_file),
                File(open(new_file, "rb")),
                save=True)
            document.save()
        return document

    def create_and_save_image(self, new_file, video):
        if FILEPICKER:
            homedir, created = UserFolder.objects.get_or_create(
                name='home',
                owner=video.owner)
            videodir, created = UserFolder.objects.get_or_create(
                name='%s' % video.slug,
                owner=video.owner)
            image = CustomImageModel(
                folder=videodir,
                created_by=video.owner
            )
            image.file.save(
                os.path.basename(new_file),
                File(open(new_file, "rb")),
                save=True)
            image.save()
        else:
            image = CustomFileModel()
            image.file.save(
                os.path.basename(new_file),
                File(open(new_file, "rb")),
                save=True)
            image.save()
        return image


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

from pods.models import ChapterPods
from pods.models import ContributorPods

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


with open("Chapter.json", "w") as out:
    json_serializer.serialize(ChapterPods.objects.all().order_by('video'),
        indent=2, stream=out)

with open("Contributor.json", "w") as out:
    json_serializer.serialize(ContributorPods.objects.all().order_by('video'),
        indent=2, stream=out)

list_doc = {}
for p in Pod.objects.all():
    list_doc["%s" %p.id] = []
    for d in p.docpods_set.all():
        list_doc["%s" %p.id].append(d.document.file.name)
with open("docpods.json", "w") as out:
    out.write(json.dumps(list_doc, indent=2))

list_track = {}
for p in Pod.objects.all():
    if p.trackpods_set.all().count() > 0:
        list_track["%s" %p.id] = []
        for d in p.trackpods_set.all():
            if d.src :
                data = {}
                data['kind'] = d.kind
                data['lang'] = d.lang
                data['src'] = d.src.file.name
                list_track["%s" %p.id].append(data)
with open("trackpods.json", "w") as out:
    out.write(json.dumps(list_track, indent=2))

list_enrich = {}
for p in Pod.objects.all().order_by('id'):
    if p.enrichpods_set.all().count() > 0:
        list_enrich["%s" %p.id] = []
        for d in p.enrichpods_set.all():
            data = {}
            data['title'] = d.title
            data['stop_video'] = d.stop_video
            data['start'] = d.start
            data['end'] = d.end
            data['type'] = d.type
            data['image'] = d.image.file.name if d.image else ""
            data['richtext'] = d.richtext
            data['weblink'] = d.weblink
            data['document'] = d.document.file.name if d.document else ""
            data['embed'] = d.embed
            list_enrich["%s" %p.id].append(data)

with open("enrichpods.json", "w") as out:
    out.write(json.dumps(list_enrich, indent=2))

"""
