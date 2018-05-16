from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from pod.authentication.models import Owner

from ldap3 import Server
from ldap3 import ALL
from ldap3 import Connection

POPULATE_USER = getattr(
    settings, 'POPULATE_USER', None)
CAS_USER_ID = getattr(
    settings, 'CAS_USER_ID', "user")
USER_CAS_MAPPING_ATTRIBUTES = getattr(
    settings, 'USER_CAS_MAPPING_ATTRIBUTES',
    {
        "uid": "uid",
        "mail": "mail",
        "last_name": "sn",
        "first_name": "givenname",
        "affiliation": "eduPersonAffiliation"
    })

CREATE_GROUP_FOM_AFFILIATION = getattr(
    settings, 'CREATE_GROUP_FOM_AFFILIATION', False)

AFFILIATION_STAFF = getattr(
    settings, 'USER_CAS_MAPPING_ATTRIBUTES',
    ('faculty', 'employee', 'staff')
)


def populateUser(tree):
    username_element = tree.find(
        './/{http://www.yale.edu/tp/cas}%s' % CAS_USER_ID)
    username = username_element.text
    user, user_created = User.objects.get_or_create(username=username)
    owner, owner_created = Owner.objects.get_or_create(user=user)
    owner.auth_type = 'CAS'
    owner.save()

    if POPULATE_USER == 'CAS':
        # Mail
        mail_element = tree.find(
            './/{http://www.yale.edu/tp/cas}%s' % USER_CAS_MAPPING_ATTRIBUTES["mail"])
        user.email = mail_element.text if mail_element is not None else ""
        # first_name
        first_name_element = tree.find(
            './/{http://www.yale.edu/tp/cas}%s' % USER_CAS_MAPPING_ATTRIBUTES["first_name"])
        user.first_name = first_name_element.text if first_name_element is not None else ""
        # last_name
        last_name_element = tree.find(
            './/{http://www.yale.edu/tp/cas}%s' % USER_CAS_MAPPING_ATTRIBUTES["last_name"])
        user.last_name = last_name_element.text if last_name_element is not None else ""
        user.save()
        # affiliation
        affiliation_element = tree.findall(
            './/{http://www.yale.edu/tp/cas}%s' % USER_CAS_MAPPING_ATTRIBUTES["affiliation"])
        for affiliation in affiliation_element:
            if affiliation.text in AFFILIATION_STAFF:
                user.is_staff = True
            if CREATE_GROUP_FOM_AFFILIATION:
                group, group_created = Group.objects.get_or_create(
                    name=affiliation.text)
                user.groups.add(group)
        user.save()
        owner.affiliation = affiliation_element[0].text
        owner.save()

    if POPULATE_USER == 'LDAP':
        # do the same
        """
        >>> server = Server('ldap.univ-lille1.fr', get_info=ALL)
        >>> conn = Connection(server, auto_bind=True)
        >>> conn.search('ou=people,dc=univ-lille1,dc=fr', '(uid=ncan)')
        True
        >>> conn.entries
        [DN: uid=ncan,ou=people,dc=univ-lille1,dc=fr - STATUS: Read - READ TIME: 2018-05-16T02:04:42.711012
        ]
        """
