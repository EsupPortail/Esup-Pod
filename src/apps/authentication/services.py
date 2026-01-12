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
from .models.utils import AFFILIATION, AFFILIATION_STAFF, DEFAULT_AFFILIATION, AUTH_TYPE

UserModel = get_user_model()
logger = logging.getLogger(__name__)

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

def verify_cas_ticket(ticket: str, service_url: str) -> Optional[User]:
    """
    Verifies the CAS service ticket using django-cas-ng utils.
    Then triggers the exact same population logic as the old backend.
    """
    client = get_cas_client(service_url=service_url)
    username, attributes, _ = client.verify_ticket(ticket)

    if not username:
        logger.warning("CAS ticket validation failed")
        return None

    if getattr(settings, 'CAS_FORCE_CHANGE_USERNAME_CASE', 'lower') == 'lower':
        username = username.lower()

    user, created = UserModel.objects.get_or_create(username=username)
    
    if created:
        user.set_unusable_password()
        user.save()

    if not hasattr(user, 'owner'):
        Owner.objects.create(user=user)

    populate_user(user, attributes)

    return user

def populate_user(user: User, cas_attributes: Optional[Dict[str, Any]]) -> None:
    """
    Strict implementation of populatedCASbackend.populateUser
    """
    owner = user.owner
    owner.auth_type = "CAS"
    
    delete_synchronized_access_group(owner)

    populate_strategy = getattr(settings, "POPULATE_USER", None)

    if populate_strategy == "CAS" and cas_attributes:
        populate_user_from_cas(user, owner, cas_attributes)
    
    if populate_strategy == "LDAP": 
        ldap_config = getattr(settings, "LDAP_SERVER", {})
        if ldap_config.get("url"):
            populate_user_from_ldap(user, owner)

    owner.save()
    user.save()


def populate_user_from_cas(
    user: User, owner: Owner, attributes: Dict[str, Any]
) -> None:
    """
    Strict implementation of populatedCASbackend.populateUserFromCAS
    """
    owner.affiliation = attributes.get('primaryAffiliation', DEFAULT_AFFILIATION)

    if 'affiliation' in attributes:
        affiliations = attributes['affiliation']
        if isinstance(affiliations, str):
            affiliations = [affiliations]
            
        create_group_from_aff = getattr(settings, "CREATE_GROUP_FROM_AFFILIATION", False)
        
        for affiliation in affiliations:
            if affiliation in AFFILIATION_STAFF:
                user.is_staff = True
            
            if create_group_from_aff:
                accessgroup, group_created = (
                    AccessGroup.objects.get_or_create(code_name=affiliation)
                )
                if group_created:
                    accessgroup.display_name = affiliation
                    accessgroup.auto_sync = True
                accessgroup.sites.add(Site.objects.get_current())
                accessgroup.save()
                owner.accessgroups.add(accessgroup)

    if 'groups' in attributes:
        groups = attributes['groups']
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

    owner.affiliation = get_entry_value(entry, "primaryAffiliation", DEFAULT_AFFILIATION)
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
            accessgroup, group_created = AccessGroup.objects.get_or_create(code_name=affiliation)
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
            accessgroup, group_created = AccessGroup.objects.get_or_create(code_name=group)
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
    
    if not ldap_server_conf.get("url"):
        return None

    try:
        url = ldap_server_conf["url"]
        server = None
        if isinstance(url, str):
            server = Server(
                url,
                port=ldap_server_conf.get("port", 389),
                use_ssl=ldap_server_conf.get("use_ssl", False),
                get_info=ALL
            )
        elif isinstance(url, tuple) or isinstance(url, list):
            server = Server(
                url[0],
                port=ldap_server_conf.get("port", 389),
                use_ssl=ldap_server_conf.get("use_ssl", False),
                get_info=ALL
            )

        if server:
            conn = Connection(server, auth_bind_dn, auth_bind_pwd, auto_bind=True)
            return conn
            
    except (LDAPBindError, LDAPSocketOpenError) as err:
        logger.error(f"LDAP Connection Error: {err}")
        return None
    return None

def get_ldap_entry(conn, username, list_value):
    """Get LDAP entries."""
    try:
        search_filter = AUTH_LDAP_USER_SEARCH[1] % {"uid": username}
        conn.search(
            AUTH_LDAP_USER_SEARCH[0],
            search_filter,
            search_scope=SUBTREE,
            attributes=list_value,
            size_limit=1,
        )
        return conn.entries[0] if len(conn.entries) > 0 else None
    except Exception as err:
        logger.error(f"LDAP Search Error: {err}")
        return None