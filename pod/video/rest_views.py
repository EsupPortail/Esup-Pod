from rest_framework import serializers, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

# from rest_framework import authentication, permissions
from rest_framework import renderers
from rest_framework.decorators import api_view
from rest_framework.decorators import action

from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404

from .models import Channel, Theme
from .models import Type, Discipline, Video
from .models import VideoRendition, EncodingVideo, EncodingAudio
from .models import PlaylistVideo, ViewCount
from .views import VIDEOS
from .remote_encode import start_store_remote_encoding_video
from .transcript import start_transcript

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
        fields = ("id", "url", "title", "description", "icon", "sites")


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
                "video_files": instance.get_audio_and_video_json(
                    request.GET.get("extensions", default=None)
                )
                if instance.get_audio_and_video_json(
                    request.GET.get("extensions", default=None)
                )
                else ""
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


class VideoRenditionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = VideoRendition
        fields = (
            "id",
            "url",
            "resolution",
            "video_bitrate",
            "audio_bitrate",
            "encode_mp4",
        )


class EncodingVideoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EncodingVideo
        fields = (
            "id",
            "url",
            "name",
            "video",
            "rendition",
            "encoding_format",
            "source_file",
        )


class EncodingAudioSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EncodingAudio
        fields = (
            "id",
            "url",
            "name",
            "video",
            "encoding_format",
            "source_file",
        )


class PlaylistVideoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PlaylistVideo
        fields = (
            "id",
            "url",
            "name",
            "video",
            "encoding_format",
            "source_file",
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
    filter_fields = (
        "owner",
        "type",
        "date_added",
        "is_draft",
        "is_restricted",
        "encoding_in_progress",
    )

    @action(detail=False, methods=["get"])
    def user_videos(self, request):
        user_videos = self.filter_queryset(self.get_queryset()).filter(
            owner__username=request.GET.get("username")
        )
        if request.GET.get("encoded") and request.GET.get("encoded") == "true":
            user_videos = user_videos.exclude(
                pk__in=[vid.id for vid in VIDEOS if not vid.encoded]
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


class VideoRenditionViewSet(viewsets.ModelViewSet):
    queryset = VideoRendition.objects.all()
    serializer_class = VideoRenditionSerializer


class EncodingVideoViewSet(viewsets.ModelViewSet):
    queryset = EncodingVideo.objects.all()
    serializer_class = EncodingVideoSerializer
    filter_fields = ("video",)

    @action(detail=False, methods=["get"])
    def video_encodedfiles(self, request):
        encoded_videos = EncodingVideoViewSet.filter_encoded_medias(
            self.queryset, request
        )
        encoded_videos = sorted(encoded_videos, key=lambda x: x.height)
        serializer = EncodingVideoSerializer(
            encoded_videos, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @staticmethod
    def filter_encoded_medias(queryset, request):
        encoded_audios = queryset
        if request.GET.get("video"):
            encoded_audios = encoded_audios.filter(video__id=request.GET.get("video"))
        if request.GET.get("extension"):
            encoded_audios = encoded_audios.filter(
                source_file__iendswith=request.GET.get("extension")
            )
        return encoded_audios


class EncodingAudioViewSet(viewsets.ModelViewSet):
    queryset = EncodingAudio.objects.all()
    serializer_class = EncodingAudioSerializer
    filter_fields = ("video",)

    @action(detail=False, methods=["get"])
    def audio_encodedfiles(self, request):
        encoded_audios = EncodingVideoViewSet.filter_encoded_medias(
            self.queryset, request
        )
        serializer = EncodingAudioSerializer(
            encoded_audios, many=True, context={"request": request}
        )
        return Response(serializer.data)


class PlaylistVideoViewSet(viewsets.ModelViewSet):
    queryset = PlaylistVideo.objects.all()
    serializer_class = PlaylistVideoSerializer


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

    def get(self, request, format=None):
        list_videos = VIDEOS
        if request.GET:
            list_videos = VIDEOS.filter(**request.GET.dict())
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
            xmlcontent += rendered
        xmlcontent += "</rdf:RDF>"
        return Response(xmlcontent)


@api_view(["GET"])
def launch_encode_view(request):
    video = get_object_or_404(Video, slug=request.GET.get("slug"))
    if (
        video is not None
        and (
            not hasattr(video, "launch_encode") or getattr(video, "launch_encode") is True
        )
        and video.encoding_in_progress is False
    ):
        video.launch_encode = True
        video.save()
    return Response(VideoSerializer(instance=video, context={"request": request}).data)


@api_view(["GET"])
def launch_transcript_view(request):
    video = get_object_or_404(Video, slug=request.GET.get("slug"))
    if video is not None and video.get_video_mp3():
        start_transcript(video.id, threaded=True)
    return Response(VideoSerializer(instance=video, context={"request": request}).data)


@api_view(["GET"])
def store_remote_encoded_video(request):
    video_id = request.GET.get("id", 0)
    video = get_object_or_404(Video, id=video_id)
    start_store_remote_encoding_video(video_id)
    return Response(VideoSerializer(instance=video, context={"request": request}).data)
