"""
Esup-Pod - CAS token obtain pair serializer.
"""

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from ..services import verify_cas_ticket


class CASTokenObtainPairSerializer(serializers.Serializer):
    """
    Serializer to exchange a CAS ticket for a JWT access/refresh token pair.
    """

    ticket = serializers.CharField()
    service = serializers.CharField()

    def validate(self, attrs):
        """Validates the CAS ticket and returns the token payload."""
        ticket = attrs.get("ticket")
        service = attrs.get("service")
        user = verify_cas_ticket(ticket, service)

        if user is None:
            raise serializers.ValidationError(
                _("Authentication failed: Invalid CAS ticket or user creation error.")
            )

        if not user.is_active:
            raise serializers.ValidationError(_("User account is disabled."))

        refresh = RefreshToken.for_user(user)

        refresh["username"] = user.username
        if hasattr(user, "owner"):
            refresh["affiliation"] = user.owner.affiliation

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "affiliation": (
                    user.owner.affiliation if hasattr(user, "owner") else None
                ),
            },
        }
