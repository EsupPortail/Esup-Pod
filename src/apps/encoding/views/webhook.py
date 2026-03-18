import logging
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist

from src.apps.video.models import Video
from config.env import env

logger = logging.getLogger(__name__)


class EncodingWebhookView(APIView):
    """
    Webhook called by the runner manager when encoding is finished.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        secret_provided = request.query_params.get("secret")
        webhook_secret = env("ENCODING_WEBHOOK_SECRET", default="")

        if webhook_secret and secret_provided != webhook_secret:
            logger.warning("Invalid webhook secret received: %s", secret_provided)
            return Response(
                {"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        payload = request.data
        logger.info("Received encoding webhook with payload: %s", payload)

        video_id = request.query_params.get("video_id")

        if not video_id:
            video_id = payload.get("video_id") or payload.get("parameters", {}).get(
                "video_id"
            )

        if not video_id:
            return Response(
                {"error": "Missing video_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            video = Video.objects.get(pk=video_id)
        except ObjectDoesNotExist:
            return Response(
                {"error": "Video not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if payload.get("status") in [
            "success",
            "completed",
        ]:

            update_fields = self._update_video_from_payload(video, payload)
            video.status = Video.Status.PUBLISHED
            video.save(update_fields=update_fields)

            logger.info("Video %s successfully published via webhook.", video.pk)
            return Response({"status": "published"})

        else:
            video.status = Video.Status.ERROR
            video.save(update_fields=["status"])
            logger.error(
                "Encoding failed for video %s: %s", video.pk, payload.get("error")
            )
            return Response({"status": "error_recorded"})

    def _update_video_from_payload(self, video, payload) -> list:
        results = {}
        script_output = payload.get("script_output")

        if script_output:
            try:
                results = json.loads(script_output)
            except json.JSONDecodeError:
                logger.warning("Could not parse script_output as JSON: %s", script_output)
        if not results and isinstance(payload.get("results"), dict):
            results = payload.get("results")

        update_fields = ["status"]

        duration = payload.get("duration") or results.get("duration")
        if duration:
            video.duration = int(float(duration))
            update_fields.append("duration")

        thumbnail_path = results.get("thumbnail_path")
        if thumbnail_path:
            video.thumbnail.name = thumbnail_path
            update_fields.append("thumbnail")

        video_path = results.get("video_path")
        if video_path:
            video.video_file.name = video_path
            update_fields.append("video_file")

        return update_fields
