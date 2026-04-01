"""
Esup-Pod - LDAP client service.
"""

import logging

from typing import Any, Optional
from ..conf import auth_settings
from config.env import env
from src.config.defaults import authentication as defaults
from ldap3 import ALL, SUBTREE, Connection, Server
from ldap3.core.exceptions import LDAPBindError, LDAPException, LDAPSocketOpenError

logger = logging.getLogger(__name__)


def get_ldap_conn():
    """Open and get LDAP connexion."""

    ldap_server_conf = auth_settings.ldap_server
    auth_bind_dn = env("LDAP_BIND_DN", default=defaults.LDAP_BIND_DN)
    auth_bind_pwd = env("LDAP_BIND_PASSWORD", default=defaults.LDAP_BIND_PASSWORD)

    url = ldap_server_conf.get("url")
    if not url:
        return None

    try:
        server = None
        if isinstance(url, str):
            server = Server(
                url,
                port=ldap_server_conf.get("port", 389),
                use_ssl=ldap_server_conf.get("use_ssl", False),
                get_info=ALL,
            )
        elif isinstance(url, tuple) or isinstance(url, list):
            server = Server(
                url[0],
                port=ldap_server_conf.get("port", 389),
                use_ssl=ldap_server_conf.get("use_ssl", False),
                get_info=ALL,
            )

        if server:
            return Connection(server, auth_bind_dn, auth_bind_pwd, auto_bind=True)

    except (LDAPBindError, LDAPSocketOpenError) as err:
        logger.error("LDAP connection error: %s", err, exc_info=True)
        return None
    return None


def get_ldap_entry(conn: Connection, username: str) -> Optional[Any]:
    """Get LDAP entry for a specific username."""
    attributes_to_fetch = list(auth_settings.ldap_mapping_attributes.values())

    try:
        search_filter = auth_settings.ldap_user_search_filter % {"uid": username}
        conn.search(
            auth_settings.ldap_user_search_base,
            search_filter,
            search_scope=SUBTREE,
            attributes=attributes_to_fetch,
            size_limit=1,
        )
        return conn.entries[0] if len(conn.entries) > 0 else None
    except (LDAPException, KeyError) as err:
        logger.error("LDAP search error for user %r: %s", username, err, exc_info=True)
        return None
