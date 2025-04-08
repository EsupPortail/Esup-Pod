from django.conf import settings
from .models import EncodingVideo, EncodingAudio, VideoRendition, PlaylistVideo
from pod.video.models import Video
from pod.recorder.models import Recording
from pod.video.rest_views import VideoSerializer

from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import SuspiciousOperation

import json
import logging
import os
import webvtt

USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)
if USE_TRANSCRIPTION:
    from pod.video_encode_transcript.transcript import start_transcript

MEDIA_ROOT = getattr(settings, "MEDIA_ROOT", "")

DEBUG = getattr(settings, "DEBUG", True)
logger = logging.getLogger(__name__)
if DEBUG:
    logger.setLevel(logging.DEBUG)


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
    filterset_fields = [
        "video",
    ]

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
    filterset_fields = [
        "video",
    ]

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
    """View API for launching video encoding."""
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
    """View API for launching transcript."""
    video = get_object_or_404(Video, slug=request.GET.get("slug"))
    if video is not None and video.get_video_mp3():
        start_transcript(video.id, threaded=True)
    return Response(VideoSerializer(instance=video, context={"request": request}).data)


@csrf_exempt
@api_view(["POST"])
def store_remote_encoded_video(request):
    """View API for storing remote encoded videos."""
    from .Encoding_video_model import Encoding_video_model
    from .encode import store_encoding_info, end_of_encoding

    video_id = request.GET.get("id", 0)
    logger.info("Start importing encoding data for video: %s" % video_id)
    video = get_object_or_404(Video, id=video_id)
    # start_store_remote_encoding_video(video_id)
    # check if video is encoding!!!
    data = json.loads(request.body.decode("utf-8"))
    if video.encoding_in_progress is False:
        raise SuspiciousOperation("Video not being encoded.")
    if str(video_id) != str(data["video_id"]):
        raise SuspiciousOperation(
            "Different video id: %s - %s" % (video_id, data["video_id"])
        )
    encoding_video = Encoding_video_model(
        video_id, data["video_path"], data["cut_start"], data["cut_end"]
    )
    encoding_video.start = data["start"]
    encoding_video.stop = data["stop"]
    final_video = store_encoding_info(video_id, encoding_video)
    end_of_encoding(final_video)
    return Response(VideoSerializer(instance=video, context={"request": request}).data)


@csrf_exempt
@api_view(["POST"])
def store_remote_encoded_video_studio(request):
    from .encode import store_encoding_studio_info

    recording_id = request.GET.get("recording_id", 0)
    get_object_or_404(Recording, id=recording_id)
    data = json.loads(request.body.decode("utf-8"))
    store_encoding_studio_info(recording_id, data["video_output"], data["msg"])
    return Response("ok")


@csrf_exempt
@api_view(["POST"])
def store_remote_transcripted_video(request):
    """View API for storing remote transcripted videos."""
    from .transcript import save_vtt_and_notify

    video_id = request.GET.get("id", 0)
    video = get_object_or_404(Video, id=video_id)
    # check if video is encoding!!!
    data = json.loads(request.body.decode("utf-8"))
    if str(video_id) != str(data["video_id"]):
        raise SuspiciousOperation(
            "different video id: %s - %s" % (video_id, data["video_id"])
        )
    logger.info("Start importing transcription data for video: %s" % video_id)
    filename = os.path.basename(data["temp_vtt_file"])
    media_temp_dir = os.path.join(MEDIA_ROOT, "temp")
    filepath = os.path.join(media_temp_dir, filename)
    new_vtt = webvtt.read(filepath)
    save_vtt_and_notify(video, data["msg"], new_vtt)
    os.remove(filepath)
    return Response(VideoSerializer(instance=video, context={"request": request}).data)
