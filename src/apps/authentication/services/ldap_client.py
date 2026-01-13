import logging
from typing import Optional, Any
from django.conf import settings
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError

from .core import USER_LDAP_MAPPING_ATTRIBUTES, AUTH_LDAP_USER_SEARCH

logger = logging.getLogger(__name__)

def get_ldap_conn():
    """Open and get LDAP connexion."""
    ldap_server_conf = getattr(settings, "LDAP_SERVER", {})
    auth_bind_dn = getattr(settings, "AUTH_LDAP_BIND_DN", "")
    auth_bind_pwd = getattr(settings, "AUTH_LDAP_BIND_PASSWORD", "")

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
        logger.error(f"LDAP Connection Error: {err}")
        return None
    return None


def get_ldap_entry(conn: Connection, username: str) -> Optional[Any]:
    """Get LDAP entry for a specific username."""
    # Build list of attributes to fetch
    attributes_to_fetch = list(USER_LDAP_MAPPING_ATTRIBUTES.values())

    try:
        search_filter = AUTH_LDAP_USER_SEARCH[1] % {"uid": username}
        conn.search(
            AUTH_LDAP_USER_SEARCH[0],
            search_filter,
            search_scope=SUBTREE,
            attributes=attributes_to_fetch,
            size_limit=1,
        )
        return conn.entries[0] if len(conn.entries) > 0 else None
    except Exception as err:
        logger.error(f"LDAP Search Error: {err}")
        return None
