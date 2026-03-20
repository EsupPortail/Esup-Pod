"""
Esup-Pod - Authentication config API views.

Exposes authentication configuration to the frontend
so it knows which login buttons to display and logout URLs to use.
"""

import logging

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..conf import auth_settings

logger = logging.getLogger(__name__)

try:
    from django_cas_ng.utils import get_cas_client
except ImportError:
    get_cas_client = None


class LogoutInfoView(APIView):
    """
    Returns the logout URLs for external providers.
    The frontend must call this endpoint to know where
    to redirect the user after deleting the local JWT token.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        responses=inline_serializer(
            name="LogoutInfoResponse",
            fields={
                "local": serializers.CharField(allow_null=True),
                "cas": serializers.CharField(allow_null=True),
                "shibboleth": serializers.CharField(allow_null=True),
                "oidc": serializers.CharField(allow_null=True),
            },
        )
    )
    def get(self, request):
        data = {"local": None, "cas": None, "shibboleth": None, "oidc": None}

        if auth_settings.use_cas and get_cas_client:
            try:
                client = get_cas_client(service_url=request.build_absolute_uri("/"))
                data["cas"] = client.get_logout_url(
                    redirect_url=request.build_absolute_uri("/")
                )
            except Exception as e:
                logger.warning(
                    "Failed to build CAS logout URL: %s",
                    e,
                    exc_info=True,
                )

        if auth_settings.use_shib:
            # TODO: Add shib_logout_url to AuthConfig if needed
            shib_logout = ""
            if shib_logout:
                return_url = request.build_absolute_uri("/")
                data["shibboleth"] = f"{shib_logout}?return={return_url}"

        if auth_settings.use_oidc:
            # TODO: Add oidc_op_logout_endpoint to AuthConfig if needed
            oidc_logout = ""
            if oidc_logout:
                data["oidc"] = oidc_logout

        return Response(data)


class LoginConfigView(APIView):
    """
    Returns the configuration of active authentication methods.
    Allows the frontend to know which login buttons to display.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: inline_serializer(
                name="LoginConfigResponse",
                fields={
                    "use_local": serializers.BooleanField(),
                    "use_cas": serializers.BooleanField(),
                    "use_shibboleth": serializers.BooleanField(),
                    "use_oidc": serializers.BooleanField(),
                    "shibboleth_name": serializers.CharField(),
                    "oidc_name": serializers.CharField(),
                },
            )
        }
    )
    def get(self, request):
        return Response(
            {
                "use_local": auth_settings.use_local_auth,
                "use_cas": auth_settings.use_cas,
                "use_shibboleth": auth_settings.use_shib,
                "use_oidc": auth_settings.use_oidc,
                "shibboleth_name": "Shibboleth",
                "oidc_name": "OpenID Connect",
            }
        )
