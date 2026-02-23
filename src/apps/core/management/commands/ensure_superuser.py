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
    help = "Create or update the Django superuser and ensure it is linked to the default Site."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not all([username, email, password]):
            self.stderr.write("Superuser environment variables are missing.")
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )

        if created:
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
        else:
            self.stdout.write(f"Superuser '{username}' already exists.")

        owner, _ = Owner.objects.get_or_create(user=user)

        if Site.objects.exists():
            site = Site.objects.first()
            if site not in owner.sites.all():
                owner.sites.add(site)
                owner.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Superuser '{username}' linked to site '{site.domain}'."
                    )
                )
