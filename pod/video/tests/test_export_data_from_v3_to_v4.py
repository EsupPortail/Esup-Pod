"""Tests for the Pod v3 to v4 data export command."""

import json
import tempfile
from datetime import date, datetime
from unittest.mock import patch

from django.test import SimpleTestCase

from pod.video.management.commands import export_data_from_v3_to_v4

Command = export_data_from_v3_to_v4.Command


class ExportDataFromV3ToV4Tests(SimpleTestCase):
    """Verify table-specific data normalization during export."""

    def setUp(self) -> None:
        """Create the command under test."""
        self.command = Command()
        self.columns = ["id", "start_at", "recurring_until", "nb_occurrences"]

    def test_invalid_meeting_recurring_until_is_moved_to_start_date(self) -> None:
        """An end date before the meeting start date must satisfy Pod v4 checks."""
        rows = [(1, datetime(2025, 12, 26, 0, 30), date(2025, 12, 25), 2)]

        result = self.command.convert_to_json(rows, self.columns, table="meeting")

        self.assertEqual(result[0]["start_at"], "2025-12-26 00:30:00")
        self.assertEqual(result[0]["recurring_until"], "2025-12-26")
        self.assertEqual(result[0]["nb_occurrences"], 2)

    def test_valid_meeting_recurring_until_is_unchanged(self) -> None:
        """A valid recurrence end date must be preserved."""
        rows = [(1, datetime(2025, 12, 26, 10, 0), date(2025, 12, 27), 2)]

        result = self.command.convert_to_json(rows, self.columns, table="meeting")

        self.assertEqual(result[0]["recurring_until"], "2025-12-27")

    def test_same_day_meeting_recurring_until_is_unchanged(self) -> None:
        """Equality is accepted by recurring_until_greater_than_start."""
        rows = [(1, datetime(2025, 12, 26, 10, 0), date(2025, 12, 26), 1)]

        result = self.command.convert_to_json(rows, self.columns, table="meeting")

        self.assertEqual(result[0]["recurring_until"], "2025-12-26")

    def test_other_tables_are_not_normalized_as_meetings(self) -> None:
        """Only meeting rows receive recurrence normalization."""
        rows = [(1, datetime(2025, 12, 26, 0, 30), date(2025, 12, 25), 2)]

        result = self.command.convert_to_json(rows, self.columns, table="other")

        self.assertEqual(result[0]["recurring_until"], "2025-12-25")

    def test_duplicate_video_to_delete_rows_are_merged(self) -> None:
        """Duplicate dates must share one parent while preserving every video."""
        data = {
            "video_videotodelete": [
                {"id": 12, "date_deletion": "2025-12-25"},
                {"id": 10, "date_deletion": "2025-12-25"},
                {"id": 11, "date_deletion": "2025-12-26"},
            ],
            "video_videotodelete_video": [
                {"id": 100, "videotodelete_id": 12, "video_id": 1},
                {"id": 101, "videotodelete_id": 10, "video_id": 2},
                {"id": 102, "videotodelete_id": 12, "video_id": 2},
                {"id": 103, "videotodelete_id": 11, "video_id": 3},
            ],
        }

        self.command.normalize_video_to_delete_data(data)

        self.assertEqual(
            data["video_videotodelete"],
            [
                {"id": 10, "date_deletion": "2025-12-25"},
                {"id": 11, "date_deletion": "2025-12-26"},
            ],
        )
        self.assertEqual(
            data["video_videotodelete_video"],
            [
                {"id": 100, "videotodelete_id": 10, "video_id": 1},
                {"id": 101, "videotodelete_id": 10, "video_id": 2},
                {"id": 103, "videotodelete_id": 11, "video_id": 3},
            ],
        )

    def test_video_to_delete_rows_without_duplicates_are_preserved(self) -> None:
        """Already valid deletion data must remain unchanged."""
        data = {
            "video_videotodelete": [
                {"id": 10, "date_deletion": "2025-12-25"},
                {"id": 11, "date_deletion": "2025-12-26"},
            ],
            "video_videotodelete_video": [
                {"id": 100, "videotodelete_id": 10, "video_id": 1},
                {"id": 101, "videotodelete_id": 11, "video_id": 2},
            ],
        }
        expected = {
            table: [row.copy() for row in rows]
            for table, rows in data.items()
        }

        self.command.normalize_video_to_delete_data(data)

        self.assertEqual(data, expected)

    def test_video_to_delete_normalization_accepts_missing_relation_table(self) -> None:
        """A partial export can still merge duplicate parent rows safely."""
        data = {
            "video_videotodelete": [
                {"id": 2, "date_deletion": "2025-12-25"},
                {"id": 1, "date_deletion": "2025-12-25"},
            ]
        }

        self.command.normalize_video_to_delete_data(data)

        self.assertEqual(
            data["video_videotodelete"],
            [{"id": 1, "date_deletion": "2025-12-25"}],
        )
        self.assertNotIn("video_videotodelete_video", data)

    def test_export_writes_normalized_video_to_delete_data(self) -> None:
        """The complete export flow must normalize data before writing JSON."""
        tables = ["video_videotodelete", "video_videotodelete_video"]
        table_data = {
            "video_videotodelete": (
                [(2, date(2025, 12, 25)), (1, date(2025, 12, 25))],
                ["id", "date_deletion"],
            ),
            "video_videotodelete_video": (
                [(10, 2, 20), (11, 1, 21)],
                ["id", "videotodelete_id", "video_id"],
            ),
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            with (
                patch.object(export_data_from_v3_to_v4, "BASE_DIR", temporary_directory),
                patch.object(export_data_from_v3_to_v4, "connection"),
                patch.object(
                    self.command, "check_table_existence", return_value=tables
                ),
                patch.object(
                    self.command,
                    "fetch_table_data",
                    side_effect=lambda cursor, table: table_data[table],
                ),
            ):
                self.command.export_tables_to_json(tables, "", "export.json")

            with open(
                f"{temporary_directory}/export.json", "r", encoding="utf-8"
            ) as json_file:
                exported_data = json.load(json_file)

        self.assertEqual(
            exported_data["video_videotodelete"],
            [{"id": 1, "date_deletion": "2025-12-25"}],
        )
        self.assertEqual(
            exported_data["video_videotodelete_video"],
            [
                {"id": 10, "videotodelete_id": 1, "video_id": 20},
                {"id": 11, "videotodelete_id": 1, "video_id": 21},
            ],
        )
