import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django_cas_ng.utils import get_cas_client
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPBindError, LDAPSocketOpenError

from .models import Owner, AccessGroup
from .models.utils import AFFILIATION_STAFF, DEFAULT_AFFILIATION

UserModel = get_user_model()
logger = logging.getLogger(__name__)

# --- Configuration Constants ---

USER_LDAP_MAPPING_ATTRIBUTES = getattr(
    settings,
    "USER_LDAP_MAPPING_ATTRIBUTES",
    {
        "uid": "uid",
        "mail": "mail",
        "last_name": "sn",
        "first_name": "givenname",
        "primaryAffiliation": "eduPersonPrimaryAffiliation",
        "affiliations": "eduPersonAffiliation",
        "groups": "memberOf",
        "establishment": "establishment",
    },
)

AUTH_LDAP_USER_SEARCH = getattr(
    settings,
    "AUTH_LDAP_USER_SEARCH",
    ("ou=people,dc=univ,dc=fr", "(uid=%(uid)s)"),
)

GROUP_STAFF = AFFILIATION_STAFF


class UserPopulator:
    """
    Handles the population of User and Owner models from external sources (CAS, LDAP).
    """

    def __init__(self, user: Any):
        self.user = user
        # Ensure owner exists
        if not hasattr(self.user, "owner"):
            Owner.objects.create(user=self.user)
        self.owner = self.user.owner

    def run(self, source: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Main entry point to populate user data.
        :param source: 'CAS', 'LDAP', 'Shibboleth', or 'OIDC'
        :param attributes: Dictionary of attributes (from CAS, Shibboleth headers, or OIDC claims)
        """
        self.owner.auth_type = source
        self._delete_synchronized_access_groups()

        if source == "CAS" and attributes:
            self._populate_from_cas(attributes)
        elif source == "LDAP":
            self._populate_from_ldap()
        elif source == "Shibboleth" and attributes:
            self._populate_from_shibboleth(attributes)
        elif source == "OIDC" and attributes:
            self._populate_from_oidc(attributes)

        self.owner.save()
        self.user.save()

    def _delete_synchronized_access_groups(self) -> None:
        """Remove groups that are marked for auto-sync."""
        groups_to_sync = self.owner.accessgroups.filter(auto_sync=True)
        if groups_to_sync.exists():
            self.owner.accessgroups.remove(*groups_to_sync)

    def _populate_from_cas(self, attributes: Dict[str, Any]) -> None:
        """Map CAS attributes to User/Owner."""
        self.owner.affiliation = attributes.get(
            "primaryAffiliation", DEFAULT_AFFILIATION
        )

        # Handle affiliations list for group creation/staff status
        affiliations = attributes.get("affiliation", [])
        if isinstance(affiliations, str):
            affiliations = [affiliations]

        self._process_affiliations(affiliations)

        # Handle explicit groups
        groups = attributes.get("groups", [])
        if isinstance(groups, str):
            groups = [groups]
        self._assign_access_groups(groups)

    def _populate_from_shibboleth(self, attributes: Dict[str, Any]) -> None:
        """Map Shibboleth attributes to User/Owner."""
        # attributes keys are our internal field names (e.g. 'affiliation', 'first_name')
        # because the view maps headers to these names before calling this.

        if "first_name" in attributes:
            self.user.first_name = attributes["first_name"]
        if "last_name" in attributes:
            self.user.last_name = attributes["last_name"]
        if "email" in attributes:
            self.user.email = attributes["email"]

        self.owner.affiliation = attributes.get("affiliation", DEFAULT_AFFILIATION)

        affiliations = attributes.get("affiliations", [])
        if isinstance(affiliations, str):
            # Shibboleth usually sends semicolon separated values or similar,
            # but here logic expects list or pre-split string.
            # The view should handle splitting if needed or we do it here?
            # Existing view logic: shib_meta.get("affiliations", "") then .split(";") later.
            # Let's assume input is cleaned or we handle it.
            # To be safe, let's say attributes['affiliations'] is the raw string from map.
            if ";" in affiliations:
                affiliations = affiliations.split(";")
            else:
                affiliations = [affiliations]

        self._process_affiliations(affiliations)

    def _populate_from_oidc(self, attributes: Dict[str, Any]) -> None:
        """Map OIDC claims to User/Owner."""
        # attributes are the OIDC claims

        # Mapping should use settings headers ideally, but here passed attributes
        # are raw claims.
        # Logic from view:
        # Puts specific claims into user fields.

        # OIDC_CLAIM_* constants are in view/settings.
        # To avoid circular imports or redefining, we accept that 'attributes' might be
        # a normalized dict OR we access settings here.
        # Let's assume the View passes a normalized dict or we use settings.

        # Actually, let's import the constants or use getattr(settings, ...)
        given_name_claim = getattr(settings, "OIDC_CLAIM_GIVEN_NAME", "given_name")
        family_name_claim = getattr(settings, "OIDC_CLAIM_FAMILY_NAME", "family_name")

        self.user.first_name = attributes.get(given_name_claim, self.user.first_name)
        self.user.last_name = attributes.get(family_name_claim, self.user.last_name)
        self.user.email = attributes.get("email", self.user.email)

        self.owner.affiliation = getattr(
            settings, "OIDC_DEFAULT_AFFILIATION", DEFAULT_AFFILIATION
        )

        # OIDC default access groups
        oidc_groups = getattr(settings, "OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES", [])
        self._assign_access_groups(oidc_groups)

        # Is user staff?
        if self.owner.affiliation in AFFILIATION_STAFF:
            self.user.is_staff = True

    def _populate_from_ldap(self) -> None:
        """Fetch and map LDAP attributes to User/Owner."""
        if not self._is_ldap_configured():
            return

        conn = get_ldap_conn()
        if not conn:
            return

        entry = get_ldap_entry(conn, self.user.username)
        if entry:
            self._apply_ldap_entry(entry)

    def _apply_ldap_entry(self, entry: Any) -> None:
        self.user.email = self._get_ldap_value(entry, "mail", "")
        self.user.first_name = self._get_ldap_value(entry, "first_name", "")
        self.user.last_name = self._get_ldap_value(entry, "last_name", "")
        self.user.save()

        self.owner.affiliation = self._get_ldap_value(
            entry, "primaryAffiliation", DEFAULT_AFFILIATION
        )
        self.owner.establishment = self._get_ldap_value(entry, "establishment", "")
        self.owner.save()

        affiliations = self._get_ldap_value(entry, "affiliations", [])
        if isinstance(affiliations, str):
            affiliations = [affiliations]
        self._process_affiliations(affiliations)

        # Groups from LDAP
        ldap_group_attr = USER_LDAP_MAPPING_ATTRIBUTES.get("groups")
        groups_element = []
        if ldap_group_attr and entry[ldap_group_attr]:
            groups_element = entry[ldap_group_attr].values

        self._assign_access_groups(groups_element)

    def _process_affiliations(self, affiliations: List[str]) -> None:
        """Process list of affiliations to set staff status and create AccessGroups."""
        create_group_from_aff = getattr(
            settings, "CREATE_GROUP_FROM_AFFILIATION", False
        )
        current_site = Site.objects.get_current()

        for affiliation in affiliations:
            if affiliation in AFFILIATION_STAFF:
                self.user.is_staff = True

            if create_group_from_aff:
                accessgroup, created = AccessGroup.objects.get_or_create(
                    code_name=affiliation
                )
                if created:
                    accessgroup.display_name = affiliation
                    accessgroup.auto_sync = True
                    accessgroup.save()

                accessgroup.sites.add(current_site)
                self.owner.accessgroups.add(accessgroup)

    def _assign_access_groups(self, groups: List[str]) -> None:
        """Assign AccessGroups based on group codes."""
        create_group_from_groups = getattr(settings, "CREATE_GROUP_FROM_GROUPS", False)
        current_site = Site.objects.get_current()

        for group_code in groups:
            if group_code in GROUP_STAFF:
                self.user.is_staff = True

            if create_group_from_groups:
                accessgroup, created = AccessGroup.objects.get_or_create(
                    code_name=group_code
                )
                if created:
                    accessgroup.display_name = group_code
                    accessgroup.auto_sync = True
                    accessgroup.save()
                accessgroup.sites.add(current_site)
                self.owner.accessgroups.add(accessgroup)
            else:
                try:
                    accessgroup = AccessGroup.objects.get(code_name=group_code)
                    self.owner.accessgroups.add(accessgroup)
                except ObjectDoesNotExist:
                    pass

    def _get_ldap_value(self, entry: Any, attribute: str, default: Any) -> Any:
        mapping = USER_LDAP_MAPPING_ATTRIBUTES.get(attribute)
        if mapping and entry[mapping]:
            if attribute == "last_name" and isinstance(entry[mapping].value, list):
                return entry[mapping].value[0]
            elif attribute == "affiliations":
                return entry[mapping].values
            else:
                return entry[mapping].value
        return default

    @staticmethod
    def _is_ldap_configured() -> bool:
        ldap_config = getattr(settings, "LDAP_SERVER", {})
        return bool(ldap_config.get("url"))


# --- Public Interface ---


def get_tokens_for_user(user) -> Dict[str, Any]:
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


def verify_cas_ticket(ticket: str, service_url: str) -> Optional[User]:
    """
    Verifies the CAS service ticket using django-cas-ng utils.
    Then populates user using UserPopulator.
    """
    client = get_cas_client(service_url=service_url)
    username, attributes, _ = client.verify_ticket(ticket)

    if not username:
        logger.warning("CAS ticket validation failed")
        return None

    if getattr(settings, "CAS_FORCE_CHANGE_USERNAME_CASE", "lower") == "lower":
        username = username.lower()

    user, created = UserModel.objects.get_or_create(username=username)

    if created:
        user.set_unusable_password()
        user.save()

    # Determine usage strategy
    populate_strategy = getattr(settings, "POPULATE_USER", None)

    populator = UserPopulator(user)

    if populate_strategy == "CAS":
        populator.run("CAS", attributes)
    elif populate_strategy == "LDAP":
        populator.run("LDAP")
    else:
        # Minimal init if no external source strategy selected
        pass

    return user


def populate_user_from_cas(
    user: User, owner: Owner, attributes: Dict[str, Any]
) -> None:
    """
    Strict implementation of populatedCASbackend.populateUserFromCAS
    """
    owner.affiliation = attributes.get("primaryAffiliation", DEFAULT_AFFILIATION)

    if "affiliation" in attributes:
        affiliations = attributes["affiliation"]
        if isinstance(affiliations, str):
            affiliations = [affiliations]

        create_group_from_aff = getattr(
            settings, "CREATE_GROUP_FROM_AFFILIATION", False
        )

        for affiliation in affiliations:
            if affiliation in AFFILIATION_STAFF:
                user.is_staff = True

            if create_group_from_aff:
                accessgroup, group_created = AccessGroup.objects.get_or_create(
                    code_name=affiliation
                )
                if group_created:
                    accessgroup.display_name = affiliation
                    accessgroup.auto_sync = True
                accessgroup.sites.add(Site.objects.get_current())
                accessgroup.save()
                owner.accessgroups.add(accessgroup)

    if "groups" in attributes:
        groups = attributes["groups"]
        if isinstance(groups, str):
            groups = [groups]
        assign_accessgroups(groups, user)


def populate_user_from_ldap(user: User, owner: Owner) -> None:
    """
    Strict implementation of populatedCASbackend.populateUserFromLDAP
    """
    list_value = []
    for val in USER_LDAP_MAPPING_ATTRIBUTES.values():
        list_value.append(str(val))

    conn = get_ldap_conn()
    if conn:
        entry = get_ldap_entry(conn, user.username, list_value)
        if entry:
            _apply_ldap_entry_to_user(user, owner, entry)


def _apply_ldap_entry_to_user(user, owner, entry):
    """
    Internal helper to map LDAP entry to User/Owner object
    (formerly populate_user_from_entry in populatedCASbackend.py)
    """
    user.email = get_entry_value(entry, "mail", "")
    user.first_name = get_entry_value(entry, "first_name", "")
    user.last_name = get_entry_value(entry, "last_name", "")
    user.save()

    owner.affiliation = get_entry_value(
        entry, "primaryAffiliation", DEFAULT_AFFILIATION
    )
    owner.establishment = get_entry_value(entry, "establishment", "")
    owner.save()

    affiliations = get_entry_value(entry, attribute="affiliations", default=[])
    if isinstance(affiliations, str):
        affiliations = [affiliations]

    create_group_from_aff = getattr(settings, "CREATE_GROUP_FROM_AFFILIATION", False)

    for affiliation in affiliations:
        if affiliation in AFFILIATION_STAFF:
            user.is_staff = True

        if create_group_from_aff:
            accessgroup, group_created = AccessGroup.objects.get_or_create(
                code_name=affiliation
            )
            if group_created:
                accessgroup.display_name = affiliation
                accessgroup.auto_sync = True
            accessgroup.sites.add(Site.objects.get_current())
            accessgroup.save()
            owner.accessgroups.add(accessgroup)

    groups_element = []
    ldap_group_attr = USER_LDAP_MAPPING_ATTRIBUTES.get("groups")

    if ldap_group_attr and entry[ldap_group_attr]:
        groups_element = entry[ldap_group_attr].values

    assign_accessgroups(groups_element, user)


def assign_accessgroups(groups_element, user) -> None:
    """
    Strict implementation of assign_accessgroups
    """
    create_group_from_groups = getattr(settings, "CREATE_GROUP_FROM_GROUPS", False)

    for group in groups_element:
        if group in GROUP_STAFF:
            user.is_staff = True

        if create_group_from_groups:
            accessgroup, group_created = AccessGroup.objects.get_or_create(
                code_name=group
            )
            if group_created:
                accessgroup.display_name = group
                accessgroup.auto_sync = True
            accessgroup.sites.add(Site.objects.get_current())
            accessgroup.save()
            user.owner.accessgroups.add(accessgroup)
        else:
            try:
                accessgroup = AccessGroup.objects.get(code_name=group)
                user.owner.accessgroups.add(accessgroup)
            except ObjectDoesNotExist:
                pass


def delete_synchronized_access_group(owner) -> None:
    """Delete synchronized access groups."""
    groups_to_sync = AccessGroup.objects.filter(auto_sync=True)
    for group_to_sync in groups_to_sync:
        owner.accessgroups.remove(group_to_sync)


def get_entry_value(entry, attribute, default):
    """Retrieve the value of the given attribute from the LDAP entry."""
    mapping = USER_LDAP_MAPPING_ATTRIBUTES.get(attribute)
    if mapping and entry[mapping]:
        if attribute == "last_name" and isinstance(entry[mapping].value, list):
            return entry[mapping].value[0]
        elif attribute == "affiliations":
            return entry[mapping].values
        else:
            return entry[mapping].value
    return default


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
