"""Esup-Pod configuration file generator.
Create a superuser if it doesn't exist.
Launch with `python3 manage.py ensure_superuser`.
"""

import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from src.apps.authentication.models import Owner


class Command(BaseCommand):
    """
    Management command to ensure a superuser exists and is correctly configured.
    """

    help = "Create or update the Django superuser and ensure it is linked to the default Site."

    def handle(self, *args, **options):
        """Creates the superuser from environment variables if it doesn't exist."""
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not all([username, email, password]):
            self.stderr.write("Superuser environment variables are missing.")
            return

        user = self._get_or_create_superuser(User, username, email, password)
        self._ensure_owner_and_site(user)

    def _get_or_create_superuser(self, User, username, email, password):
        """Gets or creates the superuser user and ensures correct privileges."""
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
        else:
            updated = False
            if not user.is_superuser:
                user.is_superuser = True
                updated = True
            if not user.is_staff:
                user.is_staff = True
                updated = True
            if updated:
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Superuser '{username}' updated to superuser/staff privileges."
                    )
                )
            else:
                self.stdout.write(f"Superuser '{username}' already exists.")
        return user

    def _ensure_owner_and_site(self, user):
        """Ensures the Owner exists and is linked to the default Site."""
        owner = Owner.objects.filter(user=user).first()
        if not owner:
            import hashlib
            from src.apps.authentication.models.utils import SECRET_KEY

            h = hashlib.sha256((SECRET_KEY + user.username).encode("utf-8")).hexdigest()
            owner = Owner.objects.filter(hashkey=h).first()
            if owner:
                owner.user = user
                owner.save()
            else:
                owner = Owner.objects.create(user=user)

        if Site.objects.exists():
            site = Site.objects.first()
            if site not in owner.sites.all():
                owner.sites.add(site)
                owner.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Superuser '{user.username}' linked to site '{site.domain}'."
                    )
                )
