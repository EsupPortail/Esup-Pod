"""Tests the forms for playlist module."""
from django.utils.translation import ugettext as _
from django.test import override_settings, TestCase

from ...playlist.forms import PlaylistForm, PlaylistRemoveForm, PlaylistPasswordForm
from ...playlist.apps import FAVORITE_PLAYLIST_NAME


FIELD_REQUIRED_ERROR_MESSAGE = _("This field is required.")

# ggignore-start
# gitguardian:ignore
PWD = "thisisnotpassword"
# ggignore-end


class PlaylistFormTest(TestCase):
    """
    Tests for the playlist form.

    Args:
        TestCase (::class::`django.test.TestCase`): The test case.
    """

    @override_settings(USE_PLAYLIST=True)
    def test_valid_data_for_public_playlist(self):
        """
        Test the form with valid data for a public playlist.
        """
        form = PlaylistForm(data={
            "name": "Test Playlist",
            "description": "Test description",
            "visibility": "public",
            "password": "",
            "autoplay": True,
            "additional_owners": [],
        })
        self.assertTrue(form.is_valid())
        print(" --->  test_valid_data_for_public_playlist ok")

    @override_settings(USE_PLAYLIST=True)
    def test_valid_data_for_private_playlist(self):
        """
        Test the form with valid data for a private playlist.
        """
        form = PlaylistForm(data={
            "name": "Test Playlist",
            "description": "Test description",
            "visibility": "private",
            "password": "",
            "autoplay": True,
            "additional_owners": [],
        })
        self.assertTrue(form.is_valid())
        print(" --->  test_valid_data_for_private_playlist ok")

    @override_settings(USE_PLAYLIST=True)
    def test_valid_data_for_protected_playlist(self):
        """
        Test the form with valid data for a protected playlist.
        """
        form = PlaylistForm(data={
            "name": "Test Playlist",
            "description": "Test description",
            "visibility": "protected",
            "password": PWD,
            "autoplay": True,
            "additional_owners": [],
        })
        self.assertTrue(form.is_valid())
        print(" --->  test_valid_data_for_protected_playlist ok")

    @override_settings(USE_PLAYLIST=True)
    def test_invalid_data_for_protected_playlist(self):
        """
        Test the form with invalid data for a protected playlist.
        """
        form = PlaylistForm(data={
            "name": "Test Playlist",
            "description": "Test description",
            "visibility": "protected",
            "password": "",
            "autoplay": True,
            "additional_owners": [],
        })
        self.assertFalse(form.is_valid())
        print(" --->  test_invalid_data_for_protected_playlist ok")

    @override_settings(USE_PLAYLIST=True)
    def test_name_validation_for_public_playlist(self):
        """
        Test if the name validation works correctly for a public playlist.
        """
        valid_form = PlaylistForm(data={
            "name": "Valid Name",
            "visibility": "public",
        })
        invalid_form = PlaylistForm(data={
            "name": FAVORITE_PLAYLIST_NAME,
            "visibility": "public",
        })
        self.assertTrue(valid_form.is_valid())
        self.assertFalse(invalid_form.is_valid())
        self.assertEqual(invalid_form.errors["name"][0], _("You cannot create a playlist named \"Favorites\""))
        print(" --->  test_name_validation_for_public_playlist ok")

    @override_settings(USE_PLAYLIST=True)
    def test_name_validation_for_private_playlist(self):
        """
        Test if the name validation works correctly for a private playlist.
        """
        valid_form = PlaylistForm(data={
            "name": "Valid Name",
            "visibility": "private",
        })
        invalid_form = PlaylistForm(data={
            "name": FAVORITE_PLAYLIST_NAME,
            "visibility": "private",
        })
        self.assertTrue(valid_form.is_valid())
        self.assertFalse(invalid_form.is_valid())
        self.assertEqual(invalid_form.errors["name"][0], _("You cannot create a playlist named \"Favorites\""))
        print(" --->  test_name_validation_for_private_playlist ok")

    @override_settings(USE_PLAYLIST=True)
    def test_name_validation_for_protected_playlist(self):
        """
        Test if the name validation works correctly for a protected playlist.
        """
        valid_form = PlaylistForm(data={
            "name": "Valid Name",
            "visibility": "protected",
            "password": PWD,
        })
        invalid_form = PlaylistForm(data={
            "name": FAVORITE_PLAYLIST_NAME,
            "visibility": "protected",
            "password": PWD,
        })
        self.assertTrue(valid_form.is_valid())
        self.assertFalse(invalid_form.is_valid())
        self.assertEqual(invalid_form.errors["name"][0], _("You cannot create a playlist named \"Favorites\""))
        print(" --->  test_name_validation_for_protected_playlist ok")

    @override_settings(USE_PLAYLIST=True)
    def test_blank_data_for_public_playlist(self):
        """
        Test the form with blank data for a public playlist.
        """
        form = PlaylistForm(data={})
        self.assertFalse(form.is_valid())
        self.assertLessEqual(1, len(form.errors))
        print(" --->  test_blank_data_for_public_playlist ok")


