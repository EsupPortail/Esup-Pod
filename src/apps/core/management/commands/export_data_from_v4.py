"""Esup-Pod - Export data from Pod v4.x to a JSON file for a future Pod version.

This script is designed to export data from a Pod v4.x database to a JSON file,
which can then be used to migrate the data to a future Pod version (e.g. v5.x).
The script handles both MariaDB/MySQL and PostgreSQL databases, adapting SQL queries
as needed.

Key Features:
- Exports specified tables from the Pod v4 database to a JSON file.
- Handles both MariaDB/MySQL and PostgreSQL databases.
- Creates a directory to store the exported data if it does not already exist.
- Converts datetime, time, and date objects to JSON-serializable formats.
- Applies data fixes during export (e.g. corrects invalid recurring_until dates
  in the meeting table) to ensure the output is compatible with v5 constraints.
- Provides detailed success and error messages using Django's management command
  framework.

Important notes:
- In Pod v4, the legacy django-tagging tables (tagging_taggeditem, tagging_tag)
  no longer exist. Tags are now handled by Tagulous and stored in separate tables:
  video_tagulous_video_tags, video_video_tags, recorder_tagulous_recorder_tags,
  and recorder_recorder_tags. The virtual tag tables
  (video_tagging_tag_2_tagulous, recorder_tagging_tag_2_tagulous) are kept in the
  table list for forward-compatibility but will be silently skipped if absent.
- The JSON output file is written to: BASE_DIR/../../data_from_v4_to_v5/v4_exported_to_v5.json
  Example: /usr/local/django_projects/data_from_v4_to_v5/v4_exported_to_v5.json
- This script can be rerun as many times as required; the JSON file is regenerated
  each time.

Usage:
    Run the script using Django's management command:
        python manage.py export_data_from_v4

Dependencies:
- Django
- Settings configured with the database connection details (DATABASES, BASE_DIR, VERSION).

Functions:
- create_directory: Creates the directory to store the exported data.
- get_table_names: Returns the list of tables to export.
- check_table_existence: Checks if the specified tables exist in the database
  (with specific handling for virtual tag table names).
- fetch_table_data: Fetches all rows and column names from a specific table.
- fetch_tag_data: Fetches tag data with special SQL for the legacy tagging system
  (MySQL and PostgreSQL compatible).
- convert_to_json: Converts rows of data to a list of JSON-serializable dicts,
  with fixes applied per table (e.g. recurring_until correction for meeting).
- export_tables_to_json: Iterates over all tables, fetches data, and writes the
  result to a JSON file.
- process: Main process to orchestrate the full data export.
"""

import json
import os
from datetime import date, datetime, time
from typing import Any, Dict, List, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

# Base directory of the Pod v4 application
BASE_DIR = getattr(settings, "BASE_DIR", "/usr/local/django_projects/podv4/pod")
# Pod version, used to validate that this script is run on the correct version
VERSION = getattr(settings, "VERSION", "undefined")


