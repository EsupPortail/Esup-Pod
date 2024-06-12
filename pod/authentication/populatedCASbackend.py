"""Esup-Pod CAS & LDAP authentication backend."""

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from pod.authentication.models import Owner
from pod.authentication.models import DEFAULT_AFFILIATION, AFFILIATION_STAFF
from ldap3 import Server
from ldap3 import ALL as __ALL__
from ldap3 import Connection
from ldap3.core.exceptions import LDAPSocketOpenError
from ldap3.core.exceptions import LDAPBindError
from ldap3.core.exceptions import LDAPAttributeError
from ldap3.core.exceptions import LDAPInvalidFilterError
from pod.authentication.models import AccessGroup
from django.core.exceptions import ObjectDoesNotExist

import logging

logger = logging.getLogger(__name__)

DEBUG = getattr(settings, "DEBUG", True)

POPULATE_USER = getattr(settings, "POPULATE_USER", None)
AUTH_CAS_USER_SEARCH = getattr(settings, "AUTH_CAS_USER_SEARCH", "user")
USER_CAS_MAPPING_ATTRIBUTES = getattr(
    settings,
    "USER_CAS_MAPPING_ATTRIBUTES",
    {
        "uid": "uid",
        "mail": "mail",
        "last_name": "sn",
        "first_name": "givenname",
        "primaryAffiliation": "eduPersonPrimaryAffiliation",
        "affiliation": "eduPersonAffiliation",
        "groups": "memberOf",
    },
)

CREATE_GROUP_FROM_AFFILIATION = getattr(settings, "CREATE_GROUP_FROM_AFFILIATION", False)

CREATE_GROUP_FROM_GROUPS = getattr(settings, "CREATE_GROUP_FROM_GROUPS", False)

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


def populateUser(tree) -> None:
    """Populate user form CAS or LDAP attributes."""
    username_element = tree.find(
        ".//{http://www.yale.edu/tp/cas}%s" % AUTH_CAS_USER_SEARCH
    )
    username_element.text = username_element.text.strip()
    username = username_element.text
    if CAS_FORCE_LOWERCASE_USERNAME:
        username = username.lower()
    user, user_created = User.objects.get_or_create(username=username)
    owner, owner_created = Owner.objects.get_or_create(user=user)
    owner.auth_type = "CAS"

    delete_synchronized_access_group(owner)

    owner.save()

    if POPULATE_USER == "CAS":
        populate_user_from_tree(user, owner, tree)
    if POPULATE_USER == "LDAP" and LDAP_SERVER["url"] != "":
        list_value = []
        for val in USER_LDAP_MAPPING_ATTRIBUTES.values():
            list_value.append(str(val))
        conn = get_ldap_conn()
        if conn is not None:
            entry = get_entry(conn, username, list_value)
            if entry is not None:
                populate_user_from_entry(user, owner, entry)


def delete_synchronized_access_group(owner) -> None:
    groups_to_sync = AccessGroup.objects.filter(auto_sync=True)
    for group_to_sync in groups_to_sync:
        owner.accessgroup_set.remove(group_to_sync)


def get_server() -> Server:
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
    groups_element = []
    if auth_type == "cas":
        tree_groups_element = tree_or_entry.findall(
            ".//{http://www.yale.edu/tp/cas}%s" % (USER_CAS_MAPPING_ATTRIBUTES["groups"])
        )
        for tge in tree_groups_element:
            groups_element.append(tge.text)
    elif auth_type == "ldap":
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
    if DEBUG:
        print(entry)
    user.email = get_entry_value(entry, "mail", "")
    user.first_name = get_entry_value(entry, "first_name", "")
    user.last_name = get_entry_value(entry, "last_name", "")
    user.save()
    owner.affiliation = get_entry_value(entry, "primaryAffiliation", DEFAULT_AFFILIATION)
    owner.establishment = get_entry_value(entry, "establishment", "")
    owner.save()
    affiliations = get_entry_value(entry, attribute="affiliations", default=[])
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


def populate_user_from_tree(user, owner, tree) -> None:
    """Populate user from CAS attributes."""
    if DEBUG:
        print_xml_tree(tree)
    # Mail
    mail_element = tree.find(
        ".//{http://www.yale.edu/tp/cas}%s" % (USER_CAS_MAPPING_ATTRIBUTES["mail"])
    )
    user.email = mail_element.text if mail_element is not None else ""
    # first_name
    first_name_element = tree.find(
        ".//{http://www.yale.edu/tp/cas}%s" % (USER_CAS_MAPPING_ATTRIBUTES["first_name"])
    )
    user.first_name = first_name_element.text if first_name_element is not None else ""
    # last_name
    last_name_element = tree.find(
        ".//{http://www.yale.edu/tp/cas}%s" % (USER_CAS_MAPPING_ATTRIBUTES["last_name"])
    )
    user.last_name = last_name_element.text if last_name_element is not None else ""
    user.save()
    # PrimaryAffiliation
    primary_affiliation_element = tree.find(
        ".//{http://www.yale.edu/tp/cas}%s"
        % (USER_CAS_MAPPING_ATTRIBUTES["primaryAffiliation"])
    )
    owner.affiliation = (
        primary_affiliation_element.text
        if (primary_affiliation_element is not None)
        else DEFAULT_AFFILIATION
    )
    # affiliation
    affiliation_element = tree.findall(
        ".//{http://www.yale.edu/tp/cas}%s" % (USER_CAS_MAPPING_ATTRIBUTES["affiliation"])
    )
    for affiliation in affiliation_element:
        if affiliation.text in AFFILIATION_STAFF:
            user.is_staff = True
        if CREATE_GROUP_FROM_AFFILIATION:
            accessgroup, group_created = AccessGroup.objects.get_or_create(
                code_name=affiliation.text
            )
            if group_created:
                accessgroup.display_name = affiliation.text
                accessgroup.auto_sync = True
            accessgroup.sites.add(Site.objects.get_current())
            accessgroup.save()
            user.owner.accessgroup_set.add(accessgroup)
    create_accessgroups(user, tree, "cas")
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
