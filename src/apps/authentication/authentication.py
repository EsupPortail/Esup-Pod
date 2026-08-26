"""Esup-Pod - Custom authentication backends."""

from rest_framework_simplejwt.authentication import JWTAuthentication


class QueryParameterJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that checks the 'token' query parameter
    if the Authorization header is not provided. Useful for HTML5 video
    streaming where setting headers in the <video> tag is not possible.
    """

    def authenticate(self, request):
        """Authenticate request using JWT token from header or query parameters."""
        # First try to authenticate using the standard header
        header_auth = super().authenticate(request)
        if header_auth is not None:
            return header_auth

        # If header authentication failed or wasn't provided, check query params
        token = request.query_params.get("token")
        if token:
            try:
                validated_token = self.get_validated_token(token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except Exception:
                pass

        return None
