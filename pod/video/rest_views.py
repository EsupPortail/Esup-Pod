from pod.video.models import Channel, Theme
from pod.video.models import VideoImageModel, Type, Discipline, Video
from pod.video.models import VideoRendition, EncodingVideo, EncodingAudio
from pod.video.models import PlaylistVideo
from rest_framework import serializers, viewsets

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


class VideoImageModelSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = VideoImageModel
        fields = ('id', 'url', 'file',)


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
            'id', 'url', 'title', 'description',
            'allow_downloading', 'is_360', 'owner', 'date_added', 'date_evt',
            'cursus', 'main_lang', 'is_draft', 'is_restricted',
            'restrict_access_to_groups', 'password', 'tags', 'thumbnail',
            'type', 'discipline', 'channel', 'theme', 'licence'
        )


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


class VideoImageModelViewSet(viewsets.ModelViewSet):
    queryset = VideoImageModel.objects.all()
    serializer_class = VideoImageModelSerializer


class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer


class DisciplineViewSet(viewsets.ModelViewSet):
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


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
