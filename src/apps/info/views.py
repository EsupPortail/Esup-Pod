import importlib
import pkgutil

from django.conf import settings
from drf_spectacular.utils import extend_schema
from pydantic_settings import BaseSettings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from src import apps


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
        configurations = {}

        # Dynamically discover conf.py in each app in src.apps
        for loader, module_name, is_pkg in pkgutil.iter_modules(apps.__path__):
            try:
                # Try to import the conf module for the app
                conf_module_path = f"src.apps.{module_name}.conf"
                conf_mod = importlib.import_module(conf_module_path)

                # Look for an instance of BaseSettings in the module
                for attr_name in dir(conf_mod):
                    attr = getattr(conf_mod, attr_name)
                    if isinstance(attr, BaseSettings):
                        # Use model_dump to get only the declared fields
                        configurations[module_name] = attr.model_dump(mode="json")
                        break
            except (ImportError, AttributeError):
                # Skip apps without a conf.py or BaseSettings
                continue

        return Response(configurations)
