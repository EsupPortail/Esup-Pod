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
    description=(
        "Returns only the public configuration fields for each application. "
        "Fields are explicitly whitelisted using json_schema_extra={'public': True} "
        "in each app's conf.py. Sensitive parameters (API keys, LDAP settings, "
        "internal paths, etc.) are never exposed."
    ),
    responses={
        200: {
            "type": "object",
            "additionalProperties": {
                "type": "object",
            },
        }
    },
)
class ConfigInfoView(APIView):
    """
    Returns a JSON with the whitelisted public configuration fields for each app.

    Only fields explicitly marked with json_schema_extra={"public": True} in
    their Field() definition are included. All other fields are private by default,
    preventing accidental leakage of sensitive data such as API keys, LDAP
    credentials, or internal server paths.
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
                        # Whitelist approach: only expose fields explicitly
                        # marked with json_schema_extra={"public": True}
                        public_config = {}
                        for field_name, field_info in attr.model_fields.items():
                            extra = field_info.json_schema_extra or {}
                            if extra.get("public") is True:
                                public_config[field_name] = getattr(attr, field_name)

                        if public_config:
                            configurations[module_name] = public_config
                        break
            except (ImportError, AttributeError):
                # Skip apps without a conf.py or BaseSettings
                continue

        return Response(configurations)
