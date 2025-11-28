from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

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
        return Response({
            "project": "POD V5",
            "version": settings.POD_VERSION,
        })
