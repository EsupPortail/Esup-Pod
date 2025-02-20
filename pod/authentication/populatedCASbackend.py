"""Esup-Pod CAS & LDAP authentication backend."""

from django.conf import settings
from django.contrib.sites.models import Site
from pod.authentication.models import (
    Owner,
    AccessGroup,
    DEFAULT_AFFILIATION,
    AFFILIATION_STAFF,
)
from ldap3 import Server, Connection
from ldap3 import ALL as __ALL__
from ldap3.core.exceptions import (
    LDAPSocketOpenError,
    LDAPBindError,
    LDAPAttributeError,
    LDAPInvalidFilterError,
)
from django.core.exceptions import ObjectDoesNotExist

import logging

logger = logging.getLogger(__name__)

AUTH_CAS_USER_SEARCH = getattr(settings, "AUTH_CAS_USER_SEARCH", "user")

GROUP_STAFF = AFFILIATION_STAFF

LDAP_SERVER = getattr(settings, "LDAP_SERVER", {"url": "", "port": 389, "use_ssl": False})
AUTH_LDAP_BIND_DN = getattr(settings, "AUTH_LDAP_BIND_DN", "")
AUTH_LDAP_BIND_PASSWORD = getattr(settings, "AUTH_LDAP_BIND_PASSWORD", "")
AUTH_LDAP_USER_SEARCH = getattr(
    settings,
    "AUTH_LDAP_USER_SEARCH",
    ("ou=people,dc=univ,dc=fr", "(uid=%(uid)s)"),
)
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
    },
)

CAS_FORCE_LOWERCASE_USERNAME = getattr(settings, "CAS_FORCE_LOWERCASE_USERNAME", False)

# search scope
__BASE__ = "BASE"
__LEVEL__ = "LEVEL"
__SUBTREE__ = "SUBTREE"


def populateUser(user, cas_attributes) -> None:
    """Populate user form CAS or LDAP attributes."""
    owner, owner_created = Owner.objects.get_or_create(user=user)
    owner.auth_type = "CAS"
    delete_synchronized_access_group(owner)

    POPULATE_USER = getattr(settings, "POPULATE_USER", None)
    if POPULATE_USER == "CAS":
        populateUserFromCAS(user, owner, cas_attributes)
    if POPULATE_USER == "LDAP" and LDAP_SERVER["url"] != "":
        populateUserFromLDAP(user, owner)

    owner.save()
    user.save()


def populateUserFromCAS(user, owner, attributes) -> None:
    """Populate user and owner objects from CAS attributes."""
    owner.affiliation = (
        attributes["primaryAffiliation"]
        if ("primaryAffiliation" in attributes)
        else DEFAULT_AFFILIATION
    )

    if "affiliation" in attributes:
        CREATE_GROUP_FROM_AFFILIATION = getattr(
            settings, "CREATE_GROUP_FROM_AFFILIATION", False
        )
        for affiliation in attributes["affiliation"]:
            if affiliation in AFFILIATION_STAFF:
                user.is_staff = True
            if CREATE_GROUP_FROM_AFFILIATION:
                # Creating access groups from CAS affiliations
                accessgroup, group_created = AccessGroup.objects.get_or_create(
                    code_name=affiliation
                )
                if group_created:
                    accessgroup.display_name = affiliation
                    accessgroup.auto_sync = True
                accessgroup.sites.add(Site.objects.get_current())
                accessgroup.save()
                user.owner.accessgroup_set.add(accessgroup)

        if "groups" in attributes:
            assign_accessgroups(attributes["groups"], user)


def populateUserFromLDAP(user, owner) -> None:
    """Populate user and owner objects from LDAP."""
    list_value = []
    for val in USER_LDAP_MAPPING_ATTRIBUTES.values():
        list_value.append(str(val))
    conn = get_ldap_conn()
    if conn is not None:
        entry = get_entry(conn, user.username, list_value)
        if entry is not None:
            populate_user_from_entry(user, owner, entry)


def delete_synchronized_access_group(owner) -> None:
    """Delete synchronized access groups."""
    groups_to_sync = AccessGroup.objects.filter(auto_sync=True)
    for group_to_sync in groups_to_sync:
        owner.accessgroup_set.remove(group_to_sync)


def get_server() -> Server:
    """Get LDAP server."""
    if isinstance(LDAP_SERVER["url"], str):
        server = Server(
            LDAP_SERVER["url"],
            port=LDAP_SERVER["port"],
            use_ssl=LDAP_SERVER["use_ssl"],
            get_info=__ALL__,
        )
    elif isinstance(LDAP_SERVER["url"], tuple):
        hosts = []
        for server in LDAP_SERVER["url"]:
            if not (server == LDAP_SERVER["url"][0]):
                hosts.append(server)
        server = Server(
            LDAP_SERVER["url"][0],
            port=LDAP_SERVER["port"],
            use_ssl=LDAP_SERVER["use_ssl"],
            get_info=__ALL__,
            allowed_referral_hosts=hosts,
        )
    return server


