from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from pod.authentication.models import Owner
from pod.authentication.models import AFFILIATION
from django.contrib.sites.models import Site
from ldap3 import Server
from ldap3 import ALL
from ldap3 import Connection
from ldap3.core.exceptions import LDAPSocketOpenError
from ldap3.core.exceptions import LDAPBindError
from ldap3.core.exceptions import LDAPAttributeError
from ldap3.core.exceptions import LDAPInvalidFilterError

import logging
logger = logging.getLogger(__name__)

POPULATE_USER = getattr(
    settings, 'POPULATE_USER', None)
AUTH_CAS_USER_SEARCH = getattr(
    settings, 'AUTH_CAS_USER_SEARCH', "user")
USER_CAS_MAPPING_ATTRIBUTES = getattr(
    settings, 'USER_CAS_MAPPING_ATTRIBUTES',
    {
        "uid": "uid",
        "mail": "mail",
        "last_name": "sn",
        "first_name": "givenname",
        "primaryAffiliation": "eduPersonPrimaryAffiliation",
        "affiliation": "eduPersonAffiliation"
    })

CREATE_GROUP_FROM_AFFILIATION = getattr(
    settings, 'CREATE_GROUP_FROM_AFFILIATION', False)

AFFILIATION_STAFF = getattr(
    settings, 'AFFILIATION_STAFF',
    ('faculty', 'employee', 'staff')
)

LDAP_SERVER = getattr(
    settings, 'LDAP_SERVER',
    {'url': '', 'port': 389, 'use_ssl': False}
)
AUTH_LDAP_BIND_DN = getattr(
    settings, 'AUTH_LDAP_BIND_DN',
    ''
)
AUTH_LDAP_BIND_PASSWORD = getattr(
    settings, 'AUTH_LDAP_BIND_PASSWORD',
    ''
)
AUTH_LDAP_USER_SEARCH = getattr(
    settings, 'AUTH_LDAP_USER_SEARCH',
    ('ou=people,dc=univ,dc=fr', "(uid=%(uid)s)")
)
USER_LDAP_MAPPING_ATTRIBUTES = getattr(
    settings, 'USER_LDAP_MAPPING_ATTRIBUTES',
    {
        "uid": "uid",
        "mail": "mail",
        "last_name": "sn",
        "first_name": "givenname",
        "primaryAffiliation": "eduPersonPrimaryAffiliation",
        "affiliations": "eduPersonAffiliation"
    })

# search scope
BASE = 'BASE'
LEVEL = 'LEVEL'
SUBTREE = 'SUBTREE'


def populateUser(tree):
    username_element = tree.find(
        './/{http://www.yale.edu/tp/cas}%s' % AUTH_CAS_USER_SEARCH)
    username = username_element.text
    user, user_created = User.objects.get_or_create(username=username)
    owner, owner_created = Owner.objects.get_or_create(user=user)
    owner.auth_type = 'CAS'
    owner.save()

    if POPULATE_USER == 'CAS':
        populate_user_from_tree(user, owner, tree)
    if POPULATE_USER == 'LDAP' and LDAP_SERVER['url'] != '':
        list_value = []
        for val in USER_LDAP_MAPPING_ATTRIBUTES.values():
            list_value.append(str(val))
        conn = get_ldap_conn()
        if conn is not None:
            entry = get_entry(conn, username, list_value)
            if entry is not None:
                populate_user_from_entry(user, owner, entry)


def get_server():
    if isinstance(LDAP_SERVER['url'], str):
        server = Server(LDAP_SERVER['url'], port=LDAP_SERVER[
                        'port'], use_ssl=LDAP_SERVER[
                            'use_ssl'], get_info=ALL)
    elif isinstance(LDAP_SERVER['url'], tuple):
        hosts = []
        for server in LDAP_SERVER['url']:
            if not (server == LDAP_SERVER['url'][0]):
                hosts.append(server)
        server = Server(LDAP_SERVER['url'][0], port=LDAP_SERVER[
            'port'], use_ssl=LDAP_SERVER[
                'use_ssl'], get_info=ALL,
                        allowed_referral_hosts=hosts)
    return server


def get_ldap_conn():
    try:
        server = get_server()
        conn = Connection(
            server, AUTH_LDAP_BIND_DN, AUTH_LDAP_BIND_PASSWORD, auto_bind=True)
        return conn
    except LDAPBindError as err:
        logger.error("LDAPBindError, credentials incorrect: {0}".format(err))
        return None
    except LDAPSocketOpenError as err:
        logger.error("LDAPSocketOpenError : %s" % err)
        return None


