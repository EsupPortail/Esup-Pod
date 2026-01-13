from typing import Dict, Any
from django.conf import settings
from django.contrib.auth import get_user_model
from ..core import SHIBBOLETH_ATTRIBUTE_MAP, REMOTE_USER_HEADER
from ..users import UserPopulator
from ..tokens import get_tokens_for_user

UserModel = get_user_model()


class ShibbolethService:
    def check_security(self, request) -> bool:
        """Verify request comes from a trusted source (SP) if configured."""
        secure_header = getattr(settings, "SHIB_SECURE_HEADER", None)
        if secure_header:
            return request.META.get(secure_header) == getattr(
                settings, "SHIB_SECURE_VALUE", "secure"
            )
        return True

    def get_header_value(self, request, header_name):
        return request.META.get(header_name, "")

    def process_request(self, request) -> Dict[str, Any]:
        """Process Shibboleth headers and return user tokens."""
        if not self.check_security(request):
            raise PermissionError("Insecure request. Missing security header.")

        username = self.get_header_value(request, REMOTE_USER_HEADER)
        if not username:
            raise ValueError(f"Missing {REMOTE_USER_HEADER} header.")

        user, created = UserModel.objects.get_or_create(username=username)

        # Extract attributes
        shib_meta = {}
        for header, (required, field) in SHIBBOLETH_ATTRIBUTE_MAP.items():
            value = self.get_header_value(request, header)
            if value:
                shib_meta[field] = value
                # Update basic user fields immediately if present
                if field in ["first_name", "last_name", "email"]:
                    setattr(user, field, value)

        user.save()
        # Use UserPopulator logic which seems more complete/centralized
        populator = UserPopulator(user)
        populator.run("Shibboleth", shib_meta)

        return get_tokens_for_user(user)
