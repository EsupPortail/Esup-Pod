import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema

from ..serializers.CustomTokenObtainPairSerializer import CustomTokenObtainPairSerializer
from ..serializers.CASTokenObtainPairSerializer import CASTokenObtainPairSerializer
from ..serializers.ExternalAuthSerializers import (
    OIDCTokenObtainSerializer,
    ShibbolethTokenObtainSerializer,
)
from ..services import ShibbolethService, OIDCService

logger = logging.getLogger(__name__)


class LoginView(TokenObtainPairView):
    """
    **Authentication Endpoint**
    Accepts a username and password and returns a pair of JWT tokens.
    """
    serializer_class = CustomTokenObtainPairSerializer


class CASLoginView(APIView):
    """
    **CAS Authentication Endpoint**
    Exchange a valid CAS ticket for a JWT token pair.
    """
    permission_classes = [AllowAny]
    serializer_class = CASTokenObtainPairSerializer

    @extend_schema(
        request=CASTokenObtainPairSerializer, responses=CASTokenObtainPairSerializer
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShibbolethLoginView(APIView):
    """
    **Shibboleth Authentication Endpoint**

    This view must be protected by the Shibboleth SP (Apache/Nginx)
    which injects the headers.
    It reads the headers (REMOTE_USER, etc.), creates or updates the user
    locally according to the logic defined in the ShibbolethService and returns JWTs.
    """
    permission_classes = [AllowAny]
    serializer_class = ShibbolethTokenObtainSerializer
    service = ShibbolethService()

    @extend_schema(request=ShibbolethTokenObtainSerializer)
    def get(self, request, *args, **kwargs):
        try:
            tokens = self.service.process_request(request)
            return Response(tokens, status=status.HTTP_200_OK)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response(
                {"error": f"{str(e)} Shibboleth misconfigured?"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            logger.error(f"Shibboleth Login failed: {e}")
            return Response(
                {"error": "Internal Server Error during Shibboleth login."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class OIDCLoginView(APIView):
    """
    **OIDC Authentication Endpoint**

    Exchanges an 'authorization_code' for OIDC tokens via the Provider,
    retrieves user information (UserInfo),
    updates the local database, and returns JWTs.
    """
    permission_classes = [AllowAny]
    serializer_class = OIDCTokenObtainSerializer
    service = OIDCService()

    @extend_schema(request=OIDCTokenObtainSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data["code"]
        redirect_uri = serializer.validated_data["redirect_uri"]

        try:
            tokens = self.service.process_code(code, redirect_uri)
            return Response(tokens, status=status.HTTP_200_OK)
        except EnvironmentError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ConnectionError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"OIDC Login failed: {e}")
            return Response(
                {"error": "Internal Server Error during OIDC login."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
