"""
Esup-Pod - Authentication configuration.

Typed and validated configuration for the authentication app using pydantic-settings.
"""

from typing import Dict, List, Optional, Tuple, Type

from django.utils.translation import gettext_lazy as _


from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from src.apps.utils.conf import DjangoSettingsSource
from src.config.defaults import authentication as defaults


class AuthConfig(BaseSettings):
    """Authentication configuration with typed fields and validation."""

    # --- Feature Flags ---
    use_local_auth: bool = Field(
        default=defaults.USE_LOCAL_AUTH,
        description=_("Enable local Django authentication (username/password)."),
        json_schema_extra={"public": True},
    )
    use_cas: bool = Field(
        default=defaults.USE_CAS,
        description=_("Enable CAS (Central Authentication Service)."),
        json_schema_extra={"public": True},
    )
    use_ldap: bool = Field(
        default=defaults.USE_LDAP,
        description=_("Enable LDAP user lookup for populating user attributes."),
        json_schema_extra={"public": True},
    )
    use_shib: bool = Field(
        default=defaults.USE_SHIB,
        description=_("Enable Shibboleth authentication."),
        json_schema_extra={"public": True},
    )
    use_oidc: bool = Field(
        default=defaults.USE_OIDC,
        description=_("Enable OpenID Connect authentication."),
        json_schema_extra={"public": True},
    )

    # --- CAS Configuration ---
    cas_version: str = Field(
        default=defaults.CAS_VERSION,
        description=_("CAS protocol version."),
    )
    cas_force_change_username_case: str = Field(
        default=defaults.CAS_FORCE_CHANGE_USERNAME_CASE,
        description=_("Force CAS username case: 'lower', 'upper', or 'False'."),
    )
    cas_apply_attributes_to_user: bool = Field(
        default=defaults.CAS_APPLY_ATTRIBUTES_TO_USER,
        description=_("Apply CAS attributes directly to the Django user model."),
    )
    cas_admin_redirect: bool = Field(
        default=defaults.CAS_ADMIN_REDIRECT,
        description=_("Redirect admin login to CAS."),
    )

    # --- LDAP Configuration ---
    ldap_server_use_ssl: bool = Field(
        default=defaults.LDAP_SERVER_USE_SSL,
        description=_("Use SSL for LDAP connection."),
    )
    ldap_user_search_base: str = Field(
        default=defaults.LDAP_USER_SEARCH_BASE,
        description=_("LDAP search base for users."),
    )
    ldap_user_search_filter: str = Field(
        default=defaults.LDAP_USER_SEARCH_FILTER,
        description=_("LDAP search filter for users."),
    )
    ldap_mapping_attributes: Dict[str, str] = Field(
        default=defaults.LDAP_MAPPING_ATTRIBUTES,
        description=_("Mapping from internal user fields to LDAP attributes."),
    )

    # --- OIDC Configuration ---
    oidc_claim_given_name: str = Field(
        default=defaults.OIDC_CLAIM_GIVEN_NAME,
        description=_("OIDC claim for given name."),
    )
    oidc_claim_family_name: str = Field(
        default=defaults.OIDC_CLAIM_FAMILY_NAME,
        description=_("OIDC claim for family name."),
    )
    oidc_claim_preferred_username: str = Field(
        default=defaults.OIDC_CLAIM_PREFERRED_USERNAME,
        description=_("OIDC claim for preferred username."),
    )
    oidc_default_affiliation: str = Field(
        default=defaults.OIDC_DEFAULT_AFFILIATION,
        description=_("Default affiliation for OIDC-authenticated users."),
    )
    oidc_default_access_group_code_names: List[str] = Field(
        default=defaults.OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES,
        description=_("Default access groups for OIDC-authenticated users."),
    )
    oidc_name: str = Field(
        default=defaults.OIDC_NAME,
        description=_("Display name for OIDC login."),
        json_schema_extra={"public": True},
    )

    # --- Shibboleth Configuration ---
    shibboleth_staff_allowed_domains: Optional[List[str]] = Field(
        default=defaults.SHIBBOLETH_STAFF_ALLOWED_DOMAINS,
        description=_("Domains allowed for Shibboleth staff users."),
    )
    shibboleth_name: str = Field(
        default=defaults.SHIB_NAME,
        description=_("Display name for Shibboleth login."),
        json_schema_extra={"public": True},
    )
    shib_secure_header: Optional[str] = Field(
        default=defaults.SHIB_SECURE_HEADER,
        description=_(
            "HTTP header to check for Shibboleth security (e.g., HTTP_X_SHIB_SECURE)."
        ),
    )
    shib_secure_value: str = Field(
        default=defaults.SHIB_SECURE_VALUE,
        description=_("Value expected in shib_secure_header."),
    )
    shibboleth_attribute_map: Dict[str, Tuple[bool, str]] = Field(
        default=defaults.SHIBBOLETH_ATTRIBUTE_MAP,
        description=_("Mapping from Shibboleth headers to user fields."),
    )

    # --- Group / Affiliation ---
    affiliation_staff: Tuple[str, ...] = Field(
        default=defaults.AFFILIATION_STAFF,
        description=_("Affiliations that grant staff status."),
    )
    create_group_from_affiliation: bool = Field(
        default=defaults.CREATE_GROUP_FROM_AFFILIATION,
        description=_("Auto-create access groups from user affiliations."),
    )
    create_group_from_groups: bool = Field(
        default=defaults.CREATE_GROUP_FROM_GROUPS,
        description=_("Auto-create groups from LDAP/CAS group attributes."),
    )

    # --- UI ---
    hide_username: bool = Field(
        default=defaults.HIDE_USERNAME,
        description=_("Hide usernames on the platform (GDPR compliance)."),
        json_schema_extra={"public": True},
    )
    use_establishment_field: bool = Field(
        default=defaults.USE_ESTABLISHMENT_FIELD,
        description=_("Add an establishment attribute to users."),
        json_schema_extra={"public": True},
    )
    default_affiliation: str = Field(
        default=defaults.DEFAULT_AFFILIATION,
        description=_("Default affiliation code for new users/owners."),
    )
    default_establishment: str = Field(
        default=defaults.DEFAULT_ESTABLISHMENT,
        description=_("Default establishment code for new users/owners."),
    )

    # --- Remote User ---
    remote_user_header: str = Field(
        default=defaults.REMOTE_USER_HEADER,
        description=_("HTTP header containing the remote username."),
    )

    # --- Security ---
    allowed_superuser_ips: List[str] = Field(
        default=defaults.ALLOWED_SUPERUSER_IPS,
        description=_("Allowed IP ranges for superuser access."),
    )

    @property
    def populate_user(self) -> Optional[str]:
        """Determine user population strategy based on active flags."""
        if self.use_cas:
            return "CAS"
        if self.use_ldap:
            return "LDAP"
        return None

    @property
    def ldap_server(self) -> dict:
        """Build the LDAP server configuration dict."""
        from config.env import env

        return {
            "url": env("LDAP_SERVER_URL", default=defaults.LDAP_SERVER_URL),
            "port": env.int("LDAP_SERVER_PORT", default=defaults.LDAP_SERVER_PORT),
            "use_ssl": self.ldap_server_use_ssl,
        }

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """
        Add DjangoSettingsSource to priority list.
        Order: Init > Env > Django Settings > DotEnv > Secrets > Defaults
        """
        return (
            init_settings,
            env_settings,
            DjangoSettingsSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )


# Singleton instance
auth_settings = AuthConfig()
