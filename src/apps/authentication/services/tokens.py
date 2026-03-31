"""
Esup-Pod - Authentication tokens service.
"""

from typing import Any, Dict


def get_tokens_for_user(user) -> Dict[str, Any]:
    """Generates a pair of JWT tokens for a given user."""
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    refresh["username"] = user.username
    refresh["is_staff"] = user.is_staff
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
            "affiliation": user.owner.affiliation if hasattr(user, "owner") else None,
        },
    }
