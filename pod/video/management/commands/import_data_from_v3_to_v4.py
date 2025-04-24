"""
Import data from Pod v3.8.x JSON file to Pod v4.0.x.

This script is designed to import data from a Pod v3.8.x JSON file into a Pod v4.0.x database.
It supports both MariaDB/MySQL and PostgreSQL databases. The script reads data from a specified JSON file,
processes it, and inserts it into the appropriate tables in the Pod v4 database.
It also handles tag management using the Tagulous library.
The script includes options for dry runs to simulate the import process without
making any changes to the database.

Key Features:
- Import JSON file, generated with specified tables from the Pod v3 database.
- Handles both MariaDB/MySQL and PostgreSQL databases.
- Creates a directory to store the exported data if it does not already exist (normally useless).
- Provides detailed success and error messages using Django's management command framework.
- Supports tag management for videos and recorders via Tagulous.
- Can execute Bash commands to create the database and initialize data.
- Safe error handling and simulation mode supported.

Important notes:
 - The JSON file must be found at BASE_DIR/data_from_v3_to_v4/v3_exported_tables.json
Example: /usr/local/django_projects/data_from_v3_to_v4/v3_exported_tables.json
 - Elasticsearch must be installed, properly configured and running
 - Set DEBUG = False to settings_local.py to avoid warnings/debug/info noise.
 - Can be executed with a MariaDB/MySQL or Postgresql database.
 - If you encounter an error "Too many connections" type, you can increase the value of
the time_sleep variable. Processing will take longer, but will be able to complete without error.
 - This script can be rerun as many times as required, the data are deleted before insertion.
 - After this, do not forget to make Pod v3 MEDIA_ROOT accessible to Pod v4 servers.
 - After this, do not forget to re-index all videos for Elasticsearch with: python manage.py index_videos --all

Usage:
Run the script using Django's management command:
    python manage.py import_data_from_v3_to_v4
Arguments:
 --dry: Simulates what will be achieved (default=False).
 --createDB: Execute Bash commands to create tables in the database and add initial data (see make createDB). Database must be empty. (default=False).
 --onlytags: Processes only tags (default=False). Useful if you encounter the 'Too many connections' problem for tags management.

Example: python manage.py import_data_from_v3_to_v4 --dry

Functions:
- add_arguments: Adds command-line arguments for the script.
- handle: Main entry point for the command, handling the overall process.
- execute_bash_commands: Executes Bash commands to create the tables of the database and add initial data.
- process: Main function to process the JSON data and insert it into the database.
- create_directory: Creates a directory to store data if it does not exist (normally useless).
- verify_json_file: Checks for the existence of the JSON file and optionally displays a dry-run message.
- display_dry_run_tables: Lists the tables that would be processed in dry-run mode.
- import_data: Performs the actual import into the database from the JSON structure.
- import_table_data: Deletes old data and inserts rows for a given table.
- delete_old_tag_data: Deletes old tag data from the database.
- reset_auto_increment: Reset auto increment for a table (manage for for Postgre or Mysql/MariaDB).
- process_tags: Processes tags for videos and recorders.
- process_video_tags: Processes tags specifically for videos.
- process_recorder_tags: Processes tags specifically for recorders.
- add_tags_to_video: Adds tags to a video.
- add_tags_to_recorder: Adds tags to a recorder.
- handle_exception: Handles exceptions that occur during the tagging process.
- quote_identifier: Quotes identifiers for SQL queries based on the database type.
"""
import json
import logging
import os
import subprocess
import time
import urllib3
from typing import Any, Dict, List

from contextlib import contextmanager
from django.core.management.base import BaseCommand
from django.db import connection, close_old_connections
from django.db import transaction
from django.conf import settings
from pod.video.models import Video
from pod.recorder.models import Recorder

# Base directory
BASE_DIR = getattr(settings, "BASE_DIR", "/home/pod/django_projects/podv3/pod")
# Pod version
VERSION = getattr(settings, "VERSION", "undefined")

# Time sleep to avoid Too many connections error
time_sleep = 0.3

# Disable InsecureRequest warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Disable warnings
logging.captureWarnings(True)
logging.getLogger('urllib3').setLevel(logging.ERROR)


@contextmanager
def managed_cursor():
    """Context manager to automatically close the database cursor."""
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()