class PlaylistRemoveFormTest(TestCase):
    """
    Tests to remove a playlist form.

    Args:
        TestCase (::class::`django.test.TestCase`): The test case.
    """

    @override_settings(USE_PLAYLIST=True)
    def test_valid_data(self):
        """
        Test the form with valid data.
        """
        form = PlaylistRemoveForm(data={"agree": True})
        self.assertTrue(form.is_valid())
        print(" --->  test_valid_data ok")

    @override_settings(USE_PLAYLIST=True)
    def test_agree_required(self):
        """
        Test the form with agree field not selected and not provided.
        """
        agree_not_selected_form = PlaylistRemoveForm(data={"agree": False})
        agree_not_provided_form = PlaylistRemoveForm(data={})
        self.assertFalse(agree_not_selected_form.is_valid())
        self.assertEqual(len(agree_not_selected_form.errors), 1)
        self.assertEqual(agree_not_selected_form.errors["agree"][0], FIELD_REQUIRED_ERROR_MESSAGE)
        self.assertFalse(agree_not_provided_form.is_valid())
        self.assertEqual(len(agree_not_provided_form.errors), 1)
        self.assertEqual(agree_not_provided_form.errors["agree"][0], FIELD_REQUIRED_ERROR_MESSAGE)
        print(" --->  test_agree_required ok")

    @override_settings(USE_PLAYLIST=True)
    def test_blank_data(self):
        """
        Test the form with empty data.
        """
        form = PlaylistRemoveForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(form.errors["agree"][0], FIELD_REQUIRED_ERROR_MESSAGE)
        print(" --->  test_blank_data ok")


class PlaylistPasswordFormTests(TestCase):
    """
    Tests for playlist password form.

    Args:
        TestCase (::class::`django.test.TestCase`): The test case.
    """

    @override_settings(USE_PLAYLIST=True)
    def test_valid_data(self):
        """
        Test the form with valid data.
        """
        form = PlaylistPasswordForm(data={"password": PWD})
        self.assertTrue(form.is_valid())
        print(" --->  test_valid_data ok")

    @override_settings(USE_PLAYLIST=True)
    def test_password_required(self):
        """
        Test the form with password field empty and not provided.
        """
        password_not_provided_form = PlaylistPasswordForm(data={})
        empty_password_form = PlaylistPasswordForm(data={"password": ""})
        self.assertFalse(password_not_provided_form.is_valid())
        self.assertEqual(len(password_not_provided_form.errors), 1)
        self.assertEqual(password_not_provided_form.errors["password"][0], FIELD_REQUIRED_ERROR_MESSAGE)
        self.assertFalse(empty_password_form.is_valid())
        self.assertEqual(len(empty_password_form.errors), 1)
        self.assertEqual(empty_password_form.errors["password"][0], FIELD_REQUIRED_ERROR_MESSAGE)
        print(" --->  test_password_required ok")

    @override_settings(USE_PLAYLIST=True)
    def test_blank_data(self):
        """
        Test the form with empty data.
        """
        form = PlaylistPasswordForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertEqual(form.errors["password"][0], FIELD_REQUIRED_ERROR_MESSAGE)
        print(" --->  test_blank_data ok")
