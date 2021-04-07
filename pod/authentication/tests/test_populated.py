# test_populated

from django.test import TestCase
from pod.authentication.models import Owner, AccessGroup
from django.contrib.auth.models import User
# from django.conf import settings
from django.test.utils import override_settings

from xml.etree import ElementTree as ET


class PopulatedTestCase(TestCase):
    # populate_user_from_tree(user, owner, tree)
    xml_string = '''<?xml version="1.0" ?>
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
</ns0:serviceResponse>'''

    def setUp(self):
        """setUp OwnerTestCase create user pod"""
        User.objects.create(username="pod", password="pod1234pod")
        AccessGroup.objects.create(code_name="group1", display_name="Group 1")
        print(" --->  SetUp of PopulatedTestCase : OK !")

    @override_settings(DEBUG=True)
    def test_populate_user_from_tree(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        from pod.authentication.populatedCASbackend\
            import populate_user_from_tree
        tree = ET.fromstring(self.xml_string)
        populate_user_from_tree(user, owner, tree)
        self.assertEqual(user.email, "pod@univ.fr")
        self.assertEqual(user.first_name, "Pod")
        self.assertEqual(user.last_name, "Univ")
        # CREATE_GROUP_FROM_AFFILIATION = getattr(
        #    settings, 'CREATE_GROUP_FROM_AFFILIATION', False)
        # CREATE_GROUP_FROM_GROUPS = getattr(
        #    settings, 'CREATE_GROUP_FROM_GROUPS', False)
        # check no group are created any from affiliation or groups
        self.assertEqual(user.is_staff, True)
        self.assertEqual(AccessGroup.objects.all().count(), 1)
        print(
            " --->  test_populate_user_from_tree by default"
            " of PopulatedTestCase : OK !")

    @override_settings(
        DEBUG=True,
        CREATE_GROUP_FROM_AFFILIATION=True
    )
    def test_populate_user_from_tree_affiliation(self):
        owner = Owner.objects.get(user__username="pod")
        user = User.objects.get(username="pod")
        self.assertEqual(user.owner, owner)
        from pod.authentication.populatedCASbackend\
            import populate_user_from_tree
        tree = ET.fromstring(self.xml_string)
        populate_user_from_tree(user, owner, tree)
        self.assertEqual(user.email, "pod@univ.fr")
        self.assertEqual(user.first_name, "Pod")
        self.assertEqual(user.last_name, "Univ")
        # CREATE_GROUP_FROM_AFFILIATION = getattr(
        #    settings, 'CREATE_GROUP_FROM_AFFILIATION', False)
        # CREATE_GROUP_FROM_GROUPS = getattr(
        #    settings, 'CREATE_GROUP_FROM_GROUPS', False)
        # check no group are created any from affiliation or groups
        self.assertEqual(user.is_staff, True)
        self.assertEqual(AccessGroup.objects.all().count(), 3)
        # user.owner.accessgroup_set.add(accessgroup)
        self.assertTrue(
            user.owner.accessgroup_set.filter(
                name__in=['member', 'staff']
            ).exists()
        )
        print(
            " --->  test_populate_user_from_tree_affiliation"
            " of PopulatedTestCase : OK !")
