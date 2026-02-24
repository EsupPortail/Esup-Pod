from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from src.apps.authentication.conf import auth_settings
from src.apps.video.conf import video_settings


@extend_schema(
    summary="System Information",
    description="Returns the project name and current version",
    responses={
        200: {
            "type": "object",
            "properties": {
                "project": {"type": "string", "example": "POD V5"},
                "version": {"type": "string", "example": "5.0.0"},
            },
        }
    },
)
class SystemInfoView(APIView):
    """
    Simple view to return public system information,
    including the current version.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "project": "POD V5",
                "version": settings.POD_VERSION,
            }
        )


@extend_schema(
    summary="App Configuration Flags",
    description="Returns configuration flags (boolean values) for each application",
    responses={
        200: {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": {"type": "boolean"},
            },
        }
    },
)
class ConfigInfoView(APIView):
    """
    Returns a JSON with all configuration fields for each app.
    Fields are extracted from each app's pydantic settings.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "authentication": auth_settings.model_dump(mode="json"),
                "video": video_settings.model_dump(mode="json"),
            }
        )
