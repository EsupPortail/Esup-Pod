"""
Esup-Pod - Info app API views.
"""

import importlib
import logging
import pkgutil

from django.conf import settings
from drf_spectacular.utils import extend_schema
from pydantic_settings import BaseSettings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from src import apps

logger = logging.getLogger(__name__)


@extend_schema(
    summary="System Information",
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
        """
        Return the project name and current version.
        """
        return Response(
            {
                "project": settings.POD_PROJECT_NAME,
                "version": settings.POD_VERSION,
            }
        )


@extend_schema(
    summary="App Configuration Flags",
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

    @staticmethod
    def _get_public_config(settings_instance: BaseSettings) -> dict:
        """
        Extract only the fields explicitly marked as public from a BaseSettings instance.
        Returns an empty dict if no public fields are found.
        """
        public_config = {}
        for field_name, field_info in settings_instance.model_fields.items():
            extra = field_info.json_schema_extra or {}
            if extra.get("public") is True:
                public_config[field_name] = getattr(settings_instance, field_name)
        return public_config

    @staticmethod
    def _load_app_conf(module_name: str) -> dict:
        """
        Import an app's conf module and return its public configuration dict.
        Returns an empty dict if no conf module or BaseSettings instance is found.
        """
        conf_module_path = f"src.apps.{module_name}.conf"
        try:
            conf_mod = importlib.import_module(conf_module_path)
        except ImportError:
            logger.debug("App %r has no conf module, skipping.", module_name)
            return {}
        except AttributeError as e:
            logger.debug(
                "App %r conf module has an unexpected structure: %s",
                module_name,
                e,
            )
            return {}

        for attr_name in dir(conf_mod):
            attr = getattr(conf_mod, attr_name)
            if isinstance(attr, BaseSettings):
                return ConfigInfoView._get_public_config(attr)

        return {}

    def get(self, request):
        """
        Aggregate and return public configuration flags for all applications.
        """
        configurations = {}

        for _loader, module_name, _is_pkg in pkgutil.iter_modules(apps.__path__):
            public_config = self._load_app_conf(module_name)
            if public_config:
                configurations[module_name] = public_config

        return Response(configurations)