class Command(BaseCommand):
    """Main command class for importing data from Pod v3 JSON file to Pod v4 database."""

    help = "Import data from Pod v3 JSON file, to Pod v4"

    def add_arguments(self, parser) -> None:
        """Allow arguments to be used with the command."""
        parser.add_argument(
            "--dry",
            help="Simulates what will be achieved (default=False).",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "--createDB",
            help="Execute Bash commands to create tables in the database and add initial data (see make createDB). Database must be empty. (default=False).",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "--onlytags",
            help="Processes only tags (default=False).",
            action="store_true",
            default=False,
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command call."""

        self.stdout.write(self.style.SUCCESS("***Start import Pod3 JSON file to Pod v4 database***"))

        if options["dry"]:
            self.stdout.write(
                self.style.NOTICE(
                    "\n----------------------------------------------------------------\n"
                    "| Simulation mode ('dry'). No database import, only print info.|"
                    "\n----------------------------------------------------------------\n"
                )
            )

        # Manage Pod version
        if VERSION[:3] == "4.0":
            self.stdout.write(
                self.style.SUCCESS(
                    f" - Pod version: {VERSION}. "
                    "This script can be achieved with this Pod version. "
                    "The process continues."
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f" - Pod version: {VERSION}. "
                    "This script can only be used for Pod version 4.0.x. "
                    "The process stops here!"
                )
            )
            # Stop process
            return

        # Check database
        backend = connection.vendor
        if backend != 'mysql' and backend != 'postgresql':
            self.stdout.write(
                self.style.ERROR(
                    "This script can only be used with a MariaDB, MySQL or Postgresql database. "
                    "The process stops here!"
                )
            )
            # Stop process
            return

        if options["dry"]:
            if options["createDB"]:
                self.stdout.write(self.style.SUCCESS(" - The command make createDB will be executed."))
        else:
            if options["createDB"]:
                self.execute_bash_commands()

        # Main function
        self.process(options)

    def execute_bash_commands(self) -> None:
        """Execute Bash commands to create the tables of the database and add initial data."""
        commands = [
            "make createDB",
        ]

        for command in commands:
            try:
                subprocess.run(command, shell=True, check=True)
                self.stdout.write(self.style.SUCCESS(f"Command executed successfully: {command}"))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f"Command failed: {command}. Error: {e}"))

    def process(self, options: Dict[str, Any]) -> None:
        """Main process to import data."""

        # Define directory and JSON file
        output_directory = "../../data_from_v3_to_v4/"
        output_json_file = "v3_exported_tables.json"

        # Create data directory, if necessary (normally useless)
        self.create_directory(output_directory)

        # Read the JSON file
        json_file = os.path.join(BASE_DIR, f"{output_directory}{output_json_file}")

        if not self.verify_json_file(json_file, options):
            return

        with open(json_file, 'r') as f:
            data = json.load(f)

        # Dry mode
        if options["dry"]:
            self.display_dry_run_tables(data, options)
            return

        # Start import data
        self.import_data(data, json_file, options)

    def create_directory(self, output_directory: str) -> None:
        """Create directory to store all the data."""
        self.stdout.write(self.style.SUCCESS(" - Create directory data if necessary"))
        os.makedirs(os.path.join(BASE_DIR, output_directory), exist_ok=True)

    def verify_json_file(self, json_file: str, options: Dict[str, Any]) -> bool:
        """Verify the presence of the JSON file and optionally display a dry-run message."""
        if options["dry"]:
            self.stdout.write(self.style.SUCCESS(f" - The JSON file {json_file} will be processed."))

        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f' - The JSON file {json_file} does not exist.'))
            return False

        return True

    def display_dry_run_tables(self, data: Dict[str, Any], options: Dict[str, Any]) -> None:
        """Display tables that would be processed in dry mode."""
        if options["onlytags"]:
            self.stdout.write(self.style.SUCCESS(" - Only the tables useful for tags management will be processed."))
        else:
            for table in data:
                self.stdout.write(self.style.SUCCESS(f" - The table {table} will be processed."))

    def import_data(self, data: Dict[str, Any], json_file: str, options: Dict[str, Any]) -> None:
        """Import data into the database."""
        error = False

        for table, rows in data.items():
            with connection.cursor() as cursor:
                # Tags management: use of Tagulous
                if table in ["video_tagging_tag_2_tagulous", "recorder_tagging_tag_2_tagulous"]:
                    # Delete old data
                    self.delete_old_tag_data(cursor, table)
                    # # Process for tags
                    self.process_tags(table, rows)
                else:
                    if not options["onlytags"]:
                        try:
                            self.import_table_data(cursor, table, rows)
                            self.stdout.write(self.style.SUCCESS(f" - The table {table} has been processed."))
                        except Exception as e:
                            error = True
                            self.stdout.write(self.style.ERROR(f" - The table {table} has not been processed. Error: {e}"))

        if error:
            self.stdout.write(self.style.ERROR(f'Not all data has been imported from {json_file}.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Data has been successfully imported from {json_file}.'))

    def import_table_data(self, cursor, table: str, rows: List[Dict[str, Any]]) -> None:
        """Delete old data and insert new rows into the specified table."""

        # Delete existing data
        cursor.execute(f"DELETE FROM {self.quote_identifier(table)}")
        # Get column names
        cursor.execute(f"SHOW COLUMNS FROM {self.quote_identifier(table)}")
        columns = [self.quote_identifier(row[0]) for row in cursor.fetchall()]
        # Create insert query
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {self.quote_identifier(table)} ({', '.join(columns)}) VALUES ({placeholders})"

        # Execute insert queries
        for row in rows:
            values = []
            for column in columns:
                try:
                    values.append(row[column.strip('`').strip('"')])
                except Exception as e:
                    # Useful if you migrate a different version than 3.8.4
                    # 'video_video' table, 'order' column was added in 3.8.4 version
                    values.append(None)
                    if table != "video_video" or column.strip('`').strip('"') != 'order':
                        # Warning: lost value
                        self.stdout.write(
                            self.style.WARNING(
                                f" - Value error for table {table} column {column}. Error: {e}"
                            )
                        )
            cursor.execute(insert_query, values)

    def delete_old_tag_data(self, cursor, table: str) -> None:
        """Delete old tag data for the given table."""
        if table == "video_tagging_tag_2_tagulous":
            self.stdout.write(self.style.SUCCESS(" - Delete old tags for videos"))
            cursor.execute(f"DELETE FROM {self.quote_identifier('video_tagulous_video_tags')}")
            self.reset_auto_increment(cursor, 'video_video_tags', 'id')
            cursor.execute(f"DELETE FROM {self.quote_identifier('video_video_tags')}")
            cursor.execute(f"ALTER TABLE {self.quote_identifier('video_video_tags')} AUTO_INCREMENT = 1")
        elif table == "recorder_tagging_tag_2_tagulous":
            self.stdout.write(self.style.SUCCESS(" - Delete old tags for recorders"))
            cursor.execute(f"DELETE FROM {self.quote_identifier('recorder_tagulous_recorder_tags')}")
            self.reset_auto_increment(cursor, 'recorder_recorder_tags', 'id')
            cursor.execute(f"DELETE FROM {self.quote_identifier('recorder_recorder_tags')}")
            cursor.execute(f"ALTER TABLE {self.quote_identifier('recorder_recorder_tags')} AUTO_INCREMENT = 1")

    def reset_auto_increment(self, cursor, table: str, id_column: int = 'id') -> None:
        """Reset auto increment for a table (manage for for Postgre or Mysql/MariaDB)."""
        backend = connection.vendor
        quoted_table = self.quote_identifier(table)
        if backend == 'mysql':
            cursor.execute(f"ALTER TABLE {quoted_table} AUTO_INCREMENT = 1")
        elif backend == 'postgresql':
            # PostgreSQL: need to reset the sequence manually
            sequence_name = f"{table}_{id_column}_seq"
            quoted_seq = self.quote_identifier(sequence_name)
            cursor.execute(f"ALTER SEQUENCE {quoted_seq} RESTART WITH 1")

    def process_tags(self, table: str, rows: list) -> None:
        """Process tags for the given table and rows."""
        try:
            if table == 'video_tagging_tag_2_tagulous':
                self.process_video_tags(rows)
            else:
                self.process_recorder_tags(rows)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Tag management has not been completed. Error: {e}"))

    def process_video_tags(self, rows: List[Dict[str, Any]]) -> None:
        """Process tags for videos."""
        number_videos_processed = 0
        self.stdout.write(self.style.SUCCESS(" - Start of tags management for videos"))
        for row in rows:
            number_videos_processed += 1
            if number_videos_processed % 100 == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"   * Processing, for tags, of the batch of videos {number_videos_processed-100}-{number_videos_processed} achieved"
                    )
                )
            self.add_tags_to_video(row['video_id'], row['tag_name'])
            close_old_connections()
            connection.close()
            time.sleep(time_sleep)
        self.stdout.write(self.style.SUCCESS(" - End of tags management for videos"))

    def process_recorder_tags(self, rows: List[Dict[str, Any]]) -> None:
        """Process tags for recorders."""
        self.stdout.write(self.style.SUCCESS(" - Start of tags management for recorders"))
        for row in rows:
            self.add_tags_to_recorder(row['recorder_id'], row['tag_name'])
            close_old_connections()
            connection.close()
            time.sleep(time_sleep)
        self.stdout.write(self.style.SUCCESS(" - End of tags management for recorders"))

    def add_tags_to_video(self, video_id: int, tags: str) -> None:
        """Add tags to video."""
        try:
            with transaction.atomic():
                video = Video.objects.get(id=video_id)
                video.tags = tags
                video.save()
        except Exception as e:
            self.handle_exception(e, video_id, "video")
        finally:
            # Close unused connections
            close_old_connections()

    def add_tags_to_recorder(self, recorder_id: int, tags: str) -> None:
        """Add tags to recorder."""
        try:
            with transaction.atomic():
                recorder = Recorder.objects.get(id=recorder_id)
                recorder.tags = tags
                recorder.save()
        except Exception as e:
            self.handle_exception(e, recorder_id, "recorder")
        finally:
            # Close unused connections
            close_old_connections()

    def handle_exception(self, e: Exception, entity_id: int, entity_type: str) -> None:
        """Handle exceptions that occur during the tagging process."""
        if "Too many connections" in str(e):
            self.stdout.write(
                self.style.ERROR(
                    f"Error: tags error for {entity_type} {entity_id}: {e}."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Warning: tags error for {entity_type} {entity_id}: {e} "
                    f"This {entity_type} had to be deleted in Pod v3, but the keywords were kept in the database."
                )
            )

    def quote_identifier(self, identifier: str) -> str:
        """Quote identifier for SQL queries based on the database type."""
        backend = connection.vendor
        if backend == 'postgresql':
            return f'"{identifier}"'
        elif backend == 'mysql':
            return f'`{identifier}`'
        else:
            return identifier