def get_ldap_conn():
    """Open and get LDAP connexion."""
    try:
        server = get_server()
        conn = Connection(
            server, AUTH_LDAP_BIND_DN, AUTH_LDAP_BIND_PASSWORD, auto_bind=True
        )
        return conn
    except LDAPBindError as err:
        logger.error("LDAPBindError, credentials incorrect: {0}".format(err))
        return None
    except LDAPSocketOpenError as err:
        logger.error("LDAPSocketOpenError: %s" % err)
        return None


def get_entry(conn, username, list_value):
    """Get LDAP entries."""
    try:
        conn.search(
            AUTH_LDAP_USER_SEARCH[0],
            AUTH_LDAP_USER_SEARCH[1] % {"uid": username},
            search_scope=__SUBTREE__,  # BASE, LEVEL and SUBTREE
            attributes=list_value,
            size_limit=1,
        )
        return conn.entries[0] if len(conn.entries) > 0 else None
    except LDAPAttributeError as err:
        logger.error("LDAPAttributeError, invalid attribute: {0}".format(err))
        return None
    except LDAPInvalidFilterError as err:
        logger.error("LDAPInvalidFilterError, invalid filter: {0}".format(err))
        return None


def assign_accessgroups(groups_element, user) -> None:
    """Assign access groups to the user."""
    # print("assign_accessgroups / groups_element : %s " % groups_element)
    CREATE_GROUP_FROM_GROUPS = getattr(settings, "CREATE_GROUP_FROM_GROUPS", False)
    for group in groups_element:

        if group in GROUP_STAFF:
            user.is_staff = True
        if CREATE_GROUP_FROM_GROUPS:
            accessgroup, group_created = AccessGroup.objects.get_or_create(
                code_name=group
            )
            if group_created:
                accessgroup.display_name = group
                accessgroup.auto_sync = True
            accessgroup.sites.add(Site.objects.get_current())
            accessgroup.save()
            user.owner.accessgroup_set.add(accessgroup)
        else:
            try:
                accessgroup = AccessGroup.objects.get(code_name=group)
                user.owner.accessgroup_set.add(accessgroup)
            except ObjectDoesNotExist:
                pass


def create_accessgroups(user, tree_or_entry, auth_type) -> None:
    """Create access groups from LDAP entry or CAS tree."""
    groups_element = []
    if auth_type == "ldap":
        groups_element = (
            tree_or_entry[USER_LDAP_MAPPING_ATTRIBUTES["groups"]].values
            if (
                USER_LDAP_MAPPING_ATTRIBUTES.get("groups")
                and tree_or_entry[USER_LDAP_MAPPING_ATTRIBUTES["groups"]]
            )
            else []
        )
    else:
        return
    assign_accessgroups(groups_element, user)


def get_entry_value(entry, attribute, default):
    """Retrieve the value of the given attribute from the LDAP entry."""
    if (
        USER_LDAP_MAPPING_ATTRIBUTES.get(attribute)
        and entry[USER_LDAP_MAPPING_ATTRIBUTES[attribute]]
    ):
        if attribute == "last_name" and isinstance(
            entry[USER_LDAP_MAPPING_ATTRIBUTES[attribute]].value, list
        ):
            return entry[USER_LDAP_MAPPING_ATTRIBUTES[attribute]].value[0]
        elif attribute == "affiliations":
            return entry[USER_LDAP_MAPPING_ATTRIBUTES[attribute]].values
        else:
            return entry[USER_LDAP_MAPPING_ATTRIBUTES[attribute]].value
    else:
        return default


def populate_user_from_entry(user, owner, entry) -> None:
    """Populate user and owner objects from the LDAP entry."""
    user.email = get_entry_value(entry, "mail", "")
    user.first_name = get_entry_value(entry, "first_name", "")
    user.last_name = get_entry_value(entry, "last_name", "")
    user.save()
    owner.affiliation = get_entry_value(entry, "primaryAffiliation", DEFAULT_AFFILIATION)
    owner.establishment = get_entry_value(entry, "establishment", "")
    owner.save()
    affiliations = get_entry_value(entry, attribute="affiliations", default=[])
    CREATE_GROUP_FROM_AFFILIATION = getattr(
        settings, "CREATE_GROUP_FROM_AFFILIATION", False
    )
    for affiliation in affiliations:
        if affiliation in AFFILIATION_STAFF:
            user.is_staff = True
        if CREATE_GROUP_FROM_AFFILIATION:
            accessgroup, group_created = AccessGroup.objects.get_or_create(
                code_name=affiliation
            )
            if group_created:
                accessgroup.display_name = affiliation
                accessgroup.auto_sync = True
            accessgroup.sites.add(Site.objects.get_current())
            accessgroup.save()
            # group.groupsite.sites.add(Site.objects.get_current())
            user.owner.accessgroup_set.add(accessgroup)
    create_accessgroups(user, entry, "ldap")
    user.save()
    owner.save()


def print_xml_tree(tree) -> None:
    """Print XML tree for debug purpose."""
    import xml.etree.ElementTree as ET
    from defusedxml import minidom
    import os

    xml_string = minidom.parseString(ET.tostring(tree)).toprettyxml()
    xml_string = os.linesep.join(
        [s for s in xml_string.splitlines() if s.strip()]
    )  # remove the weird newline issue
    print(xml_string)
