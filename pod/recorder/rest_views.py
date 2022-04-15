from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.response import Response
from django.http import HttpResponseRedirect, JsonResponse
from .models import RecordingFile, Recording, Recorder


class RecordingModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Recording
        fields = ("id", "url", "user", "title", "source_file", "type")


class RecorderModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Recorder
        fields = ("id", "name", "description", "address_ip", "recording_type", "sites")


class RecordingFileModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RecordingFile
        fields = ("id", "url", "file", "recorder")


class RecordingModelViewSet(viewsets.ModelViewSet):
    queryset = Recording.objects.all()
    serializer_class = RecordingModelSerializer


class RecordingFileModelViewSet(viewsets.ModelViewSet):
    queryset = RecordingFile.objects.all()
    serializer_class = RecordingFileModelSerializer


class RecorderModelViewSet(viewsets.ModelViewSet):
    queryset = Recorder.objects.all()
    serializer_class = RecorderModelSerializer


@api_view(["GET"])
def studio_series(request, file):
    print("studio_series")
    print('HTTP_AUTHORIZATION')
    print(request.META.get('HTTP_AUTHORIZATION'))
    print(request.META.get('Authorization'))
    print(file)
    print(request.POST)
    print(request.body)
    print(request.content_params)
    #for meta in request.META:
    #    print(meta, request.META.get(meta))
    series_json = {
        "total": 4,
        "offset": 0,
        "count": 4,
        "limit": 50,
        "results": [
            {
            "createdBy": "Administrator",
            "organizers": [],
            "id": "ID-blender-foundation",
            "contributors": [],
            "creation_date": "2022-03-02T01:03:00Z",
            "title": "Blender Foundation Productions"
            },
            {
            "createdBy": "Administrator",
            "organizers": [],
            "id": "ID-wiki-commons",
            "contributors": [],
            "creation_date": "2022-03-02T01:03:00Z",
            "title": "Wiki Commons Content"
            },
            {
            "createdBy": "Administrator",
            "organizers": [],
            "id": "ID-av-portal",
            "contributors": [],
            "creation_date": "2022-03-02T01:03:00Z",
            "title": "AV-Portal Content"
            },
            {
            "createdBy": "Administrator",
            "organizers": [],
            "id": "ID-openmedia-opencast",
            "contributors": [],
            "creation_date": "2022-03-02T01:03:00Z",
            "title": "Open Media for Opencast"
            }
        ]
    }
    return JsonResponse(series_json, status=200)

@api_view(["GET"])
def studio_services(request, file):
    print('studio_services')
    print('HTTP_AUTHORIZATION')
    print(request.META.get('HTTP_AUTHORIZATION'))
    print(request.META.get('Authorization'))
    print(request.POST)
    print(request.META)
    info = {}
    if file == "available.json":
        info = {
            "services": {
                "service":{
                    "type": "org.opencastproject.ingest",
                    "host": "http://pod2-test.univ-lille.fr/rest/studio",
                    "path": "/rest/studio",
                    "active": True,
                    "online": True,
                    "maintenance": False,
                    "jobproducer": True,
                    "onlinefrom": "2022-03-16T02:01:03.815+01:00",
                    "service_state":"NORMAL",
                    "state_changed": "2022-03-16T02:01:03.815+01:00",
                    "error_state_trigger":0,
                    "warning_state_trigger":0
                }
            }
        }
    return JsonResponse(info, status=200)

@api_view(["GET"])
def studio_api_series(request):
    print('HTTP_AUTHORIZATION')
    print(request.META.get('HTTP_AUTHORIZATION'))
    print(request.META.get('Authorization'))
    series = [
    {
        "identifier": "ID-blender-foundation",
        "license": "",
        "creator": "Administrator",
        "created": "2022-03-02T01:03:00Z",
        "subjects": [],
        "organizers": [],
        "description": "",
        "publishers": [
        "Blender Foundation"
        ],
        "language": "",
        "contributors": [],
        "title": "Blender Foundation Productions",
        "rightsholder": ""
    },
    {
        "identifier": "ID-wiki-commons",
        "license": "",
        "creator": "Administrator",
        "created": "2022-03-02T01:03:00Z",
        "subjects": [],
        "organizers": [],
        "description": "",
        "publishers": [
        "Wiki Commons"
        ],
        "language": "",
        "contributors": [],
        "title": "Wiki Commons Content",
        "rightsholder": ""
    },
    {
        "identifier": "ID-av-portal",
        "license": "",
        "creator": "Administrator",
        "created": "2022-03-02T01:03:00Z",
        "subjects": [],
        "organizers": [],
        "description": "",
        "publishers": [
        "TIB AV-Portal Hannover"
        ],
        "language": "",
        "contributors": [],
        "title": "AV-Portal Content",
        "rightsholder": ""
    },
    {
        "identifier": "ID-openmedia-opencast",
        "license": "",
        "creator": "Administrator",
        "created": "2022-03-02T01:03:00Z",
        "subjects": [],
        "organizers": [],
        "description": "Media snippets published as test media for Opencast.",
        "publishers": [
        "Lars Kiesow"
        ],
        "language": "",
        "contributors": [],
        "title": "Open Media for Opencast",
        "rightsholder": ""
    }
    ]
    return JsonResponse(series, status=200)