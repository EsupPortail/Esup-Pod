"""
Tests for authentication services and providers.

This module validates the user population logic across different authentication 
providers (CAS, OIDC, LDAP, Shibboleth) and verifies that provider-specific 
tasks, like ticket verification, are integrated correctly.
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..conf import AuthConfig
from ..models import AccessGroup
from ..services import UserPopulator, verify_cas_ticket

User = get_user_model()


class TestUserPopulator(TestCase):
    """
    Test suite for UserPopulator, which handles user attribute synchronization 
    from external auth providers.
    """

    def setUp(self):
        """
        Initializes a test user and a populator instance.
        """
        self.user = User.objects.create(username="testuser", email="test@example.com")
        self.populator = UserPopulator(self.user)

    def test_init_creates_owner(self):
        """
        Verifies that initializing a populator for a user without an owner 
        automatically triggers owner creation.
        """
        user_no_owner = User.objects.create(username="noowner")
        UserPopulator(user_no_owner)
        self.assertTrue(hasattr(user_no_owner, "owner"))
        self.assertIsNotNone(user_no_owner.owner)

    def test_populate_from_cas_basic(self):
        """
        Tests user attribute synchronization from a basic CAS attribute dictionary.
        """
        attributes = {
            "primaryAffiliation": "student",
            "affiliation": ["student"],
            "groups": ["group1"],
            "mail": "test@example.com",
        }
        self.populator.run("CAS", attributes)

        self.user.refresh_from_db()
        self.assertEqual(self.user.owner.auth_type, "CAS")
        self.assertEqual(self.user.owner.affiliation, "student")
        self.assertTrue(AccessGroup.objects.filter(code_name="student").exists())
        self.assertTrue(AccessGroup.objects.filter(code_name="group1").exists())

    def test_populate_from_shibboleth(self):
        """
        Tests user attribute synchronization from Shibboleth environment variables.
        """
        attributes = {
            "first_name": "Shib",
            "last_name": "User",
            "email": "shib@example.com",
            "affiliation": "faculty",
            "affiliations": "faculty;staff",
        }
        self.populator.run("Shibboleth", attributes)

        self.user.refresh_from_db()
        self.assertEqual(self.user.owner.auth_type, "Shibboleth")
        self.assertEqual(self.user.first_name, "Shib")
        self.assertEqual(self.user.last_name, "User")
        self.assertEqual(self.user.email, "shib@example.com")
        self.assertEqual(self.user.owner.affiliation, "faculty")
        self.assertTrue(self.user.is_staff)

    @patch(
        "src.apps.authentication.services.users.populator.auth_settings",
        new_callable=lambda: AuthConfig(
            oidc_claim_given_name="given_name",
            oidc_claim_family_name="family_name",
            oidc_default_affiliation="member",
            oidc_default_access_group_code_names=["oidc_group"],
        ),
    )
    def test_populate_from_oidc(self, mock_settings):
        """
        Tests user attribute synchronization from an OIDC claim dictionary.
        """
        attributes = {
            "given_name": "Oidc",
            "family_name": "User",
            "email": "oidc@example.com",
        }
        self.populator.run("OIDC", attributes)

        self.user.refresh_from_db()
        self.assertEqual(self.user.owner.auth_type, "OIDC")
        self.assertEqual(self.user.first_name, "Oidc")
        self.assertEqual(self.user.last_name, "User")
        self.assertEqual(self.user.email, "oidc@example.com")
        self.assertEqual(self.user.owner.affiliation, "member")
        self.assertTrue(AccessGroup.objects.filter(code_name="oidc_group").exists())

    @patch("src.apps.authentication.services.users.populator.get_ldap_conn")
    @patch("src.apps.authentication.services.users.populator.get_ldap_entry")
    @patch("src.apps.authentication.services.users.populator.auth_settings")
    def test_populate_from_ldap(self, mock_settings, mock_get_entry, mock_get_conn):
        """
        Tests user attribute synchronization from LDAP directory entries.
        """
        mock_settings.ldap_server = {"url": "ldap://localhost"}
        mock_settings.ldap_mapping_attributes = {
            "mail": "mail",
            "first_name": "givenName",
            "last_name": "sn",
            "primaryAffiliation": "eduPersonPrimaryAffiliation",
            "affiliations": "eduPersonAffiliation",
            "groups": "isMemberOf",
        }
        mock_settings.create_group_from_affiliation = True
        mock_settings.create_group_from_groups = True
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        mock_entry = {
            "mail": MagicMock(value="ldap@example.com"),
            "givenName": MagicMock(value="Ldap"),
            "sn": MagicMock(value=["User"]),
            "eduPersonPrimaryAffiliation": MagicMock(value="student"),
            "eduPersonAffiliation": MagicMock(values=["student"]),
            "isMemberOf": MagicMock(values=["ldap_group"]),
        }
        mock_get_entry.return_value = mock_entry

        self.populator.run("LDAP")

        self.user.refresh_from_db()
        self.assertEqual(self.user.owner.auth_type, "LDAP")
        self.assertEqual(self.user.first_name, "Ldap")
        self.assertEqual(self.user.last_name, "User")
        self.assertEqual(self.user.email, "ldap@example.com")
        self.assertEqual(self.user.owner.affiliation, "student")
        self.assertTrue(AccessGroup.objects.filter(code_name="ldap_group").exists())

    @patch(
        "src.apps.authentication.services.providers.cas.auth_settings",
        new_callable=lambda: AuthConfig(
            use_cas=True,
            use_ldap=False,
        ),
    )
    @patch("src.apps.authentication.services.users.populator.UserPopulator.run")
    def test_verify_cas_ticket_calls_populator(self, mock_run, mock_settings):
        """
        Tests the end-to-end flow of verifying a CAS ticket and then triggering 
        user attribute synchronization.
        """
        with patch(
            "src.apps.authentication.services.providers.cas.get_cas_client"
        ) as mock_client:
            mock_cas = MagicMock()
            mock_cas.verify_ticket.return_value = ("casuser", {"attr": "val"}, None)
            mock_client.return_value = mock_cas

            user = verify_cas_ticket("ticket", "service_url")

            self.assertIsNotNone(user)
            self.assertEqual(user.username, "casuser")
            mock_run.assert_called_with("CAS", {"attr": "val"})
