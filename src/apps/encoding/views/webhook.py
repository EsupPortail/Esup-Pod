import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from src.apps.video.models import Video

logger = logging.getLogger(__name__)

class EncodingWebhookView(APIView):
    """
    Webhook called by the runner manager when encoding is finished.
    """
    permission_classes = []  # Public endpoint, protected by secret

    def post(self, request, *args, **kwargs):
        from config.env import env
        
        # Security check
        secret = request.headers.get("X-Webhook-Secret")
        webhook_secret = env("ENCODING_WEBHOOK_SECRET", default="")
        if webhook_secret and secret != webhook_secret:
            logger.warning("Invalid webhook secret received: %s", secret)
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        payload = request.data
        logger.info("Received encoding webhook with payload: %s", payload)

        video_id = payload.get("video_id") or payload.get("parameters", {}).get("video_id")
        
        if not video_id:
            return Response({"error": "Missing video_id"}, status=status.HTTP_400_BAD_REQUEST)

        video = get_object_or_404(Video, pk=video_id)

        if payload.get("status") == "success":
            results = payload.get("results", {})
            duration = payload.get("duration") or results.get("duration")
            
            # The runner should provide paths relative to media root or absolute paths
            # that we can map. For now, we update the fields if provided.
            if duration:
                video.duration = int(float(duration))
            
            # Update thumbnail if provided
            thumbnail_path = results.get("thumbnail_path")
            if thumbnail_path:
                video.thumbnail.name = thumbnail_path

            # Update video file if provided
            video_path = results.get("video_path")
            if video_path:
                video.video_file.name = video_path

            video.status = Video.Status.PUBLISHED
            video.save()
            
            logger.info("Video %s successfully published via webhook.", video.pk)
            return Response({"status": "published"})
        
        else:
            video.status = Video.Status.ERROR
            video.save()
            logger.error("Encoding failed for video %s: %s", video.pk, payload.get("error"))
            return Response({"status": "error_recorded"})
