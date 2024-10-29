"""Esup-Pod REST views."""

from rest_framework import serializers, viewsets, renderers
from rest_framework.views import APIView
from rest_framework.response import Response

# from rest_framework import authentication, permissions
from rest_framework.decorators import action

from django.template.loader import render_to_string

from .models import Channel, Theme
from .models import Type, Discipline, Video
from .models import ViewCount
from .context_processors import get_available_videos

from pod.main.utils import remove_trailing_spaces

# commented for v3
# from .remote_encode import start_store_remote_encoding_video

import json

# Serializers define the API representation.


class ChannelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Channel
        fields = (
            "id",
            "url",
            "title",
            "description",
            "headband",
            "color",
            "style",
            "owners",
            "users",
            "visible",
            "themes",
            "site",
        )


class ThemeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Theme
        fields = (
            "id",
            "url",
            "parentId",
            "title",
            "headband",
            "description",
            "channel",
        )


class TypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Type
        fields = ("id", "url", "title", "description", "icon", "sites")


class DisciplineSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Discipline
        fields = ("id", "url", "title", "description", "icon", "site")


class VideoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Video
        fields = (
            "id",
            "url",
            "video",
            "title",
            "slug",
            "description",
            "allow_downloading",
            "is_360",
            "owner",
            "additional_owners",
            "date_added",
            "date_evt",
            "cursus",
            "main_lang",
            "is_draft",
            "is_restricted",
            "restrict_access_to_groups",
            "password",
            "tags",
            "thumbnail",
            "type",
            "discipline",
            "channel",
            "theme",
            "licence",
            "encoding_in_progress",
            "duration",
            "sites",
            "disable_comment",
            "get_encoding_step",
            "get_version",
            "encoded",
            "duration_in_time",
        )
        read_only_fields = (
            "encoding_in_progress",
            "duration",
            "get_encoding_step",
            "get_version",
            "encoded",
            "duration_in_time",
        )


class VideoUserSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        data = super(VideoUserSerializer, self).to_representation(instance)
        request = self.context["request"]
        video_data = json.loads(instance.get_json_to_index())
        video_data.update({"encoded": instance.encoded})
        video_data.update({"encoding_in_progress": instance.encoding_in_progress})
        video_data.update({"get_encoding_step": instance.get_encoding_step})
        video_data.update({"get_thumbnail_admin": instance.get_thumbnail_admin})
        video_data.update(
            {
                "video_files": (
                    instance.get_audio_and_video_json(
                        request.GET.get("extensions", default=None)
                    )
                    if instance.get_audio_and_video_json(
                        request.GET.get("extensions", default=None)
                    )
                    else ""
                )
            }
        )
        data["video_data"] = video_data
        return data

    class Meta:
        model = Video
        fields = (
            "id",
            "url",
            "get_version",
            "type",
            "date_added",
            "is_draft",
            "is_restricted",
            "encoding_in_progress",
            "encoded",
        )
        read_only_fields = (
            "encoding_in_progress",
            "duration",
            "get_encoding_step",
            "get_version",
            "encoded",
            "duration_in_time",
        )


class ViewCountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ViewCount
        fields = (
            "video",
            "date",
            "count",
        )


#############################################################################
# ViewSets define the view behavior.
#############################################################################


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all().order_by("channel")
    serializer_class = ThemeSerializer


class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer


class DisciplineViewSet(viewsets.ModelViewSet):
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    filterset_fields = [
        "owner",
        "type",
        "date_added",
        "is_draft",
        "is_restricted",
        "encoding_in_progress",
        "sites",
    ]

    @action(detail=False, methods=["get"])
    def user_videos(self, request):
        user_videos = self.filter_queryset(self.get_queryset()).filter(
            owner__username=request.GET.get("username")
        )
        if request.GET.get("encoded") and request.GET.get("encoded") == "true":
            user_videos = user_videos.exclude(
                pk__in=[vid.id for vid in user_videos if not vid.encoded]
            )
        if request.GET.get("search_title") and request.GET.get("search_title") != "":
            user_videos = user_videos.filter(
                title__icontains=request.GET.get("search_title")
            )
        page = self.paginate_queryset(user_videos)
        if page is not None:
            serializer = VideoUserSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = VideoUserSerializer(
            user_videos, many=True, context={"request": request}
        )
        return Response(serializer.data)


class ViewCountViewSet(viewsets.ModelViewSet):
    queryset = ViewCount.objects.all()
    serializer_class = ViewCountSerializer


class XmlTextRenderer(renderers.BaseRenderer):
    media_type = "text/xml"
    format = "xml"
    charset = "utf-8"

    def render(self, data, media_type=None, renderer_context=None):
        if type(data) is dict:
            data_str = ""
            for k, v in data.items():
                k = str(k).encode(self.charset).decode()
                v = str(v).encode(self.charset).decode()
                data_str += "%s: %s" % (k, v)
            return data_str
        else:
            return data.encode(self.charset)


class DublinCoreView(APIView):
    # authentication_classes = [authentication.TokenAuthentication]
    renderer_classes = (XmlTextRenderer,)
    pagination_class = "rest_framework.pagination.PageNumberPagination"
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get(self, request, format=None) -> Response:
        list_videos = get_available_videos(request)
        if request.GET:
            list_videos = list_videos.filter(**request.GET.dict())
        xmlcontent = '<?xml version="1.0" encoding="utf-8"?>\n'
        xmlcontent += (
            "<!DOCTYPE rdf:RDF PUBLIC " '"-//DUBLIN CORE//DCMES DTD 2002/07/31//EN" \n'
        )
        xmlcontent += (
            '"http://dublincore.org/documents/2002/07'
            '/31/dcmes-xml/dcmes-xml-dtd.dtd">\n'
        )
        xmlcontent += (
            "<rdf:RDF xmlns:rdf="
            '"http://www.w3.org/1999/02/22-rdf-syntax-ns#"'
            ' xmlns:dc ="http://purl.org/dc/elements/1.1/">\n'
        )
        for video in list_videos:
            rendered = render_to_string(
                "videos/dublincore.html", {"video": video, "xml": True}, request
            )
            xmlcontent += remove_trailing_spaces(rendered)
        xmlcontent += "</rdf:RDF>"
        return Response(xmlcontent)
