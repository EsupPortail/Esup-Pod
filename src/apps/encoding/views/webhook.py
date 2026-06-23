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
import contextlib
from drf_spectacular.utils import extend_schema, OpenApiResponse

from src.apps.video.models import Video
from config.env import env
from src.apps.encoding.services.runner_client import get_runner_client
from src.apps.encoding.conf import encoding_settings
from src.apps.encoding.models import EncodingVideo

logger = logging.getLogger(__name__)


class EncodingWebhookView(APIView):
    """
    Webhook called by the runner manager when the encoding is completed.
    """

    permission_classes = []
    authentication_classes = []

    @extend_schema(
        request=None,
        responses={
            200: OpenApiResponse(description="Encoding result processed successfully."),
            400: OpenApiResponse(description="Missing required fields in payload."),
            401: OpenApiResponse(description="Invalid or missing webhook secret."),
            404: OpenApiResponse(description="Video not found."),
            500: OpenApiResponse(description="Error during file retrieval."),
        },
    )
    def post(self, request, *args, **kwargs):
        """Handle incoming webhook payload from the encoding runner."""
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
        webhook_secret = env("ENCODING_WEBHOOK_SECRET", default="")
        if not webhook_secret:
            logger.critical(
                "ENCODING_WEBHOOK_SECRET is not configured. Webhook disabled."
            )
            return False

        secret_provided = request.query_params.get("secret")
        if secret_provided != webhook_secret:
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
            from pathlib import Path

            image_extensions = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
            # Esup-Runner generates thumbnails like <filename>_0.png, <filename>_1.png...
            # We match any image file whose stem ends with "_0", regardless of extension,
            # so that future runner output formats (e.g. .webp) are handled automatically.
            thumbnail_path = next(
                (
                    name
                    for name in file_list
                    if Path(name).suffix.lower() in image_extensions
                    and Path(name).stem.endswith("_0")
                ),
                None,
            )
            # Fallback if no dynamic name is found
            if not thumbnail_path:
                fallback_candidates = {"thumbnail.png", "thumbnail.jpg", "thumbnail.webp"}
                thumbnail_path = next(
                    (name for name in file_list if name in fallback_candidates), None
                )

            self._process_video_files(video, client, task_id, file_list, thumbnail_path)

            # Mark encoding as done.
            video.encoding_status = Video.EncodingStatus.DONE
            video.save()

            logger.info("Video pk=%s encoded successfully.", video.pk)
            return Response({"status": "published"})

        except Exception as e:
            logger.error(
                "Error during file retrieval for video pk=%s: %s",
                video.pk,
                e,
                exc_info=True,
            )
            video.encoding_status = Video.EncodingStatus.ERROR
            video.save(update_fields=["encoding_status"])
            return Response(
                {"status": "error_during_download"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _handle_encoding_failure(self, video: Video, payload: dict) -> Response:
        """Handle the failure of an encoding reported by the runner."""
        video.encoding_status = Video.EncodingStatus.ERROR
        video.save(update_fields=["encoding_status"])
        error_msg = payload.get("error_message") or payload.get("error")
        logger.error("Encoding failed for video pk=%s: %s", video.pk, error_msg)
        return Response({"status": "error_recorded"})

    def _process_video_files(
        self, video: Video, client, task_id: str, file_list: list, thumbnail_path: str
    ):
        """Process files from the runner: keep/delete source, insert encoded formats, and update thumbnail."""
        if not encoding_settings.keep_source_file and video.video_file:
            video.video_file.delete(save=False)
            video.video_file = None

        for file_name in file_list:
            if file_name.endswith(".mp4"):
                res = (
                    file_name.split("_")[0]
                    if "_" in file_name
                    else file_name.split(".")[0]
                )
                # NOTE: Normalise resolution to always end with "p" (e.g. "360" → "360p").
                # This ensures EncodingVideo.resolution is stored as "360p", which is
                # the format expected by VideoViewSet._get_video_file_to_stream() after
                # the V4-compatibility normalisation applied in the stream action.
                if not res.endswith("p"):
                    res = f"{res}p"
                encoded_video_file = client.download_task_file_to_temp(task_id, file_name)

                encoding_obj, created = EncodingVideo.objects.get_or_create(
                    video=video, resolution=res
                )
                if not created and encoding_obj.file:
                    encoding_obj.file.delete(save=False)

                encoding_obj.file.save(
                    encoded_video_file.name, encoded_video_file, save=True
                )
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(encoded_video_file.file.name)

        if thumbnail_path:
            if video.overview:
                video.overview.delete(save=False)
            new_overview = client.download_task_file_to_temp(task_id, thumbnail_path)
            video.overview.save(new_overview.name, new_overview, save=False)
            with contextlib.suppress(FileNotFoundError):
                os.unlink(new_overview.file.name)
