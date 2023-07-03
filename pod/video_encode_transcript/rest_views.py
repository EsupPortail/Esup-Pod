from rest_framework import serializers, viewsets
from django.conf import settings
from .models import EncodingVideo, EncodingAudio, VideoRendition, PlaylistVideo
from pod.video.models import Video
from pod.video.rest_views import VideoSerializer

from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)
if USE_TRANSCRIPTION:
    from pod.video_encode_transcript.transcript import start_transcript


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
            "sites_all",
        )


class PlaylistVideoViewSet(viewsets.ModelViewSet):
    queryset = PlaylistVideo.objects.all()
    serializer_class = PlaylistVideoSerializer


@api_view(["GET"])
def launch_encode_view(request):
    """API view for launching video encoding."""
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
    """API view for launching transcript."""
    video = get_object_or_404(Video, slug=request.GET.get("slug"))
    if video is not None and video.get_video_mp3():
        start_transcript(video.id, threaded=True)
    return Response(VideoSerializer(instance=video, context={"request": request}).data)


@api_view(["GET"])
def store_remote_encoded_video(request):
    """API view for storing remote encoded videos."""
    video_id = request.GET.get("id", 0)
    video = get_object_or_404(Video, id=video_id)
    # start_store_remote_encoding_video(video_id)
    return Response(VideoSerializer(instance=video, context={"request": request}).data)
