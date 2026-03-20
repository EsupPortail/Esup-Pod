"""
Esup-Pod - Webhook handler for the encoding process.

This module provides the view to receive and process encoding task results 
from the runner manager.
"""
import logging
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist

from src.apps.video.models import Video
from config.env import env
from src.apps.encoding.services.runner_client import get_runner_client

logger = logging.getLogger(__name__)


class EncodingWebhookView(APIView):
    """
    Webhook called by the runner manager when the encoding is completed.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        if not self._is_secret_valid(request):
            return Response(
                {"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED
            )

        payload = request.data
        logger.info("Received encoding webhook with payload: %s", payload)

        task_id = payload.get("task_id")
        video_id = self._extract_video_id(request, payload)

        if not task_id:
            logger.error("Missing task_id in webhook payload")
            return Response(
                {"error": "Missing task_id"}, status=status.HTTP_400_BAD_REQUEST
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

        if payload.get("status") in ["success", "completed"]:
            return self._handle_encoding_success(video, task_id)
        else:
            return self._handle_encoding_failure(video, payload)

    def _is_secret_valid(self, request) -> bool:
        """Check if the secret provided in the URL matches the expected secret."""
        secret_provided = request.query_params.get("secret")
        webhook_secret = env("ENCODING_WEBHOOK_SECRET", default="")

        if webhook_secret and secret_provided != webhook_secret:
            logger.warning("Invalid webhook secret received: %s", secret_provided)
            return False
        return True

    def _extract_video_id(self, request, payload):
        """Extract the video ID from the query_params or the payload."""
        video_id = request.query_params.get("video_id")
        if not video_id:
            video_id = payload.get("video_id") or payload.get("parameters", {}).get(
                "video_id"
            )
        return video_id

    def _handle_encoding_success(self, video: Video, task_id: str) -> Response:
        """Handle the success of the encoding: retrieve the manifest and update the files."""
        try:
            client = get_runner_client()
            manifest = client.get_task_manifest(task_id)
            logger.info("Manifest retrieved for task %s: %s", task_id, manifest)

            file_list = manifest.get("files", [])
            video_path = self._get_best_video_path(file_list)
            thumbnail_path = "overview.png" if "overview.png" in file_list else None

            self._replace_video_files(video, client, task_id, video_path, thumbnail_path)

            video.status = Video.Status.PUBLISHED
            video.save()

            logger.info("Video pk=%s downloaded successfully and published.", video.pk)
            return Response({"status": "published"})

        except Exception as e:
            logger.error(
                "Error during file retrieval for video pk=%s: %s",
                video.pk,
                e,
                exc_info=True,
            )
            video.status = Video.Status.ERROR
            video.save(update_fields=["status"])
            return Response(
                {"status": "error_during_download"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _handle_encoding_failure(self, video: Video, payload: dict) -> Response:
        """Handle the failure of an encoding reported by the runner."""
        video.status = Video.Status.ERROR
        video.save(update_fields=["status"])
        error_msg = payload.get("error_message") or payload.get("error")
        logger.error("Encoding failed for video pk=%s: %s", video.pk, error_msg)
        return Response({"status": "error_recorded"})

    def _get_best_video_path(self, file_list: list) -> str | None:
        """Iterate through the manifest to find the best available MP4 quality."""
        for res in ["1080p", "720p", "360p"]:
            match = next(
                (f for f in file_list if f.startswith(res) and f.endswith(".mp4")), None
            )
            if match:
                return match

        return next((f for f in file_list if f.endswith(".mp4")), None)

    def _replace_video_files(
        self, video: Video, client, task_id: str, video_path: str, thumbnail_path: str
    ):
        """Delete old files and download new files generated by the runner."""
        if video.video_file:
            video.video_file.delete(save=False)

        if video_path:
            encoded_video = client.download_task_file_to_temp(task_id, video_path)
            video.video_file.save(encoded_video.name, encoded_video, save=False)
            os.unlink(encoded_video.file.name)

        if thumbnail_path:
            if video.overview:
                video.overview.delete(save=False)
            new_overview = client.download_task_file_to_temp(task_id, thumbnail_path)
            video.overview.save(new_overview.name, new_overview, save=False)
            os.unlink(new_overview.file.name)