class Command(BaseCommand):
    """Management command to export Pod v4 database tables to a JSON file."""

    help = "Export data from Pod v4.x to a JSON file for a future Pod version"

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the management command call.

        Validates the current Pod version, then launches the export process.
        The script will only run on Pod v4.x installations to prevent accidental
        usage on incompatible versions.
        """
        self.stdout.write(
            self.style.SUCCESS("***Start export Pod4 database tables to a JSON file***")
        )

        # Validate Pod version: this script is designed for Pod v4.x only
        if VERSION.startswith("4."):
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
                    "This script can only be used for Pod version 4.x. "
                    "Please check your Pod installation. The process stops here!"
                )
            )
            # Stop process
            return

        # Launch main export process
        self.process(options)

    def create_directory(self, output_directory: str) -> None:
        """Create the output directory to store the exported JSON file.

        Args:
            output_directory: Relative path (from BASE_DIR) where the JSON file
                will be written. The directory is created if it does not exist.
        """
        self.stdout.write(self.style.SUCCESS(" - Create directory data if necessary"))
        os.makedirs(os.path.join(BASE_DIR, output_directory), exist_ok=True)

    def get_table_names(self) -> List[str]:
        """Return the list of database table names to export.

        This list covers all Pod v4 application tables. Tables that do not exist
        in the database (e.g. optional modules not installed) will be silently
        skipped by check_table_existence().

        Note: The virtual tag table names (video_tagging_tag_2_tagulous,
        recorder_tagging_tag_2_tagulous) are included for forward-compatibility
        with installations that may still use the legacy django-tagging system.
        In Pod v4, these are silently omitted because check_table_existence()
        only adds them when the underlying tagging tables are present.

        Returns:
            A list of table name strings to attempt to export.
        """
        return [
            "ai_enhancement_aienhancement",
            "authentication_accessgroup",
            "authentication_accessgroup_sites",
            "authentication_accessgroup_users",
            "authentication_groupsite",
            "authentication_groupsite_sites",
            "authentication_owner",
            "authentication_owner_accessgroups",
            "authentication_owner_sites",
            "authtoken_token",
            "auth_group",
            "auth_group_permissions",
            "auth_permission",
            "auth_user",
            "auth_user_groups",
            "auth_user_user_permissions",
            "captcha_captchastore",
            "chapter_chapter",
            "completion_contributor",
            "completion_document",
            "completion_enrichmodelqueue",
            "completion_overlay",
            "completion_track",
            "cut_cutvideo",
            "django_admin_log",
            "django_content_type",
            "django_flatpage",
            "django_flatpage_sites",
            "django_site",
            "dressing_dressing",
            "dressing_dressing_allow_to_groups",
            "dressing_dressing_owners",
            "dressing_dressing_users",
            "dressing_dressing_videos",
            "enrichment_enrichment",
            "enrichment_enrichmentgroup",
            "enrichment_enrichmentgroup_groups",
            "enrichment_enrichmentvtt",
            "import_video_externalrecording",
            "live_broadcaster",
            "live_broadcaster_manage_groups",
            "live_building",
            "live_building_sites",
            "live_event",
            "live_event_additional_owners",
            "live_event_restrict_access_to_groups",
            "live_event_videos",
            "live_event_viewers",
            "live_heartbeat",
            "live_livetranscriptrunningtask",
            "main_additionalchanneltab",
            "main_block",
            "main_block_sites",
            "main_configuration",
            "main_customfilemodel",
            "main_customimagemodel",
            "main_linkfooter",
            "main_linkfooter_sites",
            "meeting",
            "meeting_additional_owners",
            "meeting_internalrecording",
            "meeting_livegateway",
            "meeting_livestream",
            "meeting_meetingsessionlog",
            "meeting_restrict_access_to_groups",
            "playlist_playlist",
            "playlist_playlistcontent",
            "playlist_playlist_additional_owners",
            "podfile_customfilemodel",
            "podfile_customimagemodel",
            "podfile_userfolder",
            "podfile_userfolder_access_groups",
            "podfile_userfolder_users",
            "quiz_multiplechoicequestion",
            "quiz_quiz",
            "quiz_shortanswerquestion",
            "quiz_singlechoicequestion",
            "quiz_truefalsequestion",
            "recorder_recorder",
            "recorder_recorder_additional_users",
            "recorder_recorder_channel",
            "recorder_recorder_discipline",
            "recorder_recorder_restrict_access_to_groups",
            "recorder_recorder_sites",
            "recorder_recorder_tags",
            "recorder_recorder_theme",
            "recorder_recording",
            "recorder_recordingfile",
            "recorder_recordingfiletreatment",
            "recorder_tagulous_recorder_tags",
            "speaker_job",
            "speaker_jobvideo",
            "speaker_speaker",
            "thumbnail_kvstore",
            "video_advancednotes",
            "video_category",
            "video_category_video",
            "video_channel",
            "video_channel_add_channels_tab",
            "video_channel_allow_to_groups",
            "video_channel_owners",
            "video_channel_users",
            "video_comment",
            "video_discipline",
            "video_encode_transcript_encodingaudio",
            "video_encode_transcript_encodinglog",
            "video_encode_transcript_encodingstep",
            "video_encode_transcript_encodingvideo",
            "video_encode_transcript_playlistvideo",
            "video_encode_transcript_videorendition",
            "video_encode_transcript_videorendition_sites",
            "video_notecomments",
            "video_notes",
            "video_tagulous_video_tags",
            "video_theme",
            "video_type",
            "video_type_sites",
            "video_updateowner",
            "video_usermarkertime",
            "video_video",
            "video_videoaccesstoken",
            "video_videotodelete",
            "video_videotodelete_video",
            "video_videoversion",
            "video_video_additional_owners",
            "video_video_channel",
            "video_video_discipline",
            "video_video_restrict_access_to_groups",
            "video_video_sites",
            "video_video_tags",
            "video_video_theme",
            "video_viewcount",
            "video_vote",
            "webpush_group",
            "webpush_pushinformation",
            "webpush_subscriptioninfo",
            # Virtual table names for legacy tag migration compatibility.
            # check_table_existence() will only include these if tagging_taggeditem
            # and tagging_tag are present in the database (not the case in Pod v4).
            "video_tagging_tag_2_tagulous",
            "recorder_tagging_tag_2_tagulous",
        ]

    def check_table_existence(self, cursor, table_names: List[str]) -> List[str]:
        """Check which of the given table names actually exist in the database.

        Conditionally appends the two virtual tag table names only if the legacy
        django-tagging tables (tagging_taggeditem and tagging_tag) are present in
        the database. In Pod v4, these tables do not exist (Tagulous is used
        instead), so the virtual tag tables are simply not included and no error
        is raised.

        Args:
            cursor: An active database cursor.
            table_names: The full list of table names to check.

        Returns:
            A filtered list containing only the table names that exist in the
            database. The virtual tag table names are included only if the
            underlying legacy tagging tables are present.
        """
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]
        # Only include virtual tag table names if the legacy tagging system is present.
        # In Pod v4, tagging_taggeditem and tagging_tag do not exist (Tagulous is used
        # instead), so these virtual tables are excluded to avoid spurious errors.
        if "tagging_taggeditem" in tables and "tagging_tag" in tables:
            tables.append("video_tagging_tag_2_tagulous")
            tables.append("recorder_tagging_tag_2_tagulous")
        return [table for table in table_names if table in tables]

    def fetch_table_data(
        self, cursor, table: str
    ) -> Tuple[List[Tuple[Any, ...]], List[str]]:
        """Fetch all rows and column names from a database table.

        Args:
            cursor: An active database cursor.
            table: The name of the table to fetch data from.

        Returns:
            A tuple of (rows, columns) where rows is a list of row tuples
            and columns is a list of column name strings.
        """
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        cursor.execute(f"SHOW COLUMNS FROM {table}")
        columns = [row[0] for row in cursor.fetchall()]
        return rows, columns

    def fetch_tag_data(
        self, cursor, table: str, db_type: str
    ) -> Tuple[List[Tuple[Any, ...]], List[str]]:
        """Fetch tag data using legacy django-tagging SQL queries.

        This method is kept for forward-compatibility with installations that
        may still use the django-tagging system. It will only be called if
        check_table_existence() confirms that tagging_taggeditem and tagging_tag
        are present in the database.

        Supports both MySQL (GROUP_CONCAT) and PostgreSQL (STRING_AGG) aggregation.

        Args:
            cursor: An active database cursor.
            table: Virtual table name, either 'video_tagging_tag_2_tagulous' or
                'recorder_tagging_tag_2_tagulous'.
            db_type: Database engine type, e.g. 'mysql' or 'postgresql'.

        Returns:
            A tuple of (rows, columns) with the aggregated tag data.
        """
        if table == "video_tagging_tag_2_tagulous":
            query = (
                "SELECT tti.object_id as video_id, "
                + (
                    "GROUP_CONCAT(tt.name) as tag_name "
                    if db_type == "mysql"
                    else "STRING_AGG(tt.name, ', ') as tag_name "
                )
                + "FROM tagging_taggeditem tti, tagging_tag tt, django_content_type dct "
                "WHERE tti.tag_id = tt.id AND tti.content_type_id = dct.id AND dct.model = 'video' "
                "GROUP BY tti.object_id ORDER BY tti.object_id ASC"
            )
        elif table == "recorder_tagging_tag_2_tagulous":
            query = (
                "SELECT tti.object_id as recorder_id, "
                + (
                    "GROUP_CONCAT(tt.name) as tag_name "
                    if db_type == "mysql"
                    else "STRING_AGG(tt.name, ', ') as tag_name "
                )
                + "FROM tagging_taggeditem tti, tagging_tag tt, django_content_type dct "
                "WHERE tti.tag_id = tt.id AND tti.content_type_id = dct.id AND dct.model = 'recorder' "
                "GROUP BY tti.object_id ORDER BY tti.object_id ASC"
            )
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = (
            ["video_id", "tag_name"]
            if table == "video_tagging_tag_2_tagulous"
            else ["recorder_id", "tag_name"]
        )
        return rows, columns

    def convert_to_json(
        self, rows: List[Tuple[Any, ...]], columns: List[str], table: str = None
    ) -> List[Dict[str, Any]]:
        """Convert database rows to a list of JSON-serializable dictionaries.

        Handles the conversion of Python date, datetime and time objects to
        ISO-format strings. Also applies table-specific data fixes:

        - meeting table: If recurring_until is earlier than or equal to start_at
          (which can happen due to timezone offsets stored in the database),
          recurring_until is set to None. This avoids constraint violations
          (recurring_until_greater_than_start) when importing into the target
          instance.

        Args:
            rows: List of row tuples as returned by the database cursor.
            columns: List of column name strings matching the row tuple order.
            table: Optional table name used to apply table-specific fixes.

        Returns:
            A list of dicts, each representing one row with JSON-serializable values.
        """
        data = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Serialize Python date/time types to ISO-format strings
                if isinstance(value, datetime):
                    row_dict[column] = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, time):
                    row_dict[column] = value.strftime("%H:%M:%S")
                elif isinstance(value, date):
                    row_dict[column] = value.strftime("%Y-%m-%d")
                else:
                    row_dict[column] = value

            # FIX: For the meeting table, correct recurring_until values that are
            # less than or equal to start_at. This can happen due to timezone
            # differences between the application server and the database server.
            # Setting recurring_until to None is safe because the target DB constraint
            # allows NULL values for that field.
            if table == "meeting":
                start_at = row_dict.get("start_at")
                recurring_until = row_dict.get("recurring_until")
                if (
                    start_at
                    and recurring_until
                    and isinstance(start_at, str)
                    and isinstance(recurring_until, str)
                ):
                    if recurring_until[:10] <= start_at[:10]:
                        row_dict["recurring_until"] = None

            data.append(row_dict)
        return data

    def export_tables_to_json(
        self, table_names: List[str], output_directory: str, output_file: str
    ) -> None:
        """Export the specified tables to a JSON file.

        Iterates over all table names, fetches data from the database, converts
        each table's rows to JSON format, and writes the combined result to disk.
        Tables that raise an error (e.g. missing tables) are reported and skipped
        without interrupting the rest of the export.

        Args:
            table_names: List of table names to export.
            output_directory: Relative path (from BASE_DIR) to the output directory.
            output_file: Name of the output JSON file.
        """
        data = {}
        db_type = settings.DATABASES["default"]["ENGINE"].split(".")[-1]
        with connection.cursor() as cursor:
            existing_tables = self.check_table_existence(cursor, table_names)
            for table in existing_tables:
                try:
                    if table in [
                        "video_tagging_tag_2_tagulous",
                        "recorder_tagging_tag_2_tagulous",
                    ]:
                        # Use special aggregation query for legacy tag tables
                        rows, columns = self.fetch_tag_data(cursor, table, db_type)
                    else:
                        # Standard SELECT * for all other tables
                        rows, columns = self.fetch_table_data(cursor, table)
                    data[table] = self.convert_to_json(rows, columns, table=table)
                    self.stdout.write(
                        self.style.SUCCESS(f" - Table {table} has been processed.")
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f" - Table {table} could not be processed. Error: {e}"
                        )
                    )

        # Write all collected data to the JSON output file
        json_file = os.path.join(BASE_DIR, f"{output_directory}{output_file}")
        with open(json_file, "w") as f:
            json.dump(data, f, indent=4)
            f.write("\n")

    def process(self, options: Dict[str, Any]) -> None:
        """Main process to orchestrate the full database export.

        Defines the output location, triggers directory creation, retrieves the
        table list, runs the export, and reports the final result.

        Args:
            options: The options dict passed by Django's management command framework.
        """
        # Output directory and file name for the exported JSON
        output_directory = "../../data_from_v4_to_v5/"
        output_json_file = "v4_exported_to_v5.json"

        # Create output directory if it does not already exist
        self.create_directory(output_directory)

        # Retrieve the full list of tables to export
        tables_to_export = self.get_table_names()

        # Run the export
        self.export_tables_to_json(tables_to_export, output_directory, output_json_file)

        # Report the final result
        json_file = os.path.join(BASE_DIR, f"{output_directory}{output_json_file}")
        if os.path.exists(json_file):
            self.stdout.write(
                self.style.SUCCESS(f" - The JSON file {json_file} was created.")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f" - The JSON file {json_file} was not created.")
            )
