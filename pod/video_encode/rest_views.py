from rest_framework import serializers, viewsets
from .models import EncodingVideo, EncodingAudio, VideoRendition
from rest_framework.decorators import action
from rest_framework.response import Response


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
            "sites",
        )


class EncodingVideoSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for the EncodingVideo model."""

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
            "sites_all",
        )


class EncodingAudioSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for the EncodingAudio model."""

    class Meta:
        model = EncodingAudio
        fields = (
            "id",
            "url",
            "name",
            "video",
            "encoding_format",
            "source_file",
            "sites_all",
        )


class EncodingVideoViewSet(viewsets.ModelViewSet):
    """Viewset for EncodingVideo model."""

    queryset = EncodingVideo.objects.all()
    serializer_class = EncodingVideoSerializer
    filter_fields = ("video",)

    @action(detail=False, methods=["get"])
    def video_encodedfiles(self, request):
        """Retrieve encoded video files."""
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
        """Filter encoded media files."""
        encoded_audios = queryset
        if request.GET.get("video"):
            encoded_audios = encoded_audios.filter(video__id=request.GET.get("video"))
        if request.GET.get("extension"):
            encoded_audios = encoded_audios.filter(
                source_file__iendswith=request.GET.get("extension")
            )
        return encoded_audios


class EncodingAudioViewSet(viewsets.ModelViewSet):
    """Viewset for EncodingAudio model."""

    queryset = EncodingAudio.objects.all()
    serializer_class = EncodingAudioSerializer
    filter_fields = ("video",)

    @action(detail=False, methods=["get"])
    def audio_encodedfiles(self, request):
        """Retrieve encoded audio files."""
        encoded_audios = EncodingVideoViewSet.filter_encoded_medias(
            self.queryset, request
        )
        serializer = EncodingAudioSerializer(
            encoded_audios, many=True, context={"request": request}
        )
        return Response(serializer.data)


class VideoRenditionViewSet(viewsets.ModelViewSet):
    queryset = VideoRendition.objects.all()
    serializer_class = VideoRenditionSerializer
