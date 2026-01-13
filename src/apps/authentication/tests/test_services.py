from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from ..services import UserPopulator, verify_cas_ticket

User = get_user_model()


class TestUserPopulator(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser", email="test@example.com")
        self.populator = UserPopulator(self.user)

    def test_init_creates_owner(self):
        user_no_owner = User.objects.create(username="noowner")
        UserPopulator(user_no_owner)
        self.assertTrue(hasattr(user_no_owner, "owner"))
        self.assertIsNotNone(user_no_owner.owner)

    def test_populate_from_cas_basic(self):
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

        # Check groups - depends on create_group settings, but let's assume default behaviour
        # or mock settings.
        # By default CREATE_GROUP_FROM_GROUPS might be False.
        # Let's verify owner attribute is updated.

    @override_settings(POPULATE_USER="CAS")
    @patch("src.apps.authentication.services.users.populator.UserPopulator.run")
    def test_verify_cas_ticket_calls_populator(self, mock_run):
        with patch("src.apps.authentication.services.providers.cas.get_cas_client") as mock_client:
            mock_cas = MagicMock()
            mock_cas.verify_ticket.return_value = ("casuser", {"attr": "val"}, None)
            mock_client.return_value = mock_cas

            user = verify_cas_ticket("ticket", "service_url")

            self.assertIsNotNone(user)
            self.assertEqual(user.username, "casuser")
            mock_run.assert_called_with("CAS", {"attr": "val"})
