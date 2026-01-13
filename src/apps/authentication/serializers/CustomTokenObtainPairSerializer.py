from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from typing import Dict, Any


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT Token Serializer.

    Extends the default SimpleJWT serializer to include custom claims
    in the encrypted token payload (username, staff status, affiliation).
    """

    @classmethod
    def get_token(cls, user) -> Any:
        token = super().get_token(user)
        token["username"] = user.username
        token["is_staff"] = user.is_staff
        if hasattr(user, "owner"):
            token["affiliation"] = user.owner.affiliation

        return token

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adds extra responses to the JSON response body (not just inside the token).
        """
        data = super().validate(attrs)

        data["username"] = self.user.username
        data["email"] = self.user.email
        data["is_staff"] = self.user.is_staff

        if hasattr(self.user, "owner"):
            data["affiliation"] = self.user.owner.affiliation
        return data