def get_entry(conn, username, list_value):
    try:
        conn.search(AUTH_LDAP_USER_SEARCH[0],
                    AUTH_LDAP_USER_SEARCH[1] % {"uid": username},
                    search_scope=SUBTREE,  # BASE, LEVEL and SUBTREE
                    attributes=list_value,
                    size_limit=1)
        return conn.entries[0] if len(conn.entries) > 0 else None
    except LDAPAttributeError as err:
        logger.error(
            "LDAPAttributeError, invalid attribute: {0}".format(err))
        return None
    except LDAPInvalidFilterError as err:
        logger.error(
            "LDAPInvalidFilterError, invalid filter: {0}".format(err))
        return None


def populate_user_from_entry(user, owner, entry):
    user.email = (
        entry[USER_LDAP_MAPPING_ATTRIBUTES['mail']].value if (
            USER_LDAP_MAPPING_ATTRIBUTES.get('mail')
            and entry[USER_LDAP_MAPPING_ATTRIBUTES['mail']]
        ) else ""
    )
    user.first_name = (
        entry[USER_LDAP_MAPPING_ATTRIBUTES['first_name']].value if (
            USER_LDAP_MAPPING_ATTRIBUTES.get('first_name')
            and entry[USER_LDAP_MAPPING_ATTRIBUTES['first_name']]
        ) else ""
    )
    user.last_name = (
        entry[USER_LDAP_MAPPING_ATTRIBUTES['last_name']].value if (
            USER_LDAP_MAPPING_ATTRIBUTES.get('last_name')
            and entry[USER_LDAP_MAPPING_ATTRIBUTES['last_name']]
        ) else ""
    )
    user.save()
    owner.affiliation = (
        entry[USER_LDAP_MAPPING_ATTRIBUTES['primaryAffiliation']].value if (
            USER_LDAP_MAPPING_ATTRIBUTES.get('primaryAffiliation')
            and entry[USER_LDAP_MAPPING_ATTRIBUTES['primaryAffiliation']]
        ) else AFFILIATION[0][0]
    )
    owner.establishment = (
        entry[USER_LDAP_MAPPING_ATTRIBUTES['establishment']].value if (
            USER_LDAP_MAPPING_ATTRIBUTES.get('establishment')
            and entry[USER_LDAP_MAPPING_ATTRIBUTES['establishment']]
        ) else ""
    )
    owner.save()
    affiliations = (
        entry[USER_LDAP_MAPPING_ATTRIBUTES['affiliations']].values if (
            USER_LDAP_MAPPING_ATTRIBUTES.get('affiliations')
            and entry[USER_LDAP_MAPPING_ATTRIBUTES['affiliations']]
        ) else []
    )
    for affiliation in affiliations:
        if affiliation in AFFILIATION_STAFF:
            user.is_staff = True
        if CREATE_GROUP_FROM_AFFILIATION:
            group, group_created = Group.objects.get_or_create(
                name=affiliation)
            group.groupsite.sites.add(Site.objects.get_current())
            user.groups.add(group)
    user.save()


def populate_user_from_tree(user, owner, tree):
    # Mail
    mail_element = tree.find(
        './/{http://www.yale.edu/tp/cas}%s' % (
            USER_CAS_MAPPING_ATTRIBUTES["mail"])
    )
    user.email = mail_element.text if mail_element is not None else ""
    # first_name
    first_name_element = tree.find(
        './/{http://www.yale.edu/tp/cas}%s' % (
            USER_CAS_MAPPING_ATTRIBUTES["first_name"])
    )
    user.first_name = (
        first_name_element.text if first_name_element is not None else ""
    )
    # last_name
    last_name_element = tree.find(
        './/{http://www.yale.edu/tp/cas}%s' % (
            USER_CAS_MAPPING_ATTRIBUTES["last_name"])
    )
    user.last_name = (
        last_name_element.text if last_name_element is not None else ""
    )
    user.save()
    # PrimaryAffiliation
    primary_affiliation_element = tree.find(
        './/{http://www.yale.edu/tp/cas}%s' % (
            USER_CAS_MAPPING_ATTRIBUTES["primaryAffiliation"])
    )
    owner.affiliation = primary_affiliation_element.text if (
        primary_affiliation_element is not None) else AFFILIATION[0][0]
    # affiliation
    affiliation_element = tree.findall(
        './/{http://www.yale.edu/tp/cas}%s' % (
            USER_CAS_MAPPING_ATTRIBUTES["affiliation"])
    )
    for affiliation in affiliation_element:
        if affiliation.text in AFFILIATION_STAFF:
            user.is_staff = True
        if CREATE_GROUP_FROM_AFFILIATION:
            group, group_created = Group.objects.get_or_create(
                name=affiliation.text)
            user.groups.add(group)
    user.save()
    owner.save()
