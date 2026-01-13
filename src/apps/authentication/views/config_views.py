from django.conf import settings
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer

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

        if getattr(settings, "USE_CAS", False) and get_cas_client:
            try:
                client = get_cas_client(service_url=request.build_absolute_uri("/"))
                data["cas"] = client.get_logout_url(
                    redirect_url=request.build_absolute_uri("/")
                )
            except Exception:
                pass

        if getattr(settings, "USE_SHIB", False):
            shib_logout = getattr(settings, "SHIB_LOGOUT_URL", "")
            if shib_logout:
                return_url = request.build_absolute_uri("/")
                data["shibboleth"] = f"{shib_logout}?return={return_url}"

        if getattr(settings, "USE_OIDC", False):
            oidc_logout = getattr(settings, "OIDC_OP_LOGOUT_ENDPOINT", "")
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
                "use_local": getattr(settings, "USE_LOCAL_AUTH", True),
                "use_cas": getattr(settings, "USE_CAS", False),
                "use_shibboleth": getattr(settings, "USE_SHIB", False),
                "use_oidc": getattr(settings, "USE_OIDC", False),
                "shibboleth_name": getattr(settings, "SHIB_NAME", "Shibboleth"),
                "oidc_name": getattr(settings, "OIDC_NAME", "OpenID Connect"),
            }
        )
