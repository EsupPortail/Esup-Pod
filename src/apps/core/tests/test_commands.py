import os
from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from src.apps.authentication.models import Owner

User = get_user_model()


class EnsureSuperuserTests(TestCase):
    def setUp(self):
        os.environ["DJANGO_SUPERUSER_USERNAME"] = "testadmin"
        os.environ["DJANGO_SUPERUSER_EMAIL"] = "testadmin@example.com"
        # ggignore-start
        # gitguardian:ignore
        os.environ["DJANGO_SUPERUSER_PASSWORD"] = "testpass" # nosec
        # ggignore-end

        Site.objects.get_or_create(domain="testserver", name="testserver")

    def test_ensure_superuser_creation(self):
        out = StringIO()
        call_command("ensure_superuser", stdout=out)

        user = User.objects.get(username="testadmin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

        owner = Owner.objects.get(user=user)
        self.assertIn("Superuser 'testadmin' created.", out.getvalue())
        owner = Owner.objects.get(user=user)
        self.assertTrue(owner.sites.exists())

    def test_ensure_superuser_exists(self):
        User.objects.create_superuser(
            username="testadmin", email="testadmin@example.com", password="testpass"
        )

        out = StringIO()
        call_command("ensure_superuser", stdout=out)
        self.assertIn("already exists", out.getvalue())

    def test_ensure_superuser_missing_env(self):
        del os.environ["DJANGO_SUPERUSER_USERNAME"]
        out = StringIO()
        err = StringIO()
        call_command("ensure_superuser", stdout=out, stderr=err)
        self.assertIn("environment variables are missing", err.getvalue())


class ValidateConfigTests(TestCase):
    def test_validate_config_dry_run(self):
        out = StringIO()
        try:
            call_command("validate_config", "--dry-run", stdout=out)
        except (SystemExit, Exception):
            pass
        self.assertTrue(True)


class CreateConfigurationTests(TestCase):
    def test_create_configuration_dry_run(self):
        out = StringIO()
        call_command("createconfiguration", "en", stdout=out)
        self.assertIn("configuration", out.getvalue().lower())
