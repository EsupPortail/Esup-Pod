from pod.video.models import Channel, Theme
from pod.video.models import Type, Discipline, Video
from pod.video.models import VideoRendition, EncodingVideo, EncodingAudio
from pod.video.models import PlaylistVideo
from rest_framework import serializers, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
# from rest_framework import authentication, permissions
from rest_framework import renderers
from rest_framework.decorators import api_view
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404

from pod.video.views import VIDEOS

# Serializers define the API representation.


class ChannelSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Channel
        fields = ('id', 'url', 'title', 'description', 'headband',
                  'color', 'style', 'owners', 'users', 'visible', 'themes')


class ThemeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Theme
        fields = (
            'id', 'url', 'parentId', 'title',
            'headband', 'description', 'channel')


class TypeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Type
        fields = ('id', 'url', 'title', 'description', 'icon')


class DisciplineSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Discipline
        fields = ('id', 'url', 'title', 'description', 'icon')


class VideoSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Video
        fields = (
            'id', 'url', 'video', 'title', 'slug', 'description',
            'allow_downloading', 'is_360', 'owner', 'additional_owners',
            'date_added', 'date_evt', 'cursus', 'main_lang',
            'is_draft', 'is_restricted', 'restrict_access_to_groups',
            'password', 'tags', 'thumbnail',
            'type', 'discipline', 'channel', 'theme', 'licence'
        )
        filter_fields = ('owner', 'type', 'date_added')
        read_only_fields = ('encoding_in_progress', 'duration')


class VideoRenditionSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = VideoRendition
        fields = ('id', 'url', 'resolution', 'video_bitrate',
                  'audio_bitrate', 'encode_mp4'
                  )


class EncodingVideoSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = EncodingVideo
        fields = ('id', 'url', 'name', 'video',
                  'rendition', 'encoding_format', 'source_file'
                  )


class EncodingAudioSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = EncodingAudio
        fields = ('id', 'url', 'name', 'video',
                  'encoding_format', 'source_file'
                  )


class PlaylistVideoSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = PlaylistVideo
        fields = ('id', 'url', 'name', 'video',
                  'encoding_format', 'source_file'
                  )


#############################################################################
# ViewSets define the view behavior.
#############################################################################


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all().order_by('channel')
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
    filter_fields = ('owner', 'type', 'date_added', 'channel', 'discipline')


class VideoRenditionViewSet(viewsets.ModelViewSet):
    queryset = VideoRendition.objects.all()
    serializer_class = VideoRenditionSerializer


class EncodingVideoViewSet(viewsets.ModelViewSet):
    queryset = EncodingVideo.objects.all()
    serializer_class = EncodingVideoSerializer


class EncodingAudioViewSet(viewsets.ModelViewSet):
    queryset = EncodingAudio.objects.all()
    serializer_class = EncodingAudioSerializer


class PlaylistVideoViewSet(viewsets.ModelViewSet):
    queryset = PlaylistVideo.objects.all()
    serializer_class = PlaylistVideoSerializer


class XmlTextRenderer(renderers.BaseRenderer):
    media_type = 'text/xml'
    format = 'xml'
    charset = 'utf-8'

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
    renderer_classes = (XmlTextRenderer, )
    pagination_class = 'rest_framework.pagination.PageNumberPagination'
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get(self, request, format=None):
        list_videos = VIDEOS
        if request.GET:
            list_videos = VIDEOS.filter(**request.GET.dict())
        xmlcontent = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
        xmlcontent += ("<!DOCTYPE rdf:RDF PUBLIC "
                       "\"-//DUBLIN CORE//DCMES DTD 2002/07/31//EN\" \n")
        xmlcontent += ("\"http://dublincore.org/documents/2002/07"
                       "/31/dcmes-xml/dcmes-xml-dtd.dtd\">\n")
        xmlcontent += ("<rdf:RDF xmlns:rdf="
                       "\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\""
                       " xmlns:dc =\"http://purl.org/dc/elements/1.1/\">\n")
        for video in list_videos:
            rendered = render_to_string(
                'videos/dublincore.html',
                {'video': video, "xml": True},
                request)
            xmlcontent += rendered
        xmlcontent += "</rdf:RDF>"
        return Response(xmlcontent)


@api_view(['GET'])
def launch_encode_view(request):
    video = get_object_or_404(Video, slug=request.GET.get('slug'))
    if (
            video is not None
            and (
                not hasattr(video, 'launch_encode')
                or getattr(video, 'launch_encode') is True
            )
            and video.encoding_in_progress is False
    ):
        video.launch_encode = True
        video.save()
    return Response(
        VideoSerializer(instance=video, context={'request': request}).data
    )
