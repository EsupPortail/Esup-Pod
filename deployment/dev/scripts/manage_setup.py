#!/usr/bin/env python3
"""
manage_setup.py

Perform Django application setup:
    - Make migrations
    - Apply migrations
    - Collect static files
    - Ensure a Django superuser exists
    - Link the superuser to the default Site (project-specific)

All errors are printed to stderr so they can be streamed and captured
by the Docker entrypoint.

Exit codes:
    0 - Setup completed successfully
    1 - Setup failed
"""

import os
import sys
import subprocess


def run_command(command: str, description: str) -> None:
    """
    Run a shell command and exit if it fails.

    :param command: Command to execute
    :param description: Human-readable step description
    """
    print(f"[Python] {description}...")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(
            f"[Python] Command failed: {command}",
            file=sys.stderr,
        )
        sys.exit(1)


def setup_superuser() -> None:
    """
    Create or update the Django superuser and ensure it is linked
    to the default Site.
    """
    import django

    django.setup()

    from django.contrib.auth import get_user_model
    from django.contrib.sites.models import Site
    from src.apps.authentication.models import Owner

    User = get_user_model()

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

    if not all([username, email, password]):
        print(
            "[Python] Superuser environment variables are missing.",
            file=sys.stderr,
        )
        sys.exit(1)

    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email},
    )

    if created:
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"[Python] Superuser '{username}' created.")
    else:
        print(f"[Python] Superuser '{username}' already exists.")

    owner, _ = Owner.objects.get_or_create(user=user)

    if Site.objects.exists():
        site = Site.objects.first()
        if site not in owner.sites.all():
            owner.sites.add(site)
            owner.save()
            print(
                f"[Python] Superuser '{username}' linked "
                f"to site '{site.domain}'."
            )


def main() -> None:
    """
    Main Django setup workflow.
    """
    print("[Python] Starting Django setup...")

    run_command(
        "python manage.py makemigrations --no-input",
        "Running makemigrations",
    )

    run_command(
        "python manage.py migrate --noinput",
        "Applying database migrations",
    )

    run_command(
        "python manage.py collectstatic --noinput --clear",
        "Collecting static files",
    )

    try:
        setup_superuser()
    except Exception as exc:
        print(
            f"[Python] Superuser setup failed: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    print("[Python] Django setup completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
