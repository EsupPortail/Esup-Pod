"""
Esup-Pod - Shibboleth authentication provider service.
"""

from typing import Any, Dict
from ...conf import auth_settings
from django.contrib.auth import get_user_model
from ..tokens import get_tokens_for_user
from ..users import UserPopulator

UserModel = get_user_model()


class ShibbolethService:
    """
    Handles Shibboleth authentication flow by extracting user attributes
    from HTTP headers provided by the Service Provider (SP).
    """

    def check_security(self, request) -> bool:
        """Verify request comes from a trusted source (SP) if configured."""
        secure_header = auth_settings.shib_secure_header
        if secure_header:
            header_name = secure_header.upper().replace("-", "_")
            if not header_name.startswith("HTTP_"):
                header_name = f"HTTP_{header_name}"
            return request.META.get(header_name) == auth_settings.shib_secure_value
        return True

    def get_header_value(self, request, header_name):
        """Safely retrieves a value from request.META headers."""
        return request.META.get(header_name, "")

    def process_request(self, request) -> Dict[str, Any]:
        """Process Shibboleth headers and return user tokens."""
        if not self.check_security(request):
            raise PermissionError("Insecure request. Missing security header.")

        username = self.get_header_value(request, auth_settings.remote_user_header)
        if not username:
            raise ValueError(f"Missing {auth_settings.remote_user_header} header.")

        user, created = UserModel.objects.get_or_create(username=username)

        # Extract attributes
        shib_meta = {}
        for header, (required, field) in auth_settings.shibboleth_attribute_map.items():
            value = self.get_header_value(request, header)
            if value:
                shib_meta[field] = value
                # Update basic user fields immediately if present
                if field in ["first_name", "last_name", "email"]:
                    setattr(user, field, value)

        user.save()
        populator = UserPopulator(user)
        populator.run("Shibboleth", shib_meta)

        return get_tokens_for_user(user)
