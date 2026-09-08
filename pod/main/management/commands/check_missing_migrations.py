"""Check that applied Django migrations still have a migration file."""

import os

from django.db import connections
from django.apps import apps
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """Report migrations recorded in the database but missing from the code."""

    help = "List migrations recorded in the database whose files are missing"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--database",
            default="default",
            help="Database to inspect (default: %(default)s)",
        )
        parser.add_argument(
            "--fail-on-missing",
            action="store_true",
            help="Exit with an error status when missing migrations are found",
        )

    def handle(self, *args, **options) -> None:
        """Compare recorded migrations with migrations discovered on disk."""
        database = options["database"]
        db_connection = connections[database]
        loader = MigrationLoader(
            db_connection, load=False, ignore_no_migrations=True
        )
        loader.load_disk()
        applied_migrations = set(
            MigrationRecorder(db_connection)
            .migration_qs.values_list("app", "name")
        )
        missing_migrations = sorted(
            applied_migrations.difference(loader.disk_migrations)
        )

        if missing_migrations:
            self.stdout.write(self.style.ERROR("# Missing migration files:"))
            self.stdout.write("app_label,migration_name,expected_path")
            for app_label, migration_name in missing_migrations:
                expected_path = self.get_expected_path(
                    loader, app_label, migration_name
                )
                self.stdout.write(
                    f"{app_label},{migration_name},{expected_path}"
                )
            if options["fail_on_missing"]:
                raise CommandError(
                    f"{len(missing_migrations)} migration file(s) missing."
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("No missing migration files found.")
            )

    def get_expected_path(
        self, loader: MigrationLoader, app_label: str, migration_name: str
    ) -> str:
        """Return the path where a missing migration file should be located."""
        migration_package = loader.disk_migrations.get(app_label)
        if migration_package:
            migration_directory = next(iter(migration_package.__path__))
        else:
            app_config = apps.get_app_config(app_label)
            migration_directory = os.path.join(app_config.path, "migrations")
        return os.path.join(migration_directory, f"{migration_name}.py")
