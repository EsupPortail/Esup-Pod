import logging
from typing import Any, Dict

import requests
from ...conf import auth_settings

from django.contrib.auth import get_user_model

from ..core import OIDC_CLAIM_PREFERRED_USERNAME
from ..tokens import get_tokens_for_user
from ..users import UserPopulator

UserModel = get_user_model()
logger = logging.getLogger(__name__)


class OIDCService:
    def process_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange OIDC code for tokens and populate user."""

        token_url = auth_settings.oidc_op_token_endpoint
        client_id = auth_settings.oidc_rp_client_id
        client_secret = auth_settings.oidc_rp_client_secret.get_secret_value()

        if not token_url:
            raise EnvironmentError(
                "OIDC not configured (missing OIDC_OP_TOKEN_ENDPOINT)"
            )

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
        except Exception as e:
            logger.error(f"OIDC Token Exchange failed: {e}")
            raise ConnectionError("Failed to exchange OIDC code")

        userinfo_url = auth_settings.oidc_op_user_endpoint
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            r_user = requests.get(userinfo_url, headers=headers)
            r_user.raise_for_status()
            claims = r_user.json()
        except Exception as e:
            logger.error(f"OIDC UserInfo failed: {e}")

            # Additional logging for debugging
            logger.error(f"OIDC UserInfo Endpoint: {userinfo_url}")

            raise ConnectionError("Failed to fetch OIDC user info")

        username = claims.get(OIDC_CLAIM_PREFERRED_USERNAME)
        if not username:
            raise ValueError("Missing username in OIDC claims")

        user, created = UserModel.objects.get_or_create(username=username)

        # Populate user using centralized logic
        populator = UserPopulator(user)
        populator.run("OIDC", claims)

        return get_tokens_for_user(user)
