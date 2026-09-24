"""Exercise check_user_hashes against database records and temporary media files."""

import hashlib
import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, connection
from django.db.models.query import QuerySet
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from pod.authentication.models import Owner
from pod.podfile.models import CustomFileModel, CustomImageModel, UserFolder
from pod.recorder.models import RecordingFileTreatment
from pod.video.management.commands.check_database_problems import Command as LegacyCommand
from pod.video.management.commands.check_user_hashes import UserHashRepair
from pod.video.models import Type, Video
from pod.video_encode_transcript.models import (
    EncodingAudio,
    EncodingLog,
    EncodingVideo,
    PlaylistVideo,
    Task,
    VideoRendition,
)


class UserHashRepairTests(TestCase):
    """Keep stored hashes, file bytes and all references consistent during a repair."""

    def setUp(self) -> None:
        """Create a profile, media records and isolated files under a wrong hash."""
        temporary = TemporaryDirectory(prefix="pod-hash-repair-")
        self.addCleanup(temporary.cleanup)
        self.media = Path(temporary.name)
        configuration = override_settings(
            MEDIA_ROOT=temporary.name,
            FILES_DIR="documents",
            VIDEOS_DIR="recordings",
        )
        configuration.enable()
        self.addCleanup(configuration.disable)
        indexing = patch("pod.video_search.models.ES_URL", None)
        indexing.start()
        self.addCleanup(indexing.stop)
        self.user = User.objects.create(username="hash-repair-user")
        self.expected = self.digest(settings.SECRET_KEY, self.user.username)
        self.previous = self.digest("accidentally-replaced-key", self.user.username)
        Owner.objects.filter(user=self.user).update(hashkey=self.previous)
        self.references = []
        self.reference_contents = {}
        self.video = Video.objects.create(
            owner=self.user,
            title="Hash repair",
            type=Type.objects.create(title="Hash repair"),
            video=self.file_name("source.mp4"),
            overview=self.file_name("0001/overview.png"),
        )
        self.add_file(self.video, "video")
        self.add_file(self.video, "overview")
        rendition = VideoRendition.objects.create(resolution="640x360")
        for model, filename, kwargs in [
            (EncodingVideo, "0001/video.mp4", {"rendition": rendition}),
            (EncodingAudio, "0001/audio.mp3", {}),
            (PlaylistVideo, "0001/playlist.m3u8", {}),
            (EncodingLog, "0001/info_video.json", {}),
        ]:
            field = "logfile" if model is EncodingLog else "source_file"
            obj = model.objects.create(
                video=self.video, **{field: self.file_name(filename)}, **kwargs
            )
            self.add_file(obj, field)
        folder, _ = UserFolder.objects.get_or_create(owner=self.user, name="home")
        for model, filename in [
            (CustomFileModel, "note.txt"),
            (CustomImageModel, "pic.png"),
        ]:
            obj = model.objects.create(
                created_by=self.user,
                folder=folder,
                file=self.file_name(filename, root="documents"),
            )
            self.add_file(obj, "file")
        absolute = str(self.media / self.file_name("pending.mp4"))
        pending = RecordingFileTreatment.objects.create(file=absolute)
        self.add_file(pending, "file")

    @staticmethod
    def digest(key: str, username: str) -> str:
        """Return the profile hash associated with a key and username."""
        return hashlib.sha256((key + username).encode("utf-8")).hexdigest()

    def file_name(self, filename: str, root: str = "recordings") -> str:
        """Build a path using the currently incorrect profile hash."""
        return f"{root}/{self.previous}/{filename}"

    def add_file(self, obj: object, field: str) -> None:
        """Remember a database reference and materialize its contents on disk."""
        name = str(getattr(obj, field))
        self.references.append((obj, field, name))
        self.write_file(name, name.encode("utf-8"))

    def write_file(self, name: str, contents: bytes) -> Path:
        """Create a temporary file without invoking Django storage renaming."""
        path = self.media / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        return path

    def snapshot(self) -> dict:
        """Capture file names and bytes to detect any filesystem changes."""
        return {
            str(path.relative_to(self.media)): (
                path.read_bytes() if path.is_file() else None
            )
            for path in self.media.rglob("*")
        }

    def run_repair(self, **options) -> str:
        """Run the public management command and capture its report."""
        stdout = options.pop("stdout", StringIO())
        call_command(
            "check_user_hashes",
            stdout=stdout,
            stderr=StringIO(),
            **options,
        )
        return stdout.getvalue()

    def create_other_profile(self, username: str = "second-hash-profile") -> tuple:
        """Create another independent profile with a document that must also move."""
        user = User.objects.create(username=username)
        previous = self.digest("wrong", username)
        expected = self.digest(settings.SECRET_KEY, username)
        Owner.objects.filter(user=user).update(hashkey=previous)
        folder, _ = UserFolder.objects.get_or_create(owner=user, name="home")
        document = CustomFileModel.objects.create(
            created_by=user, folder=folder, file=f"documents/{previous}/note.txt"
        )
        self.write_file(document.file.name, b"other profile")
        return user, previous, expected, document

    def assert_other_profile(self, fixture: tuple, repaired: bool) -> None:
        """Check the other profile's hash, database path and complete media contents."""
        user, previous, expected, document = fixture
        current_hash = expected if repaired else previous
        other_hash = previous if repaired else expected
        self.assertEqual(Owner.objects.get(user=user).hashkey, current_hash)
        document.refresh_from_db()
        self.assertEqual(document.file.name, f"documents/{current_hash}/note.txt")
        self.assertEqual((self.media / document.file.name).read_bytes(), b"other profile")
        self.assertFalse((self.media / "documents" / other_hash).exists())

    def assert_original_database(self) -> None:
        """Check that neither the hash nor any file reference was changed."""
        self.assertEqual(Owner.objects.get(user=self.user).hashkey, self.previous)
        for obj, field, name in self.references:
            obj.refresh_from_db()
            self.assertEqual(str(getattr(obj, field)), name)

    def assert_repaired(self) -> None:
        """Check every field and file, including original videos and absolute paths."""
        self.assertEqual(Owner.objects.get(user=self.user).hashkey, self.expected)
        for obj, field, name in self.references:
            obj.refresh_from_db()
            expected_name = name.replace(self.previous, self.expected, 1)
            self.assertEqual(str(getattr(obj, field)), expected_name)
            self.assertEqual(
                (self.media / expected_name).read_bytes(),
                self.reference_contents.get(name, name.encode("utf-8")),
            )

    def create_report_conflict(
        self, encoding_at_destination: bool = False
    ) -> SimpleNamespace:
        """Reproduce a legacy video encoding beside a Runner transcription's JSON/VTT."""
        old_name = self.file_name("0001/info_video.json")
        source = self.media / old_name
        destination = self.media / old_name.replace(self.previous, self.expected)
        encoding_bytes = json.dumps(
            {
                "id": self.video.pk,
                "list_video_track": {"0": {"width": 640, "height": 360}},
                "list_audio_track": {"1": {"codec_name": "aac"}},
            }
        ).encode()
        self.reference_contents[old_name] = encoding_bytes
        self.write_file(old_name, encoding_bytes)
        if encoding_at_destination:
            (self.media / "recordings" / self.previous).rename(
                self.media / "recordings" / self.expected
            )
            for obj, field, name in self.references:
                if "recordings/" in name:
                    type(obj).objects.filter(pk=obj.pk).update(
                        **{field: name.replace(self.previous, self.expected)}
                    )
            self.video.refresh_from_db()
        retained = destination if encoding_at_destination else source
        transcription = source if encoding_at_destination else destination
        transcript_bytes = json.dumps(
            {"has_stream_video": False, "has_stream_audio": True, "duration": 120}
        ).encode()
        self.write_file(str(transcription), transcript_bytes)
        task = Task.objects.create(
            task_id="d9c5e1ef-a44d-4df8-ab4a-af24222d888f",
            type="transcription",
            status="completed",
            video=self.video,
        )
        metadata = transcription.parent / "task_metadata.json"
        self.write_file(
            str(metadata),
            json.dumps(
                {
                    "task_id": task.task_id,
                    "task_type": "transcription",
                    "timestamp": "2026-09-01T12:00:00",
                    "results": {},
                }
            ).encode(),
        )
        subtitle = transcription.parent / "audio_192k.vtt"
        self.write_file(str(subtitle), b"WEBVTT\n\n00:00.000 --> 00:01.000\nSubtitle\n")
        archive = destination.with_name(
            f"info_video.transcription-{hashlib.sha256(transcript_bytes).hexdigest()}.json"
        )
        return SimpleNamespace(
            source=source,
            destination=destination,
            retained=retained,
            transcription=transcription,
            metadata=metadata,
            subtitle=subtitle,
            archive=archive,
            task=task,
            encoding_bytes=encoding_bytes,
            transcript_bytes=transcript_bytes,
        )

    def successful_transcription_metadata(self, fixture: SimpleNamespace) -> dict:
        """Use the Runner payload from a transcription performed after key rotation."""
        runner_dir = f"/data/partage/runners/runner4/{fixture.task.task_id}"
        metadata = {
            "task_id": fixture.task.task_id,
            "task_type": "transcription",
            "timestamp": "2026-07-23T12:39:26.239175",
            "results": {
                "success": True,
                "task_type": "transcription",
                "input_path": f"{runner_dir}/audio_192k.mp3",
                "output_dir": f"{runner_dir}/output",
                "script_output": {
                    "success": True,
                    "returncode": 0,
                    "stdout": f"VTT written to: {runner_dir}/output/audio_192k.vtt\n",
                    "stderr": "",
                },
            },
        }
        fixture.metadata.write_text(json.dumps(metadata), encoding="utf-8")
        return metadata

    def create_metadata_conflict(self) -> SimpleNamespace:
        """Create two historical metadata files without any media/report conflict."""
        source = self.media / self.file_name("0001/task_metadata.json")
        destination = self.media / str(source.relative_to(self.media)).replace(
            self.previous, self.expected
        )
        source_bytes = b'{"task_id": "encoding-task", "task_type": "encoding"}'
        destination_bytes = b'{"task_id": "later-task", "task_type": "transcription"}'
        self.write_file(str(source), source_bytes)
        self.write_file(str(destination), destination_bytes)
        return SimpleNamespace(
            source=source,
            destination=destination,
            source_bytes=source_bytes,
            destination_bytes=destination_bytes,
            archive=destination.with_name(
                f"task_metadata.{hashlib.sha256(destination_bytes).hexdigest()}.json"
            ),
        )

    def planned_metadata_repair(self) -> tuple:
        """Build a metadata-only plan to exercise revalidation before applying."""
        repair = UserHashRepair(StringIO())
        repair.select_profiles([self.user.username])
        repair.configure_paths()
        plan = repair.plans[0]
        repair.plan_profile(plan)
        self.assertFalse(plan.errors)
        self.assertEqual(len(plan.metadata_archives), 1)
        return repair, plan

    def assert_report_conflict_repaired(self, fixture: SimpleNamespace) -> str:
        """Both JSONs and transcription artifacts survive, with only the encoding active."""
        metadata_bytes = fixture.metadata.read_bytes()
        subtitle_bytes = fixture.subtitle.read_bytes()
        output = self.run_repair()
        self.assert_repaired()
        self.assertEqual(fixture.destination.read_bytes(), fixture.encoding_bytes)
        self.assertEqual(fixture.archive.read_bytes(), fixture.transcript_bytes)
        self.assertEqual(
            (fixture.destination.parent / fixture.metadata.name).read_bytes(),
            metadata_bytes,
        )
        self.assertEqual(
            (fixture.destination.parent / fixture.subtitle.name).read_bytes(),
            subtitle_bytes,
        )
        self.assertIn("JSON archives        : 1", output)
        self.assertFalse((self.media / "recordings" / self.previous).exists())
        after = self.snapshot()
        self.run_repair()
        self.assertEqual(self.snapshot(), after)
        return output

    def planned_report_repair(self) -> tuple:
        """Plan one profile for a later mutation between validation and application."""
        repair = UserHashRepair(StringIO())
        repair.select_profiles([self.user.username])
        repair.configure_paths()
        plan = repair.plans[0]
        repair.plan_profile(plan)
        self.assertFalse(plan.errors)
        self.assertEqual(len(plan.report_archives), 1)
        return repair, plan

    def test_report_archive_dry_run_is_read_only(self) -> None:
        """The dry run explains the JSON choice and archive without any writes."""
        fixture = self.create_report_conflict()
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            output = self.run_repair(dry=True)
        self.assertTrue(all(q["sql"].lstrip().startswith("SELECT") for q in queries))
        self.assertIn("Keep encoding report: 0001/info_video.json (from Stored)", output)
        self.assertIn("Archive transcription report (planned", output)
        self.assertIn(fixture.archive.name, output)
        self.assertIn("JSON archives        : 1", output)
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_transcription_report_at_destination_is_archived_before_replacement(
        self,
    ) -> None:
        """Move the encoding JSON into place only after preserving the transcription JSON."""
        self.assert_report_conflict_repaired(self.create_report_conflict())

    def test_transcription_report_at_source_is_archived_without_replacing_destination(
        self,
    ) -> None:
        """Preserve an encoding already under the expected hash and merge the subtitles."""
        self.assert_report_conflict_repaired(
            self.create_report_conflict(encoding_at_destination=True)
        )

    def test_metadata_archive_keeps_encoding_metadata_and_preserves_both_files(self):
        """Keep the registered encoding's metadata even if the Task has been purged."""
        fixture = self.create_metadata_conflict()
        output = self.run_repair()
        self.assert_repaired()
        self.assertEqual(fixture.destination.read_bytes(), fixture.source_bytes)
        self.assertEqual(fixture.archive.read_bytes(), fixture.destination_bytes)
        self.assertIn("Keep task metadata: 0001/task_metadata.json (from Stored)", output)
        self.assertIn("JSON archives        : 1", output)
        self.assertFalse(fixture.source.exists())
        after = self.snapshot()
        self.run_repair()
        self.assertEqual(self.snapshot(), after)

    def test_metadata_archive_keeps_destination_when_encoding_references_are_split(self):
        """Ambiguous encoding locations only affect the metadata's canonical name."""
        fixture = self.create_metadata_conflict()
        audio = EncodingAudio.objects.get(video=self.video)
        old_name = audio.source_file.name
        new_name = old_name.replace(self.previous, self.expected)
        (self.media / old_name).rename(self.media / new_name)
        EncodingAudio.objects.filter(pk=audio.pk).update(source_file=new_name)
        output = self.run_repair()
        self.assert_repaired()
        archived = fixture.destination.with_name(
            f"task_metadata.{hashlib.sha256(fixture.source_bytes).hexdigest()}.json"
        )
        self.assertEqual(fixture.destination.read_bytes(), fixture.destination_bytes)
        self.assertEqual(archived.read_bytes(), fixture.source_bytes)
        self.assertIn(
            "Keep task metadata: 0001/task_metadata.json (from Expected)", output
        )

    def test_metadata_archive_dry_run_only_reads(self):
        """The simulation lists archival moves without changing files or references."""
        fixture = self.create_metadata_conflict()
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            output = self.run_repair(dry=True)
        self.assertTrue(all(q["sql"].lstrip().startswith("SELECT") for q in queries))
        self.assertIn("Archive task metadata (planned)", output)
        self.assertIn(fixture.archive.name, output)
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_metadata_archive_does_not_resolve_media_conflicts(self):
        """Different MP4s still block the whole profile, including metadata moves."""
        self.create_metadata_conflict()
        self.write_file(
            self.file_name("0001/video.mp4").replace(self.previous, self.expected),
            b"a different encoding",
        )
        before = self.snapshot()
        output = StringIO()
        with self.assertRaisesMessage(CommandError, "conflict(s)"):
            self.run_repair(stdout=output)
        self.assertIn("Different files or entry types", output.getvalue())
        self.assertIn("Archive task metadata (planned)", output.getvalue())
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_metadata_archive_refuses_invalid_json(self):
        """Neither metadata file may be renamed on the strength of malformed JSON."""
        fixture = self.create_metadata_conflict()
        for path in (fixture.source, fixture.destination):
            original = path.read_bytes()
            for contents in (b"not JSON", b"[]", b"{}"):
                with self.subTest(path=path, contents=contents):
                    path.write_bytes(contents)
                    before = self.snapshot()
                    with self.assertRaisesMessage(CommandError, "conflict(s)"):
                        self.run_repair()
                    self.assert_original_database()
                    self.assertEqual(self.snapshot(), before)
            path.write_bytes(original)

    def test_metadata_archive_never_overwrites_existing_archives(self):
        """An archive on either side remains intact and prevents ambiguous moves."""
        fixture = self.create_metadata_conflict()
        for path in (fixture.archive, fixture.source.with_name(fixture.archive.name)):
            with self.subTest(path=path):
                path.write_bytes(b"existing archive")
                before = self.snapshot()
                with self.assertRaisesMessage(CommandError, "conflict(s)"):
                    self.run_repair()
                self.assert_original_database()
                self.assertEqual(self.snapshot(), before)
                path.unlink()

    def test_metadata_archive_never_renames_a_referenced_file(self):
        """A file-field reference must not silently start pointing at another JSON."""
        fixture = self.create_metadata_conflict()
        RecordingFileTreatment.objects.create(file=str(fixture.destination))
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "conflict(s)"):
            self.run_repair()
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_metadata_archive_rechecks_both_json_files_before_moving(self):
        """Even valid JSON changes invalidate an already prepared archival plan."""
        fixture = self.create_metadata_conflict()
        repair, plan = self.planned_metadata_repair()
        for path in (fixture.source, fixture.destination):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                before = self.snapshot()
                with self.assertRaisesMessage(CommandError, "evidence changed"):
                    repair.apply(plan)
                self.assert_original_database()
                self.assertEqual(self.snapshot(), before)
                path.write_bytes(original)

    def test_metadata_archive_rechecks_references_before_moving(self):
        """A new consumer of the metadata to archive must block the prepared plan."""
        fixture = self.create_metadata_conflict()
        repair, plan = self.planned_metadata_repair()
        RecordingFileTreatment.objects.create(file=str(fixture.destination))
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "Report to archive is referenced"):
            repair.apply(plan)
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def assert_joint_json_archives(self, encoding_at_destination: bool) -> None:
        """Resolve both JSON collisions, retaining the encoding's report and metadata."""
        fixture = self.create_report_conflict(encoding_at_destination)
        encoding_metadata = b'{"task_id": "encoding-task", "task_type": "encoding"}'
        fixture.retained.with_name("task_metadata.json").write_bytes(encoding_metadata)
        transcription_metadata = fixture.metadata.read_bytes()
        metadata_archive = fixture.destination.with_name(
            f"task_metadata.{hashlib.sha256(transcription_metadata).hexdigest()}.json"
        )
        output = self.run_repair()
        self.assert_repaired()
        self.assertEqual(fixture.destination.read_bytes(), fixture.encoding_bytes)
        self.assertEqual(fixture.archive.read_bytes(), fixture.transcript_bytes)
        self.assertEqual(
            fixture.destination.with_name("task_metadata.json").read_bytes(),
            encoding_metadata,
        )
        self.assertEqual(metadata_archive.read_bytes(), transcription_metadata)
        self.assertIn("JSON archives        : 2", output)

    def test_metadata_archive_with_encoding_report_at_source(self):
        """A metadata collision does not interfere with proof of the transcription."""
        self.assert_joint_json_archives(encoding_at_destination=False)

    def test_metadata_archive_with_encoding_report_at_destination(self):
        """Both transcription JSON files are archived beside the retained encoding."""
        self.assert_joint_json_archives(encoding_at_destination=True)

    def test_missing_task_uses_metadata_to_archive_report_at_destination(self) -> None:
        """A purged Task does not prevent preserving the encoding and transcription."""
        fixture = self.create_report_conflict()
        self.successful_transcription_metadata(fixture)
        fixture.task.delete()
        output = self.assert_report_conflict_repaired(fixture)
        self.assertIn("Task absent from database", output)
        self.assertIn(f"metadata task_id={fixture.task.task_id!r}", output)
        self.assertFalse(Task.objects.filter(task_id=fixture.task.task_id).exists())

    def test_missing_task_uses_metadata_to_archive_report_at_source(self) -> None:
        """The fallback also merges subtitles into an encoding at the expected hash."""
        fixture = self.create_report_conflict(encoding_at_destination=True)
        self.successful_transcription_metadata(fixture)
        fixture.task.delete()
        # A UTF-8 BOM and CRLF are accepted in real-world subtitle files.
        fixture.subtitle.write_bytes(b"\xef\xbb\xbfWEBVTT\r\n\r\n")
        self.assert_report_conflict_repaired(fixture)

    def test_missing_task_metadata_dry_run_is_read_only(self) -> None:
        """Explain the fallback without moving files or recreating the absent Task."""
        fixture = self.create_report_conflict()
        self.successful_transcription_metadata(fixture)
        fixture.task.delete()
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            output = self.run_repair(dry=True)
        self.assertTrue(all(q["sql"].lstrip().startswith("SELECT") for q in queries))
        self.assertIn("Task absent from database", output)
        self.assertIn("Archive transcription report (planned, metadata task_id=", output)
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(Task.objects.filter(task_id=fixture.task.task_id).exists())

    def test_missing_task_requires_explicit_successful_metadata(self) -> None:
        """Malformed, incomplete or failed results never authorize a fallback move."""
        fixture = self.create_report_conflict()
        self.successful_transcription_metadata(fixture)
        fixture.task.delete()
        original = fixture.metadata.read_text(encoding="utf-8")
        cases = [
            ("results", None),
            ("results", []),
            ("results", {}),
            ("results.task_type", "encoding"),
            ("results.success", False),
            ("results.success", "true"),
            ("results.success", 1),
            ("results.script_output", None),
            ("results.script_output", []),
            ("results.script_output", {}),
            ("results.script_output", {"success": True}),
            ("results.script_output.success", False),
            ("results.script_output.success", "true"),
            ("results.script_output.success", 1),
            ("results.script_output.returncode", 1),
            ("results.script_output.returncode", "0"),
            ("results.script_output.returncode", False),
            ("results.script_output.returncode", 0.0),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                metadata = json.loads(original)
                data = metadata
                parts = field.split(".")
                for part in parts[:-1]:
                    data = data[part]
                data[parts[-1]] = value
                fixture.metadata.write_text(json.dumps(metadata), encoding="utf-8")
                before = self.snapshot()
                output = StringIO()
                with self.assertRaisesMessage(CommandError, "conflict(s)"):
                    self.run_repair(stdout=output)
                self.assertIn("fallback requires", output.getvalue())
                self.assert_original_database()
                self.assertEqual(self.snapshot(), before)

    def test_missing_task_requires_readable_vtt_artifacts(self) -> None:
        """Metadata alone cannot justify repair without a UTF-8 VTT artifact."""
        fixture = self.create_report_conflict()
        self.successful_transcription_metadata(fixture)
        fixture.task.delete()
        for contents in (None, b"", b"not subtitles", b"WEBVTTfake\n", b"WEBVTT\n\xff"):
            with self.subTest(contents=contents):
                if contents is None:
                    fixture.subtitle.unlink()
                else:
                    fixture.subtitle.write_bytes(contents)
                before = self.snapshot()
                with self.assertRaisesMessage(CommandError, "conflict(s)"):
                    self.run_repair()
                self.assert_original_database()
                self.assertEqual(self.snapshot(), before)

    def test_missing_task_rechecks_metadata_and_subtitles_before_moving(self) -> None:
        """A successful plan becomes stale if either fallback artifact changes."""
        fixture = self.create_report_conflict()
        self.successful_transcription_metadata(fixture)
        fixture.task.delete()
        repair, plan = self.planned_report_repair()
        for path in (fixture.metadata, fixture.subtitle):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                before = self.snapshot()
                with self.assertRaisesMessage(CommandError, "evidence changed"):
                    repair.apply(plan)
                self.assert_original_database()
                self.assertEqual(self.snapshot(), before)
                path.write_bytes(original)

    def test_missing_task_rechecks_database_before_moving(self) -> None:
        """A newly present Task invalidates a plan relying on its absence."""
        fixture = self.create_report_conflict()
        self.successful_transcription_metadata(fixture)
        fixture.task.delete()
        repair, plan = self.planned_report_repair()
        Task.objects.create(
            task_id=fixture.task.task_id,
            type="transcription",
            status="completed",
            video=self.video,
        )
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "evidence changed"):
            repair.apply(plan)
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_invalid_or_ambiguous_report_evidence_remains_a_conflict(self) -> None:
        """Malformed JSON, another video report and unproven task metadata never resolve."""
        fixture = self.create_report_conflict()
        cases = [
            (fixture.transcription, b"not JSON"),
            (fixture.transcription, b"[]"),
            (fixture.transcription, b'{"has_stream_video": true}'),
            (
                fixture.transcription,
                b'{"has_stream_video": false, "encode_video": ["video.mp4"]}',
            ),
            (fixture.retained, b'{"id": 99999, "list_video_track": {"0": {}}}'),
            (fixture.retained, b'{"has_stream_video": false}'),
            (
                fixture.metadata,
                b'{"task_type": "encoding", "task_id": "d9c5e1ef-a44d-4df8-ab4a-af24222d888f"}',
            ),
            (
                fixture.metadata,
                b'{"task_type": "transcription", "task_id": "unknown-task"}',
            ),
        ]
        for path, contents in cases:
            with self.subTest(path=path.name, contents=contents):
                original = path.read_bytes()
                try:
                    path.write_bytes(contents)
                    before = self.snapshot()
                    with self.assertRaisesMessage(CommandError, "conflict(s)"):
                        self.run_repair()
                    self.assert_original_database()
                    self.assertEqual(self.snapshot(), before)
                finally:
                    path.write_bytes(original)

    def test_report_archive_requires_completed_task_for_same_video(self) -> None:
        """Successful metadata cannot override an inconsistent existing Task."""
        fixture = self.create_report_conflict()
        self.successful_transcription_metadata(fixture)
        for values in (
            {"status": "pending"},
            {"status": "running"},
            {"status": "failed"},
            {"status": "timeout"},
            {"video_id": None},
            {"type": "encoding"},
        ):
            with self.subTest(values=values):
                Task.objects.filter(pk=fixture.task.pk).update(**values)
                before = self.snapshot()
                with self.assertRaisesMessage(CommandError, "conflict(s)"):
                    self.run_repair()
                self.assert_original_database()
                self.assertEqual(self.snapshot(), before)
                Task.objects.filter(pk=fixture.task.pk).update(
                    status="completed", video=self.video, type="transcription"
                )

    def test_report_archive_refuses_duplicate_tasks_despite_successful_metadata(
        self,
    ) -> None:
        """A duplicate task ID must not be treated as a missing task."""
        fixture = self.create_report_conflict()
        self.successful_transcription_metadata(fixture)
        Task.objects.create(
            task_id=fixture.task.task_id,
            video=self.video,
            type="transcription",
            status="completed",
        )
        before = self.snapshot()
        output = StringIO()
        with self.assertRaisesMessage(CommandError, "conflict(s)"):
            self.run_repair(stdout=output)
        self.assertIn("Ambiguous transcription", output.getvalue())
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_report_archive_refuses_a_directory_containing_media(self) -> None:
        """A second directory with video files is not a transcription-only result."""
        fixture = self.create_report_conflict()
        (fixture.transcription.parent / "unreferenced.mp4").write_bytes(
            b"another encoding"
        )
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "conflict(s)"):
            self.run_repair()
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_report_archive_refuses_split_encoding_references(self) -> None:
        """Mixed source/destination playback paths require manual review."""
        fixture = self.create_report_conflict()
        audio = EncodingAudio.objects.get(video=self.video)
        original_name = audio.source_file.name
        other_name = original_name.replace(self.previous, self.expected)
        (self.media / original_name).rename(self.media / other_name)
        EncodingAudio.objects.filter(pk=audio.pk).update(source_file=other_name)
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "conflict(s)"):
            self.run_repair()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(Owner.objects.get(user=self.user).hashkey, self.previous)
        self.assertTrue(fixture.retained.exists())

    def test_report_archive_never_breaks_a_reference_to_transcription_json(self) -> None:
        """Even an unrelated absolute FilePathField reference prevents archiving."""
        fixture = self.create_report_conflict()
        record = RecordingFileTreatment.objects.create(file=str(fixture.transcription))
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "conflict(s)"):
            self.run_repair()
        record.refresh_from_db()
        self.assertEqual(record.file, str(fixture.transcription))
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_report_archive_never_overwrites_an_existing_archive(self) -> None:
        """A preexisting archive on either side remains untouched."""
        fixture = self.create_report_conflict()
        for archive in (fixture.archive, fixture.source.with_name(fixture.archive.name)):
            with self.subTest(archive=archive):
                archive.write_bytes(b"preexisting archive")
                before = self.snapshot()
                with self.assertRaisesMessage(CommandError, "conflict(s)"):
                    self.run_repair()
                self.assert_original_database()
                self.assertEqual(self.snapshot(), before)
                archive.unlink()

    def test_report_archive_is_rolled_back_with_database_changes(self) -> None:
        """A late SQL failure restores both original JSONs and every moved file."""
        fixture = self.create_report_conflict()
        fixture.retained.with_name("task_metadata.json").write_bytes(
            b'{"task_id": "encoding-task", "task_type": "encoding"}'
        )
        update_database = UserHashRepair.update_database

        def fail_after_updates(repair, plan) -> None:
            update_database(repair, plan)
            raise DatabaseError("simulated failure after JSON archiving")

        for task_present in (True, False):
            with self.subTest(task_present=task_present):
                if not task_present:
                    self.successful_transcription_metadata(fixture)
                    fixture.task.delete()
                before = self.snapshot()
                with patch.object(UserHashRepair, "update_database", fail_after_updates):
                    with self.assertRaisesMessage(CommandError, "simulated failure"):
                        self.run_repair()
                self.assert_original_database()
                self.assertEqual(self.snapshot(), before)
                self.assertFalse(fixture.archive.exists())

    def test_report_archive_rechecks_json_and_task_before_moving(self) -> None:
        """Changed report bytes or task state invalidate a previously valid resolution."""
        fixture = self.create_report_conflict()
        repair, plan = self.planned_report_repair()
        for path in (fixture.transcription, fixture.retained, fixture.metadata):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                before = self.snapshot()
                with self.assertRaisesMessage(CommandError, "evidence changed"):
                    repair.apply(plan)
                self.assert_original_database()
                self.assertEqual(self.snapshot(), before)
                path.write_bytes(original)
        Task.objects.filter(pk=fixture.task.pk).update(status="running")
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "task in progress"):
            repair.apply(plan)
        self.assertEqual(self.snapshot(), before)

    def test_report_archive_rechecks_destination_before_moving(self) -> None:
        """An archive created after planning cannot be overwritten by the repair."""
        fixture = self.create_report_conflict()
        repair, plan = self.planned_report_repair()
        fixture.archive.write_bytes(b"appeared after planning")
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "Archive already exists"):
            repair.apply(plan)
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_only_reads_database_and_files(self) -> None:
        """A complete dry run reports every change without any mutation."""
        before = self.snapshot()
        with CaptureQueriesContext(connection) as queries:
            output = self.run_repair(dry=True)
        self.assertTrue(
            all(query["sql"].lstrip().startswith("SELECT") for query in queries)
        )
        self.assertIn(self.previous, output)
        self.assertIn(self.expected, output)
        self.assertIn("Database paths       : 9", output)
        self.assertEqual(self.snapshot(), before)
        self.assert_original_database()

    def test_repair_moves_directories_and_updates_all_file_fields(self) -> None:
        """All paths follow the restored hash without model save side effects."""
        with patch.object(Video, "save", side_effect=AssertionError("Unexpected save")):
            with patch.object(
                Owner, "save", side_effect=AssertionError("Unexpected save")
            ):
                self.run_repair()
        self.assert_repaired()
        self.assertFalse((self.media / "recordings" / self.previous).exists())
        self.assertFalse((self.media / "documents" / self.previous).exists())
        self.assertIn("No user hash mismatches", self.run_repair())

    def test_merge_keeps_existing_files_and_removes_identical_duplicates(self) -> None:
        """Merging preserves destination-only contents and accepts identical files."""
        source_name = str(self.video.video)
        duplicate = source_name.replace(self.previous, self.expected)
        self.write_file(duplicate, source_name.encode("utf-8"))
        keep = self.write_file(f"recordings/{self.expected}/keep.txt", b"keep")
        self.write_file(self.file_name("0001/unreferenced.ts"), b"segment")
        (self.media / "recordings" / self.expected / "0001").mkdir()
        self.run_repair()
        self.assert_repaired()
        self.assertEqual(keep.read_bytes(), b"keep")
        self.assertEqual(
            (
                self.media / "recordings" / self.expected / "0001/unreferenced.ts"
            ).read_bytes(),
            b"segment",
        )
        self.assertFalse((self.media / "recordings" / self.previous).exists())

    def test_collision_blocks_only_affected_profile(self) -> None:
        """A conflicted profile stays intact while another profile is fully repaired."""
        other = self.create_other_profile()
        unchanged = User.objects.create(username="already-correct-profile")
        usernames = [self.user.username, other[0].username, unchanged.username]
        self.write_file(
            str(self.video.video).replace(self.previous, self.expected), b"other"
        )
        before = self.snapshot()
        stdout = StringIO()
        with CaptureQueriesContext(connection) as queries:
            with self.assertRaisesMessage(CommandError, "conflict(s)"):
                self.run_repair(dry=True, username=usernames, stdout=stdout)
        self.assertTrue(all(q["sql"].lstrip().startswith("SELECT") for q in queries))
        self.assert_original_database()
        self.assert_other_profile(other, repaired=False)
        self.assertEqual(self.snapshot(), before)
        self.assertIn("Ready profiles       : 1", stdout.getvalue())
        self.assertIn("Blocked profiles     : 1", stdout.getvalue())
        self.assertNotIn("Repaired profiles", stdout.getvalue())

        stdout = StringIO()
        with self.assertRaisesMessage(CommandError, "1 repaired profile(s), 1 blocked"):
            self.run_repair(username=usernames, stdout=stdout)
        self.assert_original_database()
        self.assert_other_profile(other, repaired=True)
        self.assertEqual(
            self.snapshot(),
            {name.replace(other[1], other[2]): data for name, data in before.items()},
        )
        output = stdout.getvalue()
        self.assertIn("Profiles checked     : 3", output)
        self.assertIn("Unchanged profiles   : 1", output)
        self.assertIn("Hash mismatches      : 2", output)
        self.assertIn("Repaired profiles    : 1", output)
        self.assertIn("Blocked profiles     : 1", output)
        self.assertNotIn("No database or filesystem changes.", output)
        self.assertEqual(
            Owner.objects.get(user=unchanged).hashkey,
            self.digest(settings.SECRET_KEY, unchanged.username),
        )

        # Reruns skip the successful profile; correcting the collision completes recovery.
        (
            self.media / str(self.video.video).replace(self.previous, self.expected)
        ).unlink()
        self.run_repair(username=usernames)
        self.assert_repaired()
        self.assert_other_profile(other, repaired=True)

    def test_missing_file_does_not_block_other_profile(self) -> None:
        """A missing source blocks all that user's changes, but no independent user."""
        other = self.create_other_profile()
        (self.media / str(self.video.video)).unlink()
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "1 repaired profile(s), 1 blocked"):
            self.run_repair()
        self.assert_original_database()
        self.assert_other_profile(other, repaired=True)
        self.assertEqual(
            self.snapshot(),
            {name.replace(other[1], other[2]): data for name, data in before.items()},
        )

    def test_missing_file_prevents_any_change(self) -> None:
        """Do not replace paths pointing to a file absent at both locations."""
        (self.media / str(self.video.video)).unlink()
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "conflict(s)"):
            self.run_repair()
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_existing_destination_allows_resuming_interrupted_moves(self) -> None:
        """Files already moved before a crash can be associated with their new paths."""
        for root in ["documents", "recordings"]:
            (self.media / root / self.previous).rename(self.media / root / self.expected)
        self.run_repair()
        self.assert_repaired()

    def test_filesystem_error_rolls_back_previous_moves(self) -> None:
        """An I/O error restores this profile's moves and stops subsequent profiles."""
        other = self.create_other_profile()
        before = self.snapshot()
        rename = Path.rename

        def fail_second_move(path: Path, target: Path) -> Path:
            if path == self.media / "recordings" / self.previous:
                raise OSError("simulated disk failure")
            return rename(path, target)

        with patch.object(Path, "rename", fail_second_move):
            with self.assertRaisesMessage(CommandError, "simulated disk failure"):
                self.run_repair()
        self.assert_original_database()
        self.assert_other_profile(other, repaired=False)
        self.assertEqual(self.snapshot(), before)

    def test_database_error_rolls_back_paths_hashes_and_moves(self) -> None:
        """A late SQL failure restores both database fields and moved file contents."""
        source_name = str(self.video.video)
        self.write_file(
            source_name.replace(self.previous, self.expected), source_name.encode("utf-8")
        )
        before = self.snapshot()
        update = QuerySet.update

        def fail_hash_update(queryset: QuerySet, **kwargs) -> int:
            if queryset.model is Owner:
                raise RuntimeError("simulated database failure")
            return update(queryset, **kwargs)

        with patch.object(QuerySet, "update", fail_hash_update):
            with self.assertRaisesMessage(RuntimeError, "simulated database failure"):
                self.run_repair()
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_runtime_conflict_rolls_back_only_current_profile_and_continues(self) -> None:
        """A detected concurrent change rolls back a whole profile before continuing."""
        other = self.create_other_profile()
        before = self.snapshot()
        update_database = UserHashRepair.update_database

        def concurrent_change(repair, plan) -> None:
            update_database(repair, plan)
            if plan.profile.username == self.user.username:
                raise CommandError("simulated concurrent change")

        with patch.object(UserHashRepair, "update_database", concurrent_change):
            with self.assertRaisesMessage(
                CommandError, "1 repaired profile(s), 1 blocked"
            ):
                self.run_repair()
        self.assert_original_database()
        self.assert_other_profile(other, repaired=True)
        self.assertEqual(
            self.snapshot(),
            {name.replace(other[1], other[2]): data for name, data in before.items()},
        )

    def test_database_failure_keeps_earlier_repairs_and_stops_later_profiles(
        self,
    ) -> None:
        """A database error rolls back the current profile, preserving earlier commits."""
        failing = self.create_other_profile()
        remaining = self.create_other_profile("third-hash-profile")
        update = QuerySet.update

        def fail_second_hash(queryset, **kwargs) -> int:
            if queryset.model is Owner and kwargs.get("hashkey") == failing[2]:
                raise DatabaseError("simulated database failure")
            return update(queryset, **kwargs)

        stdout = StringIO()
        with patch.object(QuerySet, "update", fail_second_hash):
            with self.assertRaisesMessage(CommandError, "simulated database failure"):
                self.run_repair(stdout=stdout)
        self.assert_repaired()
        self.assert_other_profile(failing, repaired=False)
        self.assert_other_profile(remaining, repaired=False)
        output = stdout.getvalue()
        self.assertIn("Repaired profiles    : 1", output)
        self.assertIn("Failed profiles      : 1", output)
        self.assertIn("Unprocessed profiles : 1", output)
        self.assertIn("Earlier successful repairs remain applied", output)

    def test_failed_filesystem_rollback_stops_remaining_profiles(self) -> None:
        """Incomplete rollback must stop execution and explicitly request recovery."""
        failing = self.create_other_profile()
        remaining = self.create_other_profile("third-hash-profile")
        update_database = UserHashRepair.update_database
        rename = Path.rename

        def fail_second_profile(repair, plan) -> None:
            update_database(repair, plan)
            if plan.profile.username == failing[0].username:
                raise CommandError("simulated concurrent change")

        def fail_rollback(path, target) -> Path:
            if path == self.media / "documents" / failing[2]:
                raise OSError("simulated rollback failure")
            return rename(path, target)

        stdout = StringIO()
        with patch.object(UserHashRepair, "update_database", fail_second_profile):
            with patch.object(Path, "rename", fail_rollback):
                with self.assertRaisesMessage(
                    CommandError, "filesystem recovery required"
                ):
                    self.run_repair(stdout=stdout)
        self.assert_repaired()
        self.assert_other_profile(remaining, repaired=False)
        self.assertEqual(Owner.objects.get(user=failing[0]).hashkey, failing[1])
        failing[3].refresh_from_db()
        self.assertEqual(failing[3].file.name, f"documents/{failing[1]}/note.txt")
        self.assertFalse((self.media / "documents" / failing[1]).exists())
        self.assertEqual(
            (self.media / "documents" / failing[2] / "note.txt").read_bytes(),
            b"other profile",
        )
        self.assertIn("Failed profiles      : 1", stdout.getvalue())
        self.assertIn("Unprocessed profiles : 1", stdout.getvalue())

    def test_io_error_while_planning_stops_before_any_changes(self) -> None:
        """An inaccessible later profile prevents applying even earlier valid plans."""
        other = self.create_other_profile()
        before = self.snapshot()
        check_tree = UserHashRepair.check_tree

        def inaccessible_tree(repair, source) -> None:
            if source == self.media / "documents" / other[1]:
                raise OSError("simulated media failure")
            check_tree(repair, source)

        with patch.object(UserHashRepair, "check_tree", inaccessible_tree):
            with self.assertRaisesMessage(
                CommandError, "Validation stopped; no database"
            ):
                self.run_repair()
        self.assert_original_database()
        self.assert_other_profile(other, repaired=False)
        self.assertEqual(self.snapshot(), before)

    def test_username_selection_leaves_other_profiles_untouched(self) -> None:
        """Only explicitly selected profiles have hashes and directories repaired."""
        other = User.objects.create(username="unselected-profile")
        other_previous = self.digest("wrong", other.username)
        Owner.objects.filter(user=other).update(hashkey=other_previous)
        other_file = self.write_file(f"documents/{other_previous}/keep.txt", b"keep")
        self.run_repair(username=[self.user.username])
        self.assert_repaired()
        self.assertEqual(Owner.objects.get(user=other).hashkey, other_previous)
        self.assertEqual(other_file.read_bytes(), b"keep")

    def test_with_videos_filters_profiles_but_repairs_all_their_media(self) -> None:
        """Skip empty/document-only profiles, retaining all paths for video owners."""
        other = self.create_other_profile()
        self.video.additional_owners.add(other[0])
        empty = User.objects.create(username="never-uploaded-profile")
        empty_hash = self.digest("wrong", empty.username)
        Owner.objects.filter(user=empty).update(hashkey=empty_hash)
        usernames = [self.user.username, other[0].username, empty.username]
        before = self.snapshot()

        with CaptureQueriesContext(connection) as queries:
            output = self.run_repair(with_videos=True, username=usernames, dry=True)
        self.assertTrue(all(q["sql"].lstrip().startswith("SELECT") for q in queries))
        self.assertIn("Profiles checked     : 1", output)
        self.assertIn("Excluded (no videos) : 2", output)
        self.assertIn("Hash mismatches      : 1", output)
        self.assertIn("Database paths       : 9", output)
        self.assertNotIn(other[1], output)
        self.assertNotIn(empty_hash, output)
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

        output = self.run_repair(with_videos=True, username=usernames)
        self.assertIn("Repaired profiles    : 1", output)
        self.assert_repaired()
        self.assert_other_profile(other, repaired=False)
        self.assertEqual(Owner.objects.get(user=empty).hashkey, empty_hash)

    def test_with_videos_does_not_repeat_owners_with_multiple_videos(self) -> None:
        """Several videos owned by the same user produce a single complete repair."""
        second_video = Video.objects.create(
            owner=self.user,
            title="Second hash repair video",
            type=self.video.type,
            video=self.file_name("second-source.mp4"),
        )
        self.add_file(second_video, "video")
        output = self.run_repair(with_videos=True)
        self.assertIn("Profiles checked     : 1", output)
        self.assertIn("Repaired profiles    : 1", output)
        self.assert_repaired()

    def test_with_videos_and_username_use_the_intersection(self) -> None:
        """A selected user without videos is excluded without expanding selection."""
        other = self.create_other_profile()
        before = self.snapshot()
        for dry in (True, False):
            with self.subTest(dry=dry):
                output = self.run_repair(
                    with_videos=True, username=[other[0].username], dry=dry
                )
                self.assertIn("Profiles checked     : 0", output)
                self.assertIn("Excluded (no videos) : 1", output)
                self.assertIn("No profiles with videos match the selection", output)
                self.assert_original_database()
                self.assert_other_profile(other, repaired=False)
                self.assertEqual(self.snapshot(), before)

    def test_unknown_username_aborts_before_changes(self) -> None:
        """A typo in a selected profile never silently expands the selection."""
        before = self.snapshot()
        for with_videos in (False, True):
            with self.subTest(with_videos=with_videos):
                with self.assertRaisesMessage(CommandError, "Unknown profile(s)"):
                    self.run_repair(
                        username=[self.user.username, "does-not-exist"],
                        with_videos=with_videos,
                    )
        self.assert_original_database()
        self.assertEqual(self.snapshot(), before)

    def test_hash_of_another_profile_cannot_be_used_as_destination(self) -> None:
        """Do not merge data into another profile's registered hash directory."""
        other = User.objects.create(username="ambiguous-profile")
        Owner.objects.filter(user=other).update(hashkey=self.expected)
        before = self.snapshot()
        for with_videos in (False, True):
            with self.subTest(with_videos=with_videos):
                with self.assertRaisesMessage(CommandError, "conflict(s)"):
                    self.run_repair(
                        username=[self.user.username], with_videos=with_videos
                    )
        self.assertEqual(self.snapshot(), before)
        self.assert_original_database()

    def test_symlink_inside_source_prevents_repair(self) -> None:
        """Do not move symlinks or follow them into unrelated storage."""
        link = self.media / self.file_name("shortcut")
        link.symlink_to(self.media)
        with self.assertRaisesMessage(CommandError, "conflict(s)"):
            self.run_repair()
        self.assertTrue(link.is_symlink())
        self.assert_original_database()

    def test_exact_prefix_does_not_change_other_hash_directories(self) -> None:
        """A matching hash substring does not authorize moving another directory."""
        name = f"documents/{self.previous}extra/note.txt"
        obj = CustomFileModel.objects.create(
            created_by=self.user,
            folder=UserFolder.objects.get(owner=self.user, name="home"),
            file=name,
        )
        self.write_file(name, b"unrelated")
        self.run_repair()
        obj.refresh_from_db()
        self.assertEqual(obj.file.name, name)
        self.assertEqual((self.media / name).read_bytes(), b"unrelated")

    def test_empty_profile_hash_does_not_move_media_root(self) -> None:
        """An empty hash cannot safely identify an old directory to repair."""
        other = self.create_other_profile()
        Owner.objects.filter(user=self.user).update(hashkey="")
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "conflict(s)"):
            self.run_repair()
        self.assertEqual(Owner.objects.get(user=self.user).hashkey, "")
        self.assert_other_profile(other, repaired=True)
        self.assertEqual(
            self.snapshot(),
            {name.replace(other[1], other[2]): data for name, data in before.items()},
        )

    def test_symlinked_media_root_handles_both_absolute_path_spellings(self) -> None:
        """MEDIA_ROOT itself may be a deployment symlink without losing references."""
        with TemporaryDirectory(prefix="pod-media-alias-") as directory:
            alias = Path(directory) / "media"
            alias.symlink_to(self.media, target_is_directory=True)
            pending = RecordingFileTreatment.objects.create(
                file=str(alias / self.file_name("aliased.mp4"))
            )
            self.add_file(pending, "file")
            with override_settings(MEDIA_ROOT=str(alias)):
                self.run_repair()
            self.assert_repaired()

    def test_remote_storage_blocks_local_directory_repair(self) -> None:
        """A filesystem move cannot stand in for a remote storage operation."""
        before = self.snapshot()
        storage = Video._meta.get_field("video").storage
        with patch.object(
            storage, "path", side_effect=NotImplementedError("Remote storage")
        ):
            with self.assertRaisesMessage(CommandError, "conflict(s)"):
                self.run_repair()
        self.assertEqual(self.snapshot(), before)
        self.assert_original_database()

    def test_destination_appearing_after_planning_is_not_overwritten(self) -> None:
        """Recheck destination existence immediately before each move."""
        repair = UserHashRepair(StringIO())
        repair.select_profiles([self.user.username])
        repair.configure_paths()
        plan = repair.plans[0]
        repair.plan_profile(plan)
        unexpected = self.media / "recordings" / self.expected
        unexpected.mkdir()
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "Destination appeared"):
            repair.apply(plan)
        self.assertEqual(self.snapshot(), before)
        self.assert_original_database()

    def test_duplicate_changed_after_planning_blocks_repair(self) -> None:
        """Do not update a path to a destination that ceased to be identical."""
        source_name = str(self.video.video)
        destination = self.write_file(
            source_name.replace(self.previous, self.expected), source_name.encode("utf-8")
        )
        repair = UserHashRepair(StringIO())
        repair.select_profiles([self.user.username])
        repair.configure_paths()
        plan = repair.plans[0]
        repair.plan_profile(plan)
        destination.write_bytes(b"changed during repair")
        before = self.snapshot()
        with self.assertRaisesMessage(CommandError, "Duplicate changed"):
            repair.apply(plan)
        self.assertEqual(self.snapshot(), before)
        self.assert_original_database()

    def test_profile_change_between_plan_and_apply_aborts(self) -> None:
        """Optimistic planning cannot overwrite a more recent profile change."""
        before = self.snapshot()
        repair = UserHashRepair(StringIO())
        repair.select_profiles([self.user.username])
        repair.configure_paths()
        plan = repair.plans[0]
        repair.plan_profile(plan)
        Owner.objects.filter(user=self.user).update(hashkey="c" * 64)
        with self.assertRaisesMessage(CommandError, "Profile changed"):
            repair.apply(plan)
        self.assertEqual(self.snapshot(), before)

    def test_legacy_command_does_not_run_hash_repair(self) -> None:
        """The existing ownership repair remains the default command behavior."""
        with patch.object(LegacyCommand, "process") as legacy:
            with patch.object(UserHashRepair, "run") as repair:
                call_command("check_database_problems", dry=True, stdout=StringIO())
        legacy.assert_called_once()
        repair.assert_not_called()
