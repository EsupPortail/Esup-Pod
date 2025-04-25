"""
Export data from Pod v3.8.x to a JSON file for Pod v4.0.x.

This script is designed to export data from a Pod v3.8.x database to a JSON file, which can then be used to migrate the data to a Pod v4.0.x database.
The script handles both MariaDB/MySQL and PostgreSQL databases, adapting SQL queries as needed.

Key Features:
- Exports specified tables from the Pod v3 database to a JSON file.
- Handles both MariaDB/MySQL and PostgreSQL databases.
- Creates a directory to store the exported data if it does not already exist.
- Converts datetime, time, and date objects to JSON-serializable formats.
- Provides detailed success and error messages using Django's management command framework.

Important notes:
- The JSON file must be found at BASE_DIR/data_from_v3_to_v4/v3_exported_tables.json
Example: /usr/local/django_projects/data_from_v3_to_v4/v3_exported_tables.json
 - This script can be rerun as many times as required, the JSON file is regenerated each time.

Usage:
Run the script using Django's management command:
    python manage.py export_data_from_v3_to_v4

Dependencies:
- Django
- Settings configured with the database connection details.

Functions:
- create_directory: Creates the directory to store the exported data.
- get_table_names: Returns the list of tables to export.
- check_table_existence: Checks if the specified tables exist in the database (with specific code for tags management).
- fetch_table_data: Fetches data from a specific table.
- fetch_tag_data: Fetches tag data with special handling for tags.
- convert_to_json: Converts rows of data to JSON format.
- export_tables_to_json: Exports the specified tables to a JSON file.
- process: Main process to handle the data export.
"""

import json
import os
from datetime import date, datetime, time
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from typing import List, Tuple, Dict, Any

# Base directory
BASE_DIR = getattr(settings, "BASE_DIR", "/home/pod/django_projects/podv3/pod")
# Pod version
VERSION = getattr(settings, "VERSION", "undefined")


class Command(BaseCommand):
    """Main command class."""

    help = "Export data from Pod v3.8.x to Pod v4.0.x"

    def handle(self, *args: Any, **options: Any) -> None:
        """Handle the command call."""

        self.stdout.write(
            self.style.SUCCESS("***Start export Pod3 database tables to a JSON file***")
        )

        # Manage Pod version
        if VERSION[:3] == "3.8":
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
                    f"- Pod version: {VERSION}. "
                    "This script can only be used for Pod version 3.8.x. "
                    "Please update Pod. The process stops here!"
                )
            )
            # Stop process
            return

        # Main function
        self.process(options)

    def create_directory(self, output_directory: str) -> None:
        """Create directory to store all the data."""
        self.stdout.write(self.style.SUCCESS(" - Create directory data if necessary"))
        os.makedirs(os.path.join(BASE_DIR, output_directory), exist_ok=True)

    def get_table_names(self) -> List[str]:
        """Return the list of tables to export."""
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
            "chunked_upload_chunkedupload",
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
            "recorder_recorder_theme",
            "recorder_recording",
            "recorder_recordingfile",
            "recorder_recordingfiletreatment",
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
            "video_video_theme",
            "video_viewcount",
            "video_vote",
            "webpush_group",
            "webpush_pushinformation",
            "webpush_subscriptioninfo",
            # Specific for tags management
            "video_tagging_tag_2_tagulous",
            "recorder_tagging_tag_2_tagulous",
        ]

    def check_table_existence(self, cursor, table_names: List[str]) -> List[str]:
        """Check if the tables exist in the database."""
        cursor.execute("SHOW TABLES;")
        tables = [row[0] for row in cursor.fetchall()]
        # Specific for tags management
        tables.append("video_tagging_tag_2_tagulous")
        tables.append("recorder_tagging_tag_2_tagulous")
        return [table for table in table_names if table in tables]

    def fetch_table_data(
        self, cursor, table: str
    ) -> Tuple[List[Tuple[Any, ...]], List[str]]:
        """Fetch data from a specific table."""
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        cursor.execute(f"SHOW COLUMNS FROM {table}")
        columns = [row[0] for row in cursor.fetchall()]
        return rows, columns

    def fetch_tag_data(
        self, cursor, table: str, db_type: str
    ) -> Tuple[List[Tuple[Any, ...]], List[str]]:
        """Fetch tag data for specific management."""
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
        self, rows: List[Tuple[Any, ...]], columns: List[str]
    ) -> List[Dict[str, Any]]:
        """Convert rows to JSON format."""
        data = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(columns):
                value = row[i]
                # Manage date/time format
                if isinstance(value, datetime):
                    row_dict[column] = value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, time):
                    row_dict[column] = value.strftime("%H:%M:%S")
                elif isinstance(value, date):
                    row_dict[column] = value.strftime("%Y-%m-%d")
                else:
                    row_dict[column] = value
            data.append(row_dict)
        return data

    def export_tables_to_json(
        self, table_names: List[str], output_directory: str, output_file: str
    ) -> None:
        """Export the specified tables to a JSON file."""
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
                        # Management for tags
                        rows, columns = self.fetch_tag_data(cursor, table, db_type)
                    else:
                        # Management for others data
                        rows, columns = self.fetch_table_data(cursor, table)
                    data[table] = self.convert_to_json(rows, columns)
                    self.stdout.write(
                        self.style.SUCCESS(f" - Table {table} has been processed.")
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f" - Table {table} could not be processed. Error: {e}"
                        )
                    )

        # Write the JSON file
        json_file = os.path.join(BASE_DIR, f"{output_directory}{output_file}")
        with open(json_file, "w") as f:
            json.dump(data, f, indent=4)
            f.write("\n")

    def process(self, options: Dict[str, Any]) -> None:
        """Main process to export data."""

        # Define directory and JSON file
        output_directory = "../../data_from_v3_to_v4/"
        output_json_file = "v3_exported_tables.json"

        # Create data directory, if necessary
        self.create_directory(output_directory)

        # List of tables to export
        tables_to_export = self.get_table_names()

        # Export tables to JSON file
        self.export_tables_to_json(tables_to_export, output_directory, output_json_file)

        # Path of the JSON file
        json_file = os.path.join(BASE_DIR, f"{output_directory}{output_json_file}")
        if os.path.exists(json_file):
            self.stdout.write(
                self.style.SUCCESS(f" - The JSON file {json_file} was created.")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f" - The JSON file {json_file} was not created.")
            )
