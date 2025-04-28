import os
from django.core.management.base import BaseCommand
from django.contrib import flatpages


class Command(BaseCommand):
    help = "Delete migration files and .pyc files of the flatpages app"

    def handle(self, *args, **kwargs):
        # Find the migrations directory of flatpages
        flatpages_dir = os.path.dirname(flatpages.__file__)
        migrations_dir = os.path.join(flatpages_dir, "migrations")

        # Check if the migrations directory exists
        if os.path.isdir(migrations_dir):
            # Delete all migration files except __init__.py
            for filename in os.listdir(migrations_dir):
                if filename != "__init__.py" and filename.endswith(".py"):
                    file_path = os.path.join(migrations_dir, filename)
                    os.remove(file_path)
                    self.stdout.write(f"Deleted: {file_path}")

            # Delete all .pyc files in the migrations directory
            for root, dirs, files in os.walk(migrations_dir):
                for file in files:
                    if file.endswith(".pyc"):
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        self.stdout.write(f"Deleted: {file_path}")

            self.stdout.write(
                self.style.SUCCESS(
                    "Flatpages migration files and .pyc files have been deleted."
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR("Flatpages migrations directory not found.")
            )
