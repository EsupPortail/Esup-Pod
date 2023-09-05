"""test populated authentication."""
import random
from django.conf import settings
from django.test import TestCase, override_settings
from pod.authentication.models import Owner, AccessGroup, AFFILIATION_STAFF
from pod.authentication import populatedCASbackend
from pod.authentication import shibmiddleware
from pod.authentication import backends
from pod.authentication.backends import (
    ShibbBackend,
    OIDCBackend,
    OIDC_CLAIM_FAMILY_NAME,
    OIDC_CLAIM_GIVEN_NAME,
)
from django.test import RequestFactory
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

REMOTE_USER_HEADER = getattr(settings, "REMOTE_USER_HEADER", "REMOTE_USER")

SHIBBOLETH_ATTRIBUTE_MAP = getattr(
    settings,
    "SHIBBOLETH_ATTRIBUTE_MAP",
    {
        "REMOTE_USER": (True, "username"),
        "Shibboleth-givenName": (True, "first_name"),
        "Shibboleth-sn": (False, "last_name"),
        "Shibboleth-mail": (False, "email"),
        "Shibboleth-primary-affiliation": (False, "affiliation"),
        "Shibboleth-unscoped-affiliation": (False, "affiliations"),
    },
)

SHIBBOLETH_STAFF_ALLOWED_DOMAINS = getattr(
    settings, "SHIBBOLETH_STAFF_ALLOWED_DOMAINS", None
)

SHIB_URL = getattr(settings, "SHIB_URL", "https://univ.fr/Shibboleth.sso/WAYF")

SHIB_LOGOUT_URL = getattr(
    settings, "SHIB_LOGOUT_URL", "https://univ.fr/Shibboleth.sso/Logout"
)

UNSTAFFABLE_AFFILIATIONS = ["member", "unprobable"]

