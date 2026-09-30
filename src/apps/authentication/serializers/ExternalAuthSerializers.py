"""
Esup-Pod - External authentication (OIDC/Shibboleth) serializers.
"""

from rest_framework import serializers


class OIDCTokenObtainSerializer(serializers.Serializer):
    """
    Serializer for OIDC code exchange. The frontend returns the 'code' received after redirection.
    """

    code = serializers.CharField(required=True)
    redirect_uri = serializers.CharField(
        required=True,
        help_text="The redirect URI used in the OIDC flow. It must match the one registered with the OIDC provider.",
    )


class ShibbolethTokenObtainSerializer(serializers.Serializer):
    """
    Empty serializer because Shibboleth uses HTTP headers. Used primarily for API documentation (Swagger).
    """

    pass
