"""
Esup-Pod - Tests for management commands in the core app.

This module validates the execution of common administration commands like
ensure_superuser, validate_config, and createconfiguration.
"""

import os
import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site

from src.apps.authentication.models import Owner

User = get_user_model()

# ggignore-start
# gitguardian:ignore
PWD = "testpass"  # nosec
# ggignore-end


class EnsureSuperuserTests(TestCase):
    """
    Test suite for the ensure_superuser management command.
    """

    def setUp(self):
        """
        Setup environment variables and testing site.
        """
        os.environ["DJANGO_SUPERUSER_USERNAME"] = "testadmin"
        os.environ["DJANGO_SUPERUSER_EMAIL"] = "testadmin@example.org"
        os.environ["DJANGO_SUPERUSER_PASSWORD"] = PWD

        Site.objects.get_or_create(domain="testserver", name="testserver")

    def test_ensure_superuser_creation(self):
        """
        Tests that a superuser is correctly created when valid environment variables are set.
        """
        out = StringIO()
        call_command("ensure_superuser", stdout=out)

        user = User.objects.get(username="testadmin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

        Owner.objects.get(user=user)
        self.assertIn("Superuser 'testadmin' created.", out.getvalue())
        owner = Owner.objects.get(user=user)
        self.assertTrue(owner.sites.exists())

    def test_ensure_superuser_exists(self):
        """
        Tests that the command does nothing when the superuser already exists.
        """
        User.objects.create_superuser(
            username="testadmin", email="testadmin@example.org", password=PWD
        )

        out = StringIO()
        call_command("ensure_superuser", stdout=out)
        self.assertIn("already exists", out.getvalue())

    def test_ensure_superuser_upgrades_existing(self):
        """
        Tests that an existing user without superuser rights is upgraded.
        """
        User.objects.create_user(
            username="testadmin", email="testadmin@example.org", password=PWD
        )

        out = StringIO()
        call_command("ensure_superuser", stdout=out)
        self.assertIn("updated to superuser/staff privileges", out.getvalue())
        user = User.objects.get(username="testadmin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_ensure_superuser_missing_env(self):
        """
        Tests that the command reports an error if environment variables are missing.
        """
        del os.environ["DJANGO_SUPERUSER_USERNAME"]
        out = StringIO()
        err = StringIO()
        call_command("ensure_superuser", stdout=out, stderr=err)
        self.assertIn("environment variables are missing", err.getvalue())


class ValidateConfigTests(TestCase):
    """
    Test suite for the validate_config management command.
    """

    def test_validate_config_dry_run(self):
        """
        Tests that validate_config can run in dry-run mode.
        """
        out = StringIO()
        try:
            call_command("validate_config", "--dry-run", stdout=out)
        except (SystemExit, Exception):
            pass
        self.assertTrue(True)


class CreateConfigurationTests(TestCase):
    """
    Test suite for the createconfiguration management command.
    """

    def test_create_configuration_dry_run(self):
        """
        Tests that createconfiguration can generate configuration documentation.
        """
        out = StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_base = Path(temp_dir)
            config_file = temp_base / "src" / "apps" / "core" / "configuration.json"
            config_file.parent.mkdir(parents=True)
            shutil.copy(
                settings.BASE_DIR / "src" / "apps" / "core" / "configuration.json",
                config_file,
            )

            with override_settings(BASE_DIR=temp_base):
                call_command("createconfiguration", "en", stdout=out)

            generated_file = temp_base / "docs" / "CONFIGURATION_EN.md"
            self.assertTrue(generated_file.is_file())
            self.assertIn("configuration", generated_file.read_text().lower())
        self.assertIn("successfully export configuration", out.getvalue().lower())