UNSTAFFABLE_AFFILIATION = random.choice(UNSTAFFABLE_AFFILIATIONS)


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
        AccessGroup.objects.create(
            code_name="groupTest2", display_name="Group de test 2", auto_sync="True"
        )
        print(" --->  SetUp of PopulatedCASTestCase: OK!")

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
        self.assertEqual(AccessGroup.objects.all().count(), 2)
        self.assertEqual(user.owner.accessgroup_set.all().count(), 0)
        print(
            " --->  test_populate_user_from_tree by default"
            " of PopulatedCASTestCase: OK!"
        )

    @override_settings(DEBUG=False, CREATE_GROUP_FROM_AFFILIATION=True)
    def test_populate_user_from_tree_affiliation(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        reload(populatedCASbackend)
        tree = ET.fromstring(self.xml_string)
        populatedCASbackend.populate_user_from_tree(user, owner, tree)
        self.assertEqual(AccessGroup.objects.all().count(), 4)
        self.assertTrue(
            user.owner.accessgroup_set.filter(code_name__in=["member", "staff"]).exists()
        )
        print(
            " --->  test_populate_user_from_tree_affiliation"
            " of PopulatedCASTestCase: OK!"
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
        self.assertEqual(AccessGroup.objects.all().count(), 6)
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
            " of PopulatedCASTestCase: OK!"
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
        self.assertEqual(AccessGroup.objects.all().count(), 4)

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
            " of PopulatedCASTestCase: OK!"
        )

    @override_settings(
        DEBUG=True,
        CREATE_GROUP_FROM_AFFILIATION=True,
        CREATE_GROUP_FROM_GROUPS=True,
        POPULATE_USER="CAS",
    )
    def test_populate_user_from_tree_unpopulate_group(self):
        user = User.objects.get(username="pod")
        user.owner.accessgroup_set.add(AccessGroup.objects.get(code_name="groupTest"))
        user.owner.accessgroup_set.add(AccessGroup.objects.get(code_name="groupTest2"))
        user.save()

        reload(populatedCASbackend)
        tree = ET.fromstring(self.xml_string)
        populatedCASbackend.populateUser(tree)
        user = User.objects.get(username="pod")

        self.assertEqual(AccessGroup.objects.all().count(), 6)
        self.assertTrue(
            user.owner.accessgroup_set.filter(
                code_name__in=[
                    "member",
                    "staff",
                    "cn=group1,ou=groups,dc=univ,dc=fr",
                    "cn=group2,ou=groups,dc=univ,dc=fr",
                    "groupTest",
                ]
            ).exists()
        )
        self.assertFalse(
            user.owner.accessgroup_set.filter(
                code_name__in=[
                    "groupTest2",
                ]
            ).exists()
        )
        print(
            " --->  test_populate_user_from_tree_unpopulate_group"
            " of PopulatedCASTestCase: OK!"
        )

    def test_delete_synchronized_access_group(self):
        user = User.objects.get(username="pod")
        user.owner.accessgroup_set.add(AccessGroup.objects.get(code_name="groupTest"))
        user.owner.accessgroup_set.add(AccessGroup.objects.get(code_name="groupTest2"))
        user.save()
        populatedCASbackend.delete_synchronized_access_group(user.owner)
        self.assertEqual(AccessGroup.objects.all().count(), 2)
        self.assertTrue(
            user.owner.accessgroup_set.filter(
                code_name__in=[
                    "groupTest",
                ]
            ).exists()
        )
        self.assertFalse(
            user.owner.accessgroup_set.filter(
                code_name__in=[
                    "groupTest2",
                ]
            ).exists()
        )
        print(" --->  test_delete_synchronized_access_group of PopulatedCASTestCase: OK!")


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
        AccessGroup.objects.create(
            code_name="groupTest2", display_name="Group de test 2", auto_sync="True"
        )
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
        print(" --->  SetUp of PopulatedLDAPTestCase: OK!")

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
        self.assertEqual(AccessGroup.objects.all().count(), 2)
        self.assertEqual(user.owner.accessgroup_set.all().count(), 0)
        print(
            " --->  test_populate_user_from_entry by default"
            " of PopulatedLDAPTestCase: OK!"
        )

    @override_settings(DEBUG=False, CREATE_GROUP_FROM_AFFILIATION=True)
    def test_populate_user_from_entry_affiliation(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        reload(populatedCASbackend)
        populatedCASbackend.populate_user_from_entry(user, owner, self.entry)
        self.assertEqual(AccessGroup.objects.all().count(), 4)
        self.assertTrue(
            user.owner.accessgroup_set.filter(code_name__in=["member", "staff"]).exists()
        )
        print(
            " --->  test_populate_user_from_entry_affiliation"
            " of PopulatedLDAPTestCase: OK!"
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
        self.assertEqual(AccessGroup.objects.all().count(), 6)
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
            " of PopulatedLDAPTestCase: OK!"
        )

        @override_settings(
            DEBUG=True,
            CREATE_GROUP_FROM_AFFILIATION=True,
            CREATE_GROUP_FROM_GROUPS=True,
            POPULATE_USER="LDAP",
        )
        def test_populate_user_from_entry_unpopulate_group(self):
            user = User.objects.get(username="pod")
            user.owner.accessgroup_set.add(AccessGroup.objects.get(code_name="groupTest"))
            user.owner.accessgroup_set.add(
                AccessGroup.objects.get(code_name="groupTest2")
            )
            user.save()

            reload(populatedCASbackend)
            tree = ET.fromstring(self.xml_string)
            populatedCASbackend.populateUser(tree)
            user = User.objects.get(username="pod")

            self.assertEqual(AccessGroup.objects.all().count(), 6)
            self.assertTrue(
                user.owner.accessgroup_set.filter(
                    code_name__in=[
                        "member",
                        "staff",
                        "cn=group1,ou=groups,dc=univ,dc=fr",
                        "cn=group2,ou=groups,dc=univ,dc=fr",
                        "groupTest",
                    ]
                ).exists()
            )
            self.assertFalse(
                user.owner.accessgroup_set.filter(
                    code_name__in=[
                        "groupTest2",
                    ]
                ).exists()
            )
            print(
                " --->  test_populate_user_from_entry_unpopulate_group"
                " of PopulatedLDAPTestCase: OK!"
            )


class PopulatedShibTestCase(TestCase):
    def setUp(self):
        """setUp PopulatedShibTestCase create user pod"""
        self.hmap = {}
        for a in SHIBBOLETH_ATTRIBUTE_MAP:
            self.hmap[SHIBBOLETH_ATTRIBUTE_MAP[a][1]] = a
            # print(SHIBBOLETH_ATTRIBUTE_MAP[a][1] + ' > ' + a)

        print(" --->  SetUp of PopulatedShibTestCase: OK!")

    def _authenticate_shib_user(self, u):
        """Simulate shibboleth header."""
        fake_shib_header = {
            "REMOTE_USER": u["username"],
            self.hmap["username"]: u["username"],
            self.hmap["email"]: u["email"],
            self.hmap["first_name"]: u["first_name"],
            self.hmap["last_name"]: u["last_name"],
        }
        if "groups" in u.keys():
            fake_shib_header[self.hmap["groups"]] = u["groups"]
        if "affiliations" in u.keys():
            fake_shib_header[self.hmap["affiliation"]] = u["affiliations"].split(";")[0]
            fake_shib_header[self.hmap["affiliations"]] = u["affiliations"]

        """Get valid shib_meta from simulated shibboleth header """
        request = RequestFactory().get("/", REMOTE_USER=u["username"])
        request.META.update(**fake_shib_header)
        shib_meta, error = shibmiddleware.ShibbMiddleware.parse_attributes(request)
        self.assertFalse(error, "Generating shibboleth attribute mapping contains errors")

        """Check user authentication """
        user = ShibbBackend.authenticate(
            ShibbBackend(),
            request=request,
            remote_user=u["username"],
            shib_meta=shib_meta,
        )
        self.assertTrue(user.is_authenticated)

        return (user, shib_meta)

    @override_settings(DEBUG=False)
    def test_make_profile(self):
        """Test if user attributes are retrieved."""
        user, shib_meta = self._authenticate_shib_user(
            {
                "username": "jdo@univ.fr",
                "first_name": "John",
                "last_name": "Do",
                "email": "john.do@univ.fr",
                "affiliations": "teacher;staff;member",
            }
        )
        self.assertEqual(user.username, "jdo@univ.fr")
        self.assertEqual(user.email, "john.do@univ.fr")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Do")

        """Test if user can be staff if SHIBBOLETH_STAFF_ALLOWED_DOMAINS is None """
        settings.SHIBBOLETH_STAFF_ALLOWED_DOMAINS = None
        reload(shibmiddleware)
        shibmiddleware.ShibbMiddleware.make_profile(
            shibmiddleware.ShibbMiddleware(), user, shib_meta
        )
        self.assertTrue(user.is_staff)

        owner = Owner.objects.get(user__username="jdo@univ.fr")
        self.assertEqual(owner.affiliation, "teacher")

        """Test if user can be staff when SHIBBOLETH_STAFF_ALLOWED_DOMAINS
        is restricted """
        settings.SHIBBOLETH_STAFF_ALLOWED_DOMAINS = (
            "univ-a.fr",
            "univ-b.fr",
        )
        user.is_staff = False  # Staff status is not remove
        user.save()
        reload(shibmiddleware)
        shibmiddleware.ShibbMiddleware.make_profile(
            shibmiddleware.ShibbMiddleware(), user, shib_meta
        )
        self.assertFalse(user.is_staff)

        """Test if user become staff when SHIBBOLETH_STAFF_ALLOWED_DOMAINS
        is restrict and contains his domain """
        settings.SHIBBOLETH_STAFF_ALLOWED_DOMAINS = ("univ.fr",)
        reload(shibmiddleware)
        shibmiddleware.ShibbMiddleware.make_profile(
            shibmiddleware.ShibbMiddleware(), user, shib_meta
        )
        self.assertTrue(user.is_staff)

        """Test if same user with new unstaffable affiliation keep his staff status """
        for a in UNSTAFFABLE_AFFILIATIONS:
            self.assertFalse(a in AFFILIATION_STAFF)
        user, shib_meta = self._authenticate_shib_user(
            {
                "username": "jdo@univ.fr",
                "first_name": "Jean",
                "last_name": "Do",
                "email": "jean.do@univ.fr",
                "affiliations": ";".join(UNSTAFFABLE_AFFILIATIONS),
            }
        )
        shibmiddleware.ShibbMiddleware.make_profile(
            shibmiddleware.ShibbMiddleware(), user, shib_meta
        )
        self.assertTrue(user.is_staff)  # Staff status is not remove

        """Test if the main affiliation of this same user
        with new unstaffable affiliation has changed """
        owner = Owner.objects.get(user__username="jdo@univ.fr")
        self.assertEqual(owner.affiliation, "member")

        """Test if a new user with same unstaffable affiliations has no staff status"""
        user, shib_meta = self._authenticate_shib_user(
            {
                "username": "ada@univ.fr",
                "first_name": "Ada",
                "last_name": "Da",
                "email": "ada.da@univ.fr",
                "affiliations": ";".join(UNSTAFFABLE_AFFILIATIONS),
            }
        )
        shibmiddleware.ShibbMiddleware.make_profile(
            shibmiddleware.ShibbMiddleware(), user, shib_meta
        )
        self.assertFalse(user.is_staff)

        print(" --->  test_make_profile of PopulatedShibTestCase: OK!")


class PopulatedOIDCTestCase(TestCase):
    @override_settings(
        OIDC_RP_CLIENT_ID="MWViNTY2NzJjNGY4YTQ1MTAwMTNiYjk3",
        OIDC_RP_CLIENT_SECRET="YTM0MzIxZTVmMzZmMTdjNzY5NDQyODcw",
        OIDC_OP_TOKEN_ENDPOINT="https://auth.server.com/oauth/token",
        OIDC_OP_USER_ENDPOINT="https://auth.server.com/oauth/userinfo",
        OIDC_DEFAULT_AFFILIATION=UNSTAFFABLE_AFFILIATION,
    )
    def test_OIDC_commoner_with_default_unstaffable_affiliation(self):
        backends.OIDC_DEFAULT_AFFILIATION = UNSTAFFABLE_AFFILIATION
        user = OIDCBackend().create_user(
            claims={OIDC_CLAIM_GIVEN_NAME: "John", OIDC_CLAIM_FAMILY_NAME: "Doe"}
        )
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.owner.affiliation, settings.OIDC_DEFAULT_AFFILIATION)
        self.assertFalse(
            user.is_staff
        )  # user should not be django admin according to its unstaffable affiliation
        print(
            " --->  test_OIDC_commoner_with_default_unstaffable_access_group"
            " of PopulatedOIDCTestCase: OK!"
        )

    @override_settings(
        OIDC_RP_CLIENT_ID="MWViNTY2NzJjNGY4YTQ1MTAwMTNiYjk3",
        OIDC_RP_CLIENT_SECRET="YTM0MzIxZTVmMzZmMTdjNzY5NDQyODcw",
        OIDC_OP_TOKEN_ENDPOINT="https://auth.server.com/oauth/token",
        OIDC_OP_USER_ENDPOINT="https://auth.server.com/oauth/userinfo",
        # OIDC_DEFAULT_AFFILIATION=random.choice(AFFILIATION_STAFF),
    )
    def test_OIDC_django_admin_user_with_default_staff_affiliation(self):
        backends.OIDC_DEFAULT_AFFILIATION = random.choice(AFFILIATION_STAFF)
        user = OIDCBackend().create_user(
            claims={OIDC_CLAIM_GIVEN_NAME: "Jane", OIDC_CLAIM_FAMILY_NAME: "Did"}
        )
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Did")
        self.assertEqual(user.owner.affiliation, backends.OIDC_DEFAULT_AFFILIATION)
        self.assertTrue(
            user.is_staff
        )  # staffable affiliation should give user access to django admin
        print(
            " --->  test_OIDC_django_admin_user_with_default_staff_affiliation"
            " of PopulatedOIDCTestCase: OK!"
        )

    @override_settings(
        OIDC_RP_CLIENT_ID="MWViNTY2NzJjNGY4YTQ1MTAwMTNiYjk3",
        OIDC_RP_CLIENT_SECRET="YTM0MzIxZTVmMzZmMTdjNzY5NDQyODcw",
        OIDC_OP_TOKEN_ENDPOINT="https://auth.server.com/oauth/token",
        OIDC_OP_USER_ENDPOINT="https://auth.server.com/oauth/userinfo",
        OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES=["specific"],
    )
    def test_OIDC_user_with_default_access_group(self):
        backends.OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES = ["specific"]
        for code_name in settings.OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES + [
            "useless",
            "dull",
        ]:
            AccessGroup.objects.create(
                code_name=code_name, display_name=f"Access group {code_name}"
            )
        user = OIDCBackend().create_user(
            claims={OIDC_CLAIM_GIVEN_NAME: "Jean", OIDC_CLAIM_FAMILY_NAME: "Fit"}
        )
        self.assertEqual(user.first_name, "Jean")
        self.assertEqual(user.last_name, "Fit")
        self.assertEqual(AccessGroup.objects.all().count(), 3)
        self.assertEqual(user.owner.accessgroup_set.all().count(), 1)
        self.assertTrue(
            user.owner.accessgroup_set.filter(code_name="specific").exists()
        )  # OIDC new user should have the specified access group from in settings
        print(
            " --->  test_OIDC_user_with_default_access_group"
            " of PopulatedOIDCTestCase: OK!"
        )

    @override_settings(
        OIDC_RP_CLIENT_ID="MWViNTY2NzJjNGY4YTQ1MTAwMTNiYjk3",
        OIDC_RP_CLIENT_SECRET="YTM0MzIxZTVmMzZmMTdjNzY5NDQyODcw",
        OIDC_OP_TOKEN_ENDPOINT="https://auth.server.com/oauth/token",
        OIDC_OP_USER_ENDPOINT="https://auth.server.com/oauth/userinfo",
        OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES=["specific", "unique"],
    )
    def test_OIDC_user_with_multiple_default_access_groups(self):
        backends.OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES = ["specific", "unique"]
        for code_name in settings.OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES + ["dull"]:
            AccessGroup.objects.create(
                code_name=code_name, display_name=f"Access group {code_name}"
            )
        user = OIDCBackend().create_user(
            claims={OIDC_CLAIM_GIVEN_NAME: "Jean", OIDC_CLAIM_FAMILY_NAME: "Fit"}
        )
        self.assertEqual(user.first_name, "Jean")
        self.assertEqual(user.last_name, "Fit")
        self.assertEqual(AccessGroup.objects.all().count(), 3)
        self.assertEqual(
            user.owner.accessgroup_set.all().count(), 2
        )  # OIDC new user should have 2 access groups
        self.assertTrue(user.owner.accessgroup_set.filter(code_name="specific").exists())
        self.assertTrue(user.owner.accessgroup_set.filter(code_name="unique").exists())
        print(
            " --->  test_OIDC_user_with_multiple_default_access_groups"
            " of PopulatedOIDCTestCase: OK!"
        )
