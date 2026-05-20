"""
Esup-Pod - OIDC authentication provider service.
"""

import logging
import requests

from ...conf import auth_settings
from config.env import env
from src.config.defaults import authentication as defaults
from ..tokens import get_tokens_for_user
from ..users import UserPopulator
from django.contrib.auth import get_user_model
from typing import Any, Dict

UserModel = get_user_model()
logger = logging.getLogger(__name__)


class OIDCService:
    """
    Handles OpenID Connect (OIDC) authentication flow, including code exchange
    and user profile population.
    """

    def process_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange OIDC code for tokens and populate user."""

        token_url = env("OIDC_OP_TOKEN_ENDPOINT", default=defaults.OIDC_OP_TOKEN_ENDPOINT)
        client_id = env("OIDC_RP_CLIENT_ID", default=defaults.OIDC_RP_CLIENT_ID)
        client_secret = env(
            "OIDC_RP_CLIENT_SECRET", default=defaults.OIDC_RP_CLIENT_SECRET
        )

        if not token_url:
            raise EnvironmentError("OIDC not configured (missing OIDC_OP_TOKEN_ENDPOINT)")

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            r_token = requests.post(token_url, data=payload)
            r_token.raise_for_status()
            tokens_oidc = r_token.json()
            access_token = tokens_oidc.get("access_token")
        except requests.exceptions.RequestException as e:
            logger.error("OIDC token exchange failed: %s", e, exc_info=True)
            raise ConnectionError("Failed to exchange OIDC code")

        userinfo_url = env(
            "OIDC_OP_USER_ENDPOINT", default=defaults.OIDC_OP_USER_ENDPOINT
        )
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            r_user = requests.get(userinfo_url, headers=headers)
            r_user.raise_for_status()
            claims = r_user.json()
        except requests.exceptions.RequestException as e:
            logger.error(
                "OIDC UserInfo request failed (endpoint: %s): %s",
                userinfo_url,
                e,
                exc_info=True,
            )
            raise ConnectionError("Failed to fetch OIDC user info")

        username = claims.get(auth_settings.oidc_claim_preferred_username)
        if not username:
            raise ValueError("Missing username in OIDC claims")

        user, created = UserModel.objects.get_or_create(username=username)

        # Populate user using centralized logic
        populator = UserPopulator(user)
        populator.run("OIDC", claims)

        return get_tokens_for_user(user)
