from rest_framework import serializers, viewsets
from .models import EncodingVideo, EncodingAudio
from rest_framework.decorators import action
from rest_framework.response import Response


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
            "sites_all",
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
            "sites_all",
        )


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
