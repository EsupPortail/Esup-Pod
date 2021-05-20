# test_populated
from django.conf import settings
from django.test import TestCase, override_settings
from pod.authentication.models import Owner, AccessGroup
from pod.authentication import populatedCASbackend
from django.contrib.auth.models import User
from importlib import reload
from xml.etree import ElementTree as ET

from ldap3 import Server, Connection, MOCK_SYNC

"""
USER_CAS_MAPPING_ATTRIBUTES = getattr(
    settings, 'USER_CAS_MAPPING_ATTRIBUTES',
    {
        "uid": "uid",
        "mail": "mail",
        "last_name": "sn",
        "first_name": "givenname",
        "primaryAffiliation": "eduPersonPrimaryAffiliation",
        "affiliation": "eduPersonAffiliation",
        "groups": "memberOf"
    })
"""
USER_CAS_MAPPING_ATTRIBUTES_TEST_NOGROUPS = {
    "uid": "uid",
    "mail": "mail",
    "last_name": "sn",
    "first_name": "givenname",
    "primaryAffiliation": "eduPersonPrimaryAffiliation",
    "affiliation": "eduPersonAffiliation",
    "groups": "",
}

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


class PopulatedCASTestCase(TestCase):
    # populate_user_from_tree(user, owner, tree)
    xml_string = """<?xml version="1.0" ?>
<ns0:serviceResponse xmlns:ns0="http://www.yale.edu/tp/cas">
    <ns0:authenticationSuccess>
        <ns0:user>pod</ns0:user>
        <ns0:attributes>
            <ns0:uid>pod</ns0:uid>
            <ns0:eduPersonAffiliation>member</ns0:eduPersonAffiliation>
            <ns0:eduPersonAffiliation>staff</ns0:eduPersonAffiliation>
            <ns0:mail>pod@univ.fr</ns0:mail>
            <ns0:eduPersonPrimaryAffiliation>staff</ns0:eduPersonPrimaryAffiliation>
            <ns0:sn>Pod</ns0:sn>
            <ns0:givenname>Univ</ns0:givenname>
            <ns0:memberOf>cn=group1,ou=groups,dc=univ,dc=fr</ns0:memberOf>
            <ns0:memberOf>cn=group2,ou=groups,dc=univ,dc=fr</ns0:memberOf>
        </ns0:attributes>
    </ns0:authenticationSuccess>
</ns0:serviceResponse>"""

    def setUp(self):
        """setUp PopulatedCASTestCase create user pod"""
        User.objects.create(username="pod", password="pod1234pod")
        AccessGroup.objects.create(code_name="groupTest", display_name="Group de test")
        print(" --->  SetUp of PopulatedCASTestCase : OK !")

    @override_settings(DEBUG=False)
    def test_populate_user_from_tree(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        tree = ET.fromstring(self.xml_string)
        reload(populatedCASbackend)
        populatedCASbackend.populate_user_from_tree(user, owner, tree)
        self.assertEqual(user.email, "pod@univ.fr")
        self.assertEqual(user.first_name, "Univ")
        self.assertEqual(user.last_name, "Pod")
        # CREATE_GROUP_FROM_AFFILIATION = getattr(
        #    settings, 'CREATE_GROUP_FROM_AFFILIATION', False)
        # CREATE_GROUP_FROM_GROUPS = getattr(
        #    settings, 'CREATE_GROUP_FROM_GROUPS', False)
        # check no group are created any from affiliation or groups
        self.assertEqual(user.is_staff, True)
        self.assertEqual(AccessGroup.objects.all().count(), 1)
        self.assertEqual(user.owner.accessgroup_set.all().count(), 0)
        print(
            " --->  test_populate_user_from_tree by default"
            " of PopulatedCASTestCase : OK !"
        )

    @override_settings(DEBUG=False, CREATE_GROUP_FROM_AFFILIATION=True)
    def test_populate_user_from_tree_affiliation(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        reload(populatedCASbackend)
        tree = ET.fromstring(self.xml_string)
        populatedCASbackend.populate_user_from_tree(user, owner, tree)
        self.assertEqual(AccessGroup.objects.all().count(), 3)
        self.assertTrue(
            user.owner.accessgroup_set.filter(code_name__in=["member", "staff"]).exists()
        )
        print(
            " --->  test_populate_user_from_tree_affiliation"
            " of PopulatedCASTestCase : OK !"
        )

    @override_settings(
        DEBUG=True,
        CREATE_GROUP_FROM_AFFILIATION=True,
        CREATE_GROUP_FROM_GROUPS=True,
    )
    def test_populate_user_from_tree_affiliation_group(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        reload(populatedCASbackend)
        tree = ET.fromstring(self.xml_string)
        populatedCASbackend.populate_user_from_tree(user, owner, tree)
        self.assertEqual(AccessGroup.objects.all().count(), 5)
        self.assertTrue(
            user.owner.accessgroup_set.filter(
                code_name__in=[
                    "member",
                    "staff",
                    "cn=group1,ou=groups,dc=univ,dc=fr",
                    "cn=group2,ou=groups,dc=univ,dc=fr",
                ]
            ).exists()
        )
        print(
            " --->  test_populate_user_from_tree_affiliation_group"
            " of PopulatedCASTestCase : OK !"
        )

    @override_settings(
        DEBUG=True,
        CREATE_GROUP_FROM_AFFILIATION=True,
        CREATE_GROUP_FROM_GROUPS=True,
        USER_CAS_MAPPING_ATTRIBUTES=USER_CAS_MAPPING_ATTRIBUTES_TEST_NOGROUPS,
    )
    def test_populate_user_from_tree_affiliation_nogroup(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        reload(populatedCASbackend)
        tree = ET.fromstring(self.xml_string)
        populatedCASbackend.populate_user_from_tree(user, owner, tree)
        # check they are only existing group and affiliation groups x2
        self.assertEqual(AccessGroup.objects.all().count(), 3)

        self.assertTrue(
            user.owner.accessgroup_set.filter(
                code_name__in=[
                    "member",
                    "staff",
                ]
            ).exists()
        )
        print(
            " --->  test_populate_user_from_tree_affiliation_nogroup"
            " of PopulatedCASTestCase : OK !"
        )


class PopulatedLDAPTestCase(TestCase):
    attrs = {
        "eduPersonAffiliation": ["staff", "member"],
        "eduPersonPrimaryAffiliation": "staff",
        "givenName": "Univ",
        "mail": "pod@univ.fr",
        "memberOf": [
            "cn=group1,ou=groups,dc=univ,dc=fr",
            "cn=group2,ou=groups,dc=univ,dc=fr",
        ],
        "sn": "Pod",
        "uid": "pod",
    }
    entry = ""

    def setUp(self):
        """setUp PopulatedLDAPTestCase create user pod"""
        User.objects.create(username="pod", password="pod1234pod")
        AccessGroup.objects.create(code_name="groupTest", display_name="Group de test")
        fake_server = Server("my_fake_server")
        fake_connection = Connection(fake_server, client_strategy=MOCK_SYNC)
        fake_connection.strategy.add_entry("uid=pod,ou=people,dc=univ,dc=fr", self.attrs)
        fake_connection.bind()
        list_value = []
        for val in USER_LDAP_MAPPING_ATTRIBUTES.values():
            list_value.append(str(val))
        is_entry = fake_connection.search(
            "ou=people,dc=univ,dc=fr",
            "(uid=pod)",
            search_scope="SUBTREE",
            attributes=list_value,
            size_limit=1,
        )
        if is_entry:
            self.entry = fake_connection.entries[0]
        fake_connection.unbind()
        print(" --->  SetUp of PopulatedLDAPTestCase : OK !")

    @override_settings(DEBUG=False)
    def test_populate_user_from_entry(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        reload(populatedCASbackend)
        populatedCASbackend.populate_user_from_entry(user, owner, self.entry)
        self.assertEqual(user.email, "pod@univ.fr")
        self.assertEqual(user.first_name, "Univ")
        self.assertEqual(user.last_name, "Pod")
        # CREATE_GROUP_FROM_AFFILIATION = getattr(
        #    settings, 'CREATE_GROUP_FROM_AFFILIATION', False)
        # CREATE_GROUP_FROM_GROUPS = getattr(
        #    settings, 'CREATE_GROUP_FROM_GROUPS', False)
        # check no group are created any from affiliation or groups
        self.assertEqual(user.is_staff, True)
        self.assertEqual(AccessGroup.objects.all().count(), 1)
        self.assertEqual(user.owner.accessgroup_set.all().count(), 0)
        print(
            " --->  test_populate_user_from_entry by default"
            " of PopulatedLDAPTestCase : OK !"
        )

    @override_settings(DEBUG=False, CREATE_GROUP_FROM_AFFILIATION=True)
    def test_populate_user_from_entry_affiliation(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        reload(populatedCASbackend)
        populatedCASbackend.populate_user_from_entry(user, owner, self.entry)
        self.assertEqual(AccessGroup.objects.all().count(), 3)
        self.assertTrue(
            user.owner.accessgroup_set.filter(code_name__in=["member", "staff"]).exists()
        )
        print(
            " --->  test_populate_user_from_entry_affiliation"
            " of PopulatedLDAPTestCase : OK !"
        )

    @override_settings(
        DEBUG=True,
        CREATE_GROUP_FROM_AFFILIATION=True,
        CREATE_GROUP_FROM_GROUPS=True,
    )
    def test_populate_user_from_entry_affiliation_group(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        reload(populatedCASbackend)
        populatedCASbackend.populate_user_from_entry(user, owner, self.entry)
        self.assertEqual(AccessGroup.objects.all().count(), 5)
        # user.owner.accessgroup_set.add(accessgroup)
        self.assertTrue(
            user.owner.accessgroup_set.filter(
                code_name__in=[
                    "member",
                    "staff",
                    "cn=group1,ou=groups,dc=univ,dc=fr",
                    "cn=group2,ou=groups,dc=univ,dc=fr",
                ]
            ).exists()
        )
        print(
            " --->  test_populate_user_from_entry_affiliation_group"
            " of PopulatedLDAPTestCase : OK !"
        )
