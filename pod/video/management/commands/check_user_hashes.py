"""User Hash and Media Consistency Check Script for Esup-Pod.

This command checks and repairs inconsistencies caused by an accidental SECRET_KEY
change. A username change can also produce a mismatch. Implemented for Pod v4.

Checks performed:
1. Select all profiles or the usernames supplied with --username, then compare
   Owner.hashkey with SHA256(SECRET_KEY + username). Report only mismatches.
   With --with-videos, filter to primary owners of existing videos before checking
   hashes or scanning media paths; count excluded profiles separately.
2. Reject unknown usernames, empty/invalid stored hashes and destination hashes
   already assigned to another profile.
3. Check directory types, file collisions and byte-identical duplicates under
   MEDIA_ROOT/FILES_DIR and MEDIA_ROOT/VIDEOS_DIR. Reject unsupported storage,
   symlinks inside media paths and special files.
4. Find matching directory prefixes in FileField, ImageField and FilePathField
   values and require each referenced file at its source or destination.
5. Resolve an info_video.json collision when the database identifies the encoding
   directory and the other report describes a completed transcription or another
   encoding of the same video. For two encodings, require successful reports and
   match the retained report's output files against all registered media paths.
   Keep the active encoding report and archive the other JSON.
6. Preserve differing task_metadata.json files by archiving the unreferenced one
   as task_metadata.<SHA256>.json. Keep the encoding directory's metadata when
   identifiable, otherwise the destination's. Validate both JSON objects first.
7. Preserve differing encoding.log files as encoding.<SHA256>.log. Keep a
   referenced log under its canonical name; block if both logs are referenced.
8. Reconcile EncodingLog.logfile with a validated encoding report when it points
   to the same video's info_video.json under the other hash. Keep all other
   references to the archived report blocking; never select new media.

Key Features:
- With --dry, validate the complete plan without database or filesystem changes.
  Use --verbosity 2 to review every planned operation.
- With --with-videos, avoid expensive path scans for profiles without videos.
  Still check all media and file references belonging to the selected hash paths.
- Automatically archive a transcription report as
  info_video.transcription-<SHA256>.json beside the retained encoding report.
  Require task_metadata.json (task_type/task_id), valid reports and consistent
  media references. A matching Task must be completed and belong to this video.
  If the Task is absent (for example after retention cleanup), require explicit
  transcription success in results and script_output, an integer returncode of
  zero and UTF-8 VTT files with WEBVTT headers. An encoding.log beside JSON/VTT
  artifacts is permitted. Report this fallback explicitly.
  The video association then relies on the local output directory and encoding
  references; historical runner paths are not accessed. Ambiguity or a conflicting
  existing Task remains a conflict. Do not recreate missing Task rows.
  Recheck the evidence before applying; archive moves participate in rollback.
- Archive an alternative encoding report as info_video.encoding-<SHA256>.json.
  Recognize both legacy and Runner output manifests, including generated HLS
  transport streams and master playlists. Require both reports to identify this
  video and the database to identify actual rendition files in the retained one.
  Do not choose by timestamps, report format or hash age. No Task row is required
  for this case; differing media files remain conflicts.
- With --verbosity 0, show conflicts, warnings and the final summary only.
  The default verbosity (1) adds progress counters approximately every five
  seconds, between operations. A single slow database/file operation can delay
  the next update. With --verbosity 2, show the detailed plan grouped by user,
  directory and database field, including full source and destination paths.
  Green [OK] entries mean validation succeeded; dry-run entries are planned
  changes, not applied changes.
- Without --dry, rename or merge directories without overwriting different files,
  update database paths and the hash in a separate transaction per profile, then remove
  identical old copies and empty source directories.
- Validate all profiles before applying any change. A conflict blocks only the
  affected profile; independent profiles can still be repaired. Reverse that
  profile's moves if application fails. Stop on database, I/O or rollback errors;
  earlier successful repairs remain committed.
- Report checked, unchanged, repairable/repaired and blocked profiles separately.
  Return a nonzero exit status if conflicts remain, including after partial success.

Main Components:
- Command: Django management command entry point and profile selection options.
- UserHashRepair: Planning, validation, application, rollback and cleanup.
- ProfileChange / FileChange / ProfilePlan: Changes and isolated per-profile plans.
- ReportArchive: Evidence and archive destination for a resolved JSON collision.
- AuxiliaryArchive: Preserve task metadata and logs without selecting media files.

Important notes:
- Restore the intended SECRET_KEY first and back up the database and media.
  Avoid concurrent uploads, profile changes and encoding/import operations for
  the profiles being repaired.
- Database and filesystem changes do not share a single transaction. Review
  recovery/cleanup warnings and verify playback and downloads after repair.
- Local storage under MEDIA_ROOT and the default database are used. Previously
  overwritten hashes cannot be recovered by this comparison. File contents,
  URLs in text and external caches are not rewritten.
- --with-videos excludes profiles with only documents/images, users who are only
  additional video owners, and former owners whose videos were deleted or
  transferred. Omit it for a complete check. It combines with --username (intersection).

Recommended sequence:
1. Simulate first with --dry; add --verbosity 2 to review the detailed plan.
    python manage.py check_user_hashes --with-videos --dry
2. Repair the primary owners of videos first, preferably during maintenance.
    python manage.py check_user_hashes --with-videos
3. Run without --with-videos to process all remaining profiles.
    python manage.py check_user_hashes
   This final pass can take hours in a large institution. Already corrected
   profiles are skipped; after video owners have been repaired, the remaining
   work usually has little user impact and can run outside a full maintenance
   window. Resolve any remaining video-owner conflicts first and avoid concurrent
   changes to the profiles/media still being repaired. The unfiltered pass also
   includes accounts with documents or images; it is not a read-only operation.

Other usage:
    python manage.py check_user_hashes --dry
    python manage.py check_user_hashes --username alice --username bob --dry
    python manage.py check_user_hashes --username alice
Arguments:
    --dry: Report planned changes only (default=False); omit it to apply changes.
    --username USERNAME: Select a profile; repeat for several users.
        All profiles are checked when neither selection option is supplied.
    --with-videos: Only check primary owners of at least one existing video.
        Excluded profiles and their stored hashes are left untouched.
    --verbosity 0: Conflicts, warnings and final summary only.
    --verbosity 1: Periodic progress and final summary (default).
    --verbosity 2: Detailed plan with full before/after paths.

Functions:
- add_arguments / handle: Configure and execute the management command.
- UserHashRepair.run / apply_profiles: Plan all profiles, then repair each valid one.
- select_profiles / plan_profile: Identify mismatches and plan media changes.
- plan_references: Validate matching database file paths and local storage.
- plan_report_archive / recheck_report_archives: Resolve proven encoding/transcription
  report collisions and revalidate the evidence immediately before application.
- apply / update_database: Move files and commit corrected paths and hashes.
- rollback_moves / cleanup: Recover failed moves and remove obsolete duplicates.
"""

import filecmp
import hashlib
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from time import monotonic

from django.apps import apps
from django.conf import settings
from django.core.management.base import (
    BaseCommand,
    CommandError,
    CommandParser,
    OutputWrapper,
)
from django.core.management.color import Style, no_style
from django.db import DatabaseError, models, transaction

from pod.authentication.models import Owner
from pod.video.models import Video
from pod.video_encode_transcript.models import (
    EncodingAudio,
    EncodingLog,
    EncodingVideo,
    PlaylistVideo,
    Task,
)


class Command(BaseCommand):
    """Check and repair user hashes, media directories and database file paths."""

    help = (
        "Check and repair user hashes and media paths using the current SECRET_KEY. "
        "Use --dry to report changes without applying them."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Configure simulation and optional profile selection."""
        parser.add_argument(
            "--dry",
            action="store_true",
            help="Report planned changes without modifying the database or filesystem.",
        )
        parser.add_argument(
            "--username",
            action="append",
            help="Select a profile (repeatable; default: all profiles).",
        )
        parser.add_argument(
            "--with-videos",
            action="store_true",
            help=(
                "Only check primary owners of at least one existing video. "
                "Excludes profiles with only documents/images; combines with --username."
            ),
        )

    def handle(self, *args, **options) -> None:
        """Run the hash repair with a fresh plan for this invocation."""
        if options["verbosity"] >= 1:
            self.stdout.write("\n" + "=" * 72)
            self.stdout.write("User hash consistency check")
            self.stdout.write("=" * 72)
            mode = "DRY RUN - no changes will be applied" if options["dry"] else "REPAIR"
            self.stdout.write(f"Mode: {mode}")
            if options["with_videos"]:
                self.stdout.write(
                    "Selection: primary owners of at least one existing video"
                )
            self.stdout.write(
                "[OK] validated | [WARNING] attention needed | [CONFLICT] blocked"
            )
        UserHashRepair(self.stdout, self.style, options["verbosity"]).run(
            options["username"], options["dry"], with_videos=options["with_videos"]
        )


@dataclass
class ProfileChange:
    """Keep the stored hash until all file references have been repaired."""

    pk: int
    username: str
    previous: str
    expected: str


@dataclass
class FileChange:
    """An exact database field replacement and its destination on disk."""

    model: type[models.Model]
    field: str
    pk: object
    previous: str
    expected: str
    destination: Path


@dataclass
class ReportArchive:
    """Record the evidence and reversible moves for one JSON conflict resolution."""

    source: Path
    destination: Path
    retained: Path
    archived: Path
    archive: Path
    report_type: str
    task_id: str | None
    task_pk: int | None
    corrected_log_pk: int | None
    fingerprints: dict[Path, str]
    references: tuple


@dataclass
class AuxiliaryArchive:
    """Record both metadata/log files and the evidence for their canonical name."""

    source: Path
    destination: Path
    retained: Path
    archived: Path
    archive: Path
    fingerprints: dict[Path, str]
    references: tuple


@dataclass
class ProfilePlan:
    """Keep each profile's operations, conflicts and outcome independent."""

    profile: ProfileChange
    files: list[FileChange] = dataclass_field(default_factory=list)
    moves: list[tuple[Path, Path]] = dataclass_field(default_factory=list)
    duplicates: list[tuple[Path, Path]] = dataclass_field(default_factory=list)
    source_directories: list[Path] = dataclass_field(default_factory=list)
    errors: list[str] = dataclass_field(default_factory=list)
    report_archives: list[ReportArchive] = dataclass_field(default_factory=list)
    metadata_archives: list[AuxiliaryArchive] = dataclass_field(default_factory=list)
    log_archives: list[AuxiliaryArchive] = dataclass_field(default_factory=list)
    outcome: str = "ready"


class FilesystemRecoveryError(CommandError):
    """Stop all repairs when a profile's filesystem rollback could not complete."""


class UserHashRepair:
    """Validate all plans, then repair each conflict-free profile independently."""

    def __init__(
        self, stdout: OutputWrapper, style: Style | None = None, verbosity: int = 1
    ) -> None:
        self.stdout = stdout
        self.style = style if style is not None else no_style()
        self.verbosity = verbosity
        self.plans = []
        self.checked = 0
        self.with_videos = False
        self.excluded_without_videos = 0
        self.progress_phase = ""
        self.progress_completed = 0
        self.progress_total = None
        self.progress_username = ""
        self.last_progress = None

    def begin_progress(self, phase: str, total: int | None = None) -> None:
        """Start a phase with constant-size counters, without extra database queries."""
        self.progress_phase = phase
        self.progress_completed = 0
        self.progress_total = total
        self.progress_username = ""
        self.last_progress = None
        self.report_progress()

    def report_progress(self) -> None:
        """Emit a compact update at most every five seconds within each phase."""
        if self.verbosity != 1 or not self.progress_phase:
            return
        now = monotonic()
        if self.last_progress is not None and now - self.last_progress < 5:
            return
        total = "" if self.progress_total is None else f"/{self.progress_total}"
        current = (
            f" | current: {self.progress_username}" if self.progress_username else ""
        )
        self.stdout.write(
            f"[PROGRESS] {self.progress_phase}: "
            f"{self.progress_completed}{total} profiles processed{current}"
        )
        self.stdout.flush()
        self.last_progress = now

    def run(
        self, usernames: list[str] | None, dry: bool, with_videos: bool = False
    ) -> None:
        """Validate every profile before starting independent repairs."""
        try:
            self.select_profiles(usernames, with_videos=with_videos)
            if self.plans:
                self.configure_paths()
                if self.verbosity >= 2:
                    self.stdout.write(f"Media root: {self.media}")
                self.plan_profiles()
        except (OSError, DatabaseError) as exc:
            raise CommandError(
                f"Validation stopped; no database or filesystem changes: {exc}"
            ) from exc
        if not dry:
            self.apply_profiles()
        self.report_summary(dry)
        self.report_completion(dry)

    def plan_profiles(self) -> None:
        """Finish reporting local conflicts before allowing any profile to change."""
        self.begin_progress("Validation", len(self.plans))
        for index, plan in enumerate(self.plans, start=1):
            self.progress_username = plan.profile.username
            self.report_progress()
            self.report_profile(plan, index)
            self.plan_profile(plan)
            if plan.errors:
                plan.outcome = "blocked"
                self.status(
                    f"Profile blocked: {plan.profile.username}. No changes will be applied to this profile.",
                    "CONFLICT",
                    indent=1,
                )
            else:
                self.status("Profile validated. Ready for repair.", indent=1)
            self.progress_completed = index
            self.progress_username = ""
            self.report_progress()

    def apply_profiles(self) -> None:
        """Skip blocked profiles and stop on infrastructure or rollback failures."""
        self.begin_progress("Repair", len(self.plans))
        for index, plan in enumerate(self.plans, start=1):
            if plan.errors:
                self.progress_completed = index
                self.report_progress()
                continue
            self.progress_username = plan.profile.username
            self.report_progress()
            if self.verbosity >= 2:
                self.stdout.write(f"\nApplying repair for {plan.profile.username}...")
            try:
                self.apply(plan)
            except FilesystemRecoveryError as exc:
                self.stop_after_failure(plan, exc, recovery_required=True)
            except CommandError as exc:
                # apply() has successfully rolled back this profile's changes.
                plan.errors.append(str(exc))
                plan.outcome = "blocked"
                self.report_conflicts(plan.errors, plan.profile)
                self.status(
                    f"Profile blocked: {plan.profile.username}; its changes were rolled back.",
                    "CONFLICT",
                    1,
                )
            except (OSError, DatabaseError) as exc:
                self.stop_after_failure(plan, exc)
            else:
                plan.outcome = "repaired"
                self.status(f"Profile repaired: {plan.profile.username}", indent=1)
            self.progress_completed = index
            self.progress_username = ""
            self.report_progress()

    def stop_after_failure(
        self, plan: ProfilePlan, error: Exception, recovery_required: bool = False
    ) -> None:
        """Report partial progress without implying earlier commits were undone."""
        plan.outcome = "failed"
        self.report_summary(dry=False)
        recovery = (
            "Filesystem recovery required for this profile"
            if recovery_required
            else "This profile's changes were rolled back"
        )
        message = (
            f"Repair stopped for {plan.profile.username}: {error}. {recovery}. "
            "Earlier successful repairs remain applied; remaining profiles were not processed."
        )
        self.status(message, "CONFLICT", indent=0)
        self.stdout.flush()
        raise CommandError(message) from error

    def report_completion(self, dry: bool) -> None:
        """Return a failure status for unresolved profiles, even after partial success."""
        conflicts = sum(len(plan.errors) for plan in self.plans)
        blocked = sum(plan.outcome == "blocked" for plan in self.plans)
        repaired = sum(plan.outcome == "repaired" for plan in self.plans)
        if self.with_videos and not self.checked:
            message = "No profiles with videos match the selection. No changes needed."
        elif dry:
            message = "Simulation complete. No database or filesystem changes."
        elif not self.plans:
            message = "No user hash mismatches found. No changes needed."
        else:
            message = f"Repair complete: {repaired} repaired profile(s), {blocked} blocked profile(s)."
            if not repaired:
                message += " No database or filesystem changes."
        self.status(message, "CONFLICT" if conflicts else "OK", indent=0)
        if conflicts:
            self.stdout.flush()
            raise CommandError(f"{conflicts} conflict(s); {message}")

    def status(self, message: str, status: str = "OK", indent: int = 3) -> None:
        """Use consistent semantic colors and labels that also work without color."""
        if status == "OK" and indent > 0 and self.verbosity < 2:
            return
        styles = {
            "OK": self.style.SUCCESS,
            "WARNING": self.style.WARNING,
            "CONFLICT": self.style.ERROR,
        }
        self.stdout.write("  " * indent + styles[status](f"[{status}] {message}"))

    def report_profile(self, plan: ProfilePlan, index: int) -> None:
        """Display full hashes once before the user's directory reports."""
        profile = plan.profile
        if self.verbosity >= 2:
            self.stdout.write("\n" + "-" * 72)
            self.stdout.write(f"User {index}/{len(self.plans)}: {profile.username}")
            self.stdout.write(f"  Stored hash   : {profile.previous or '(empty)'}")
            self.stdout.write(f"  Expected hash : {profile.expected}")
            self.stdout.write("  <hash> below changes from Stored to Expected.")
        self.report_conflicts(plan.errors, profile)

    def report_conflicts(self, errors: list[str], profile: ProfileChange) -> None:
        """Keep conflicts near their user, with full paths available in verbose mode."""
        for error in errors:
            if self.verbosity < 2:
                error = error.replace(str(self.media), "<MEDIA_ROOT>")
                if profile.previous:
                    error = error.replace(profile.previous, "<stored hash>")
                error = error.replace(profile.expected, "<expected hash>")
                error = f"{profile.username}: {error}"
            self.status(error, "CONFLICT")

    def report_summary(self, dry: bool) -> None:
        """Distinguish planned operations from each profile's actual outcome."""
        self.stdout.write("\n" + "=" * 72)
        self.stdout.write("Summary - simulation" if dry else "Summary - repair")
        self.stdout.write("=" * 72)
        outcomes = [plan.outcome for plan in self.plans]
        counts = [
            ("Profiles checked", self.checked),
        ]
        if self.with_videos:
            counts.append(("Excluded (no videos)", self.excluded_without_videos))
        counts.extend(
            [
                ("Unchanged profiles", self.checked - len(self.plans)),
                ("Hash mismatches", len(self.plans)),
            ]
        )
        if not dry:
            counts.append(("Repaired profiles", outcomes.count("repaired")))
        counts.extend(
            [
                (
                    "Ready profiles" if dry else "Unprocessed profiles",
                    outcomes.count("ready"),
                ),
                ("Blocked profiles", outcomes.count("blocked")),
                ("Failed profiles", outcomes.count("failed")),
                ("Conflicts", sum(len(plan.errors) for plan in self.plans)),
            ]
        )
        for label, count in counts:
            self.stdout.write(f"  {label:<20} : {count}")
        self.stdout.write(
            "\n  Planned operations (including blocked/unprocessed profiles):"
        )
        for label, count in [
            ("Moves planned", sum(len(plan.moves) for plan in self.plans)),
            ("Identical duplicates", sum(len(plan.duplicates) for plan in self.plans)),
            (
                "JSON archives",
                sum(
                    len(plan.report_archives) + len(plan.metadata_archives)
                    for plan in self.plans
                ),
            ),
            ("Log archives", sum(len(plan.log_archives) for plan in self.plans)),
            ("Database paths", sum(len(plan.files) for plan in self.plans)),
        ]:
            self.stdout.write(f"  {label:<20} : {count}")

    def select_profiles(
        self, usernames: list[str] | None, with_videos: bool = False
    ) -> None:
        """Filter profiles in SQL before checking hashes or scanning their file paths."""
        self.begin_progress("Selection")
        self.with_videos = with_videos
        owners = Owner.objects.order_by("pk")
        if usernames:
            owners = owners.filter(user__username__in=usernames)
            found = set(owners.values_list("user__username", flat=True))
            missing = set(usernames) - found
            if missing:
                raise CommandError(f"Unknown profile(s): {', '.join(sorted(missing))}")
        if with_videos:
            has_video = models.Exists(
                Video.objects.filter(owner_id=models.OuterRef("user_id"))
            )
            self.excluded_without_videos = owners.filter(~has_video).count()
            owners = owners.filter(has_video)
        rows = owners.values_list("pk", "user__username", "hashkey")
        for pk, username, previous in rows.iterator():
            self.checked += 1
            self.progress_completed = self.checked
            self.report_progress()
            expected = hashlib.sha256(
                (settings.SECRET_KEY + username).encode("utf-8")
            ).hexdigest()
            if previous == expected:
                continue
            plan = ProfilePlan(ProfileChange(pk, username, previous, expected))
            if not re.fullmatch(r"[0-9a-f]{64}", previous):
                plan.errors.append(f"Invalid stored hash for {username}: {previous!r}")
            if Owner.objects.filter(hashkey=expected).exclude(pk=pk).exists():
                plan.errors.append(
                    f"Destination hash already belongs to another profile: {username}"
                )
            self.plans.append(plan)

    def configure_paths(self) -> None:
        """Require local media directories inside MEDIA_ROOT."""
        if not settings.MEDIA_ROOT:
            raise CommandError("MEDIA_ROOT must be configured for a filesystem repair.")
        self.configured_media = Path(settings.MEDIA_ROOT).absolute()
        self.media = self.configured_media.resolve()
        self.roots = sorted(
            {
                getattr(settings, "FILES_DIR", "files"),
                getattr(settings, "VIDEOS_DIR", "videos"),
            }
        )
        for root in self.roots:
            if not root or Path(root).is_absolute() or ".." in Path(root).parts:
                raise CommandError(
                    f"Expected a directory relative to MEDIA_ROOT: {root!r}"
                )
            self.safe_path(self.media / root)

    def safe_path(self, path: Path) -> Path:
        """Reject paths outside media, traversal and symlinks inside media."""
        try:
            parts = path.relative_to(self.media).parts
        except ValueError as exc:
            raise CommandError(f"Path is outside MEDIA_ROOT: {path}") from exc
        if ".." in parts:
            raise CommandError(f"Path traversal is not supported: {path}")
        current = self.media
        for part in parts:
            current /= part
            if current.is_symlink():
                raise CommandError(f"Symlink requires manual handling: {current}")
        return path

    def plan_profile(self, plan: ProfilePlan) -> None:
        """Plan directory merges and all matching Django file field changes."""
        profile = plan.profile
        if not profile.previous or not re.fullmatch(r"[0-9a-f]{64}", profile.previous):
            return
        for root in self.roots:
            source = self.media / root / profile.previous
            destination = self.media / root / profile.expected
            plan.source_directories.append(source)
            if self.verbosity >= 2:
                self.stdout.write(f"\n  Directory: {root}/<hash>/")
                self.stdout.write("    File names below are relative to this directory.")
            before = (
                len(plan.moves),
                len(plan.duplicates),
                len(plan.files),
                len(plan.errors),
            )
            try:
                self.plan_directory(plan, source, destination)
            except CommandError as exc:
                plan.errors.append(str(exc))
            self.plan_references(plan, source, destination)
            self.report_directory(plan, source, destination, before)

    def report_directory(
        self, plan: ProfilePlan, source: Path, destination: Path, before: tuple
    ) -> None:
        """Group validated operations and references below their directory."""
        moves, duplicates, files, errors = before
        if self.verbosity >= 2:
            self.stdout.write("\n    Filesystem")
            self.report_filesystem(plan, source, destination, moves, duplicates)
            self.report_database(destination, plan.files[files:])
        self.report_conflicts(plan.errors[errors:], plan.profile)

    def report_filesystem(
        self,
        plan: ProfilePlan,
        source: Path,
        destination: Path,
        move_start: int,
        duplicate_start: int,
    ) -> None:
        """Use relative paths for planned moves instead of repeating the hashes."""
        moves = plan.moves[move_start:]
        duplicates = plan.duplicates[duplicate_start:]
        archive_paths = {
            item.archive
            for item in plan.report_archives + plan.metadata_archives + plan.log_archives
        }
        for old, new in moves:
            if new in archive_paths:
                continue
            relative = old.relative_to(source).as_posix()
            description = "Rename directory" if relative == "." else f"Move: {relative}"
            self.status(f"{description} (planned)")
            self.report_full_paths(str(old), str(new), indent=4)
        self.report_json_archives(plan, source)
        self.report_auxiliary_archives(plan, source)
        for old, new in duplicates:
            self.status(
                f"Identical duplicate: {old.relative_to(source)} (cleanup planned)"
            )
            self.report_full_paths(str(old), str(new), indent=4)
        if not moves and not duplicates:
            self.stdout.write("      No filesystem move planned.")
        if not source.exists() and destination.is_dir():
            self.stdout.write(
                "      Source absent; checking files already at destination."
            )

    def report_json_archives(self, plan: ProfilePlan, source: Path) -> None:
        """Explain which report is retained and where the other will be preserved."""
        for item in plan.report_archives:
            if not item.source.is_relative_to(source):
                continue
            origin = "Stored" if item.retained == item.source else "Expected"
            self.status(
                f"Keep encoding report: {item.source.relative_to(source)} (from {origin})"
            )
            report_type = "transcription"
            evidence = f"task #{item.task_pk}"
            if item.report_type == "encoding":
                report_type = "alternative encoding"
                evidence = "registered media match retained report"
            elif item.task_pk is None:
                self.status(
                    "Task absent from database; validated successful transcription "
                    "metadata and VTT files."
                )
                evidence = f"metadata task_id={item.task_id!r}"
            self.status(
                f"Archive {report_type} report (planned, {evidence}): "
                f"{item.source.parent.relative_to(source) / item.archive.name}"
            )
            self.report_full_paths(str(item.archived), str(item.archive), indent=4)
            if item.corrected_log_pk is not None:
                self.status(
                    f"Reconcile EncodingLog #{item.corrected_log_pk}.logfile with "
                    "the retained encoding report (planned)."
                )

    def report_auxiliary_archives(self, plan: ProfilePlan, source: Path) -> None:
        """Show canonical metadata/log choices and their preserved alternatives."""
        for item in plan.metadata_archives + plan.log_archives:
            if not item.source.is_relative_to(source):
                continue
            origin = "Stored" if item.retained == item.source else "Expected"
            label = (
                "encoding log" if item.source.name == "encoding.log" else "task metadata"
            )
            self.status(
                f"Keep {label}: {item.source.relative_to(source)} (from {origin})"
            )
            self.status(
                f"Archive {label} (planned): "
                f"{item.source.parent.relative_to(source) / item.archive.name}"
            )
            self.report_full_paths(str(item.archived), str(item.archive), indent=4)

    def report_database(self, destination: Path, changes: list[FileChange]) -> None:
        """List each validated file once, grouped by its model and field."""
        self.stdout.write(f"\n    Database paths ({len(changes)} validated)")
        groups = defaultdict(list)
        for change in changes:
            groups[f"{change.model._meta.label}.{change.field}"].append(change)
        for label, entries in groups.items():
            self.stdout.write(f"      {label} ({len(entries)})")
            for change in entries:
                relative = change.destination.relative_to(destination).as_posix()
                self.status(f"#{change.pk}: {relative}", indent=4)
                self.report_full_paths(change.previous, change.expected, indent=5)

    def report_full_paths(self, previous: str, expected: str, indent: int) -> None:
        """Expose exact before/after paths on demand without truncating them."""
        if self.verbosity >= 2:
            self.stdout.write("  " * indent + f"From: {previous}")
            self.stdout.write("  " * indent + f"To  : {expected}")

    def plan_directory(self, plan: ProfilePlan, source: Path, destination: Path) -> None:
        """Rename missing destinations; recursively merge existing directories."""
        self.report_progress()
        self.safe_path(source)
        self.safe_path(destination)
        if destination.exists() and not destination.is_dir():
            raise CommandError(f"Expected a destination directory: {destination}")
        if not source.exists():
            return
        if not source.is_dir():
            raise CommandError(f"Expected a source directory: {source}")
        if not destination.exists():
            self.check_tree(source)
            plan.moves.append((source, destination))
            return
        for child in sorted(source.iterdir()):
            self.report_progress()
            target = destination / child.name
            self.safe_path(child)
            self.safe_path(target)
            if child.is_dir():
                self.plan_directory(plan, child, target)
            elif child.is_file():
                self.plan_file(plan, child, target)
            else:
                raise CommandError(f"Unsupported filesystem entry: {child}")

    def check_tree(self, source: Path) -> None:
        """Reject symlinks and special files before renaming an entire directory."""
        for directory, dirs, files in os.walk(source, onerror=self.walk_error):
            for name in dirs + files:
                self.report_progress()
                path = self.safe_path(Path(directory) / name)
                if not path.is_dir() and not path.is_file():
                    raise CommandError(f"Unsupported filesystem entry: {path}")

    @staticmethod
    def walk_error(error: OSError) -> None:
        """Do not silently skip inaccessible directory contents."""
        raise error

    def plan_file(self, plan: ProfilePlan, source: Path, destination: Path) -> None:
        """Allow identical duplicates, but never overwrite different contents."""
        if not destination.exists():
            plan.moves.append((source, destination))
        elif destination.is_file() and self.same_file(source, destination):
            plan.duplicates.append((source, destination))
        elif source.name == "info_video.json" and destination.is_file():
            self.plan_report_archive(plan, source, destination)
        elif (
            source.name in ("task_metadata.json", "encoding.log")
            and destination.is_file()
        ):
            self.plan_auxiliary_archive(plan, source, destination)
        else:
            plan.errors.append(
                f"Different files or entry types: {source} / {destination}"
            )

    def plan_report_archive(
        self, plan: ProfilePlan, source: Path, destination: Path
    ) -> None:
        """Resolve a verified report collision without overwriting either JSON."""
        try:
            archive = self.inspect_report_conflict(plan.profile, source, destination)
        except CommandError as exc:
            plan.errors.append(f"Cannot resolve {source} / {destination}: {exc}")
            return
        plan.report_archives.append(archive)
        plan.moves.append((archive.archived, archive.archive))
        if archive.retained == source:
            plan.moves.append((source, destination))

    def plan_auxiliary_archive(
        self, plan: ProfilePlan, source: Path, destination: Path
    ) -> None:
        """Archive a metadata/log collision without replacing different media files."""
        try:
            archive = self.inspect_auxiliary_conflict(plan.profile, source, destination)
        except CommandError as exc:
            plan.errors.append(f"Cannot resolve {source} / {destination}: {exc}")
            return
        archives = (
            plan.log_archives if source.name == "encoding.log" else plan.metadata_archives
        )
        archives.append(archive)
        plan.moves.append((archive.archived, archive.archive))
        if archive.retained == source:
            plan.moves.append((source, destination))

    def inspect_auxiliary_conflict(
        self, profile: ProfileChange, source: Path, destination: Path
    ) -> AuxiliaryArchive:
        """Preserve both artifacts, using references only to choose their names."""
        video = self.report_video(profile, source, destination)
        fingerprints = {}
        self.read_auxiliary_file(source, fingerprints)
        self.read_auxiliary_file(destination, fingerprints)
        references = self.encoding_references(video)
        try:
            retained = self.retained_report(references, source, destination)
        except CommandError:
            # Metadata is historical: preserve the destination's canonical name
            # when encoding references do not identify a single directory.
            # Media/report collisions are still checked independently.
            retained = destination
        archived = destination if retained == source else source
        if source.name == "encoding.log" and self.file_reference(archived):
            retained, archived = archived, retained
        self.require_unreferenced_report(archived)
        archive = self.safe_path(
            destination.with_name(
                f"{source.stem}.{fingerprints[archived]}{source.suffix}"
            )
        )
        if archive.exists() or self.safe_path(source.with_name(archive.name)).exists():
            raise CommandError(
                f"Archive already exists; manual review required: {archive}"
            )
        return AuxiliaryArchive(
            source, destination, retained, archived, archive, fingerprints, references
        )

    def read_auxiliary_file(self, path: Path, fingerprints: dict) -> None:
        """Validate metadata JSON; preserve logs byte-for-byte without parsing them."""
        if path.name == "task_metadata.json":
            self.read_report(path, fingerprints)
            return
        self.safe_path(path)
        if not path.is_file():
            raise CommandError(f"Missing encoding log: {path}")
        fingerprints[path] = hashlib.sha256(path.read_bytes()).hexdigest()

    def read_report(self, path: Path, fingerprints: dict) -> dict:
        """Read a regular JSON object and remember its exact bytes for revalidation."""
        self.safe_path(path)
        if not path.is_file():
            raise CommandError(f"Missing JSON report: {path}")
        contents = path.read_bytes()
        try:
            data = json.loads(contents)
        except (ValueError, UnicodeError, RecursionError) as exc:
            raise CommandError(f"Invalid JSON report: {path}") from exc
        if not isinstance(data, dict) or not data:
            raise CommandError(f"Expected a nonempty JSON object: {path}")
        fingerprints[path] = hashlib.sha256(contents).hexdigest()
        return data

    def report_video(
        self, profile: ProfileChange, source: Path, destination: Path
    ) -> Video:
        """Restrict automatic resolution to this owner's exact video output directory."""
        root = self.media / getattr(settings, "VIDEOS_DIR", "videos")
        try:
            parts = source.relative_to(root / profile.previous).parts
        except ValueError as exc:
            raise CommandError("Report is outside the user's video directory") from exc
        if len(parts) != 2 or not re.fullmatch(r"[0-9]+", parts[0]):
            raise CommandError("Report does not identify a video output directory")
        video_id = int(parts[0])
        if parts[0] != f"{video_id:04d}" or destination != root / profile.expected / Path(
            *parts
        ):
            raise CommandError("Unexpected video report location")
        video = Video.objects.filter(pk=video_id, owner__owner__pk=profile.pk).first()
        if video is None or not video.is_video:
            raise CommandError("No matching video owned by this profile")
        if (
            video.encoding_in_progress
            or Task.objects.filter(
                video=video, status__in=("pending", "running")
            ).exists()
        ):
            raise CommandError("Video has an encoding/transcription task in progress")
        return video

    def encoding_references(self, video: Video) -> tuple:
        """Snapshot database media paths used to identify the retained encoding report."""
        references = [("video", video.pk, video.video.name)]
        for model in (EncodingVideo, PlaylistVideo, EncodingAudio):
            for pk, name in (
                model.objects.filter(video=video)
                .order_by("pk")
                .values_list("pk", "source_file")
            ):
                references.append((model._meta.model_name, pk, name))
        for pk, name in EncodingLog.objects.filter(video=video).values_list(
            "pk", "logfile"
        ):
            references.append(("encodinglog", pk, name))
        return tuple(references)

    def retained_report(self, references: tuple, source: Path, destination: Path) -> Path:
        """Require all registered renditions/audio/playlists on the same side."""
        media = [row for row in references if row[0] not in ("video", "encodinglog")]
        if not any(row[0] in ("encodingvideo", "playlistvideo") for row in media):
            raise CommandError(
                "No registered video encoding or playlist identifies the report"
            )
        paths = [self.media_path(name) for _, _, name in media if name]
        if len(paths) != len(media) or not all(path.is_file() for path in paths):
            raise CommandError("An encoding/audio/playlist reference is empty or missing")
        candidates = [
            report
            for report in (source, destination)
            if all(path.is_relative_to(report.parent) for path in paths)
        ]
        if len(candidates) != 1:
            raise CommandError(
                "Encoding references are split between directories or outside them"
            )
        return candidates[0]

    def validate_report_references(
        self, references: tuple, retained: Path, alternative: Path
    ) -> None:
        """Allow the video's log to reference either exact hash counterpart report."""
        for kind, _, name in references:
            if kind == "video":
                path = self.media_path(name)
                if not path.is_relative_to(retained.parent.parent) or not path.is_file():
                    raise CommandError(
                        "Video source does not match the encoding directory"
                    )
            if kind == "encodinglog" and name:
                path = self.media_path(name)
                if path not in (retained, alternative):
                    raise CommandError(
                        f"Encoding log references a different report: {path}; "
                        f"expected {retained} or {alternative}"
                    )

    @staticmethod
    def report_has_video(data: dict) -> bool:
        """Recognize video evidence in the legacy and Runner report formats."""
        return data.get("has_stream_video") is True or any(
            data.get(name)
            for name in (
                "list_video_track",
                "list_mp4_files",
                "list_hls_files",
                "encode_video",
            )
        )

    @staticmethod
    def legacy_encoding_entries(data: dict) -> list[tuple[str, str, str]]:
        """Read output maps written by the historical encoder, without reading logs."""
        entries = []
        for key, kind, suffix in (
            ("list_mp4_files", "encodingvideo", ".mp4"),
            ("list_hls_files", "playlistvideo", ".m3u8"),
            ("list_mp3_files", "encodingaudio", ".mp3"),
            ("list_m4a_files", "encodingaudio", ".m4a"),
        ):
            files = data.get(key, {})
            if not isinstance(files, dict):
                raise CommandError(f"Invalid legacy encoding output map: {key}")
            entries.extend((kind, name, suffix) for name in files.values())
        return entries

    @staticmethod
    def runner_encoding_entries(data: dict) -> list[tuple[str, str, str]]:
        """Read Runner filenames using the formats handled by the media importer."""
        entries = []
        for key, formats in (
            (
                "encode_video",
                {
                    "video/mp4": ("encodingvideo", ".mp4"),
                    "video/mp2t": ("playlistvideo", ".m3u8"),
                },
            ),
            (
                "encode_audio",
                {
                    "audio/mp3": ("encodingaudio", ".mp3"),
                    "video/mp4": ("encodingaudio", ".m4a"),
                },
            ),
        ):
            files = data.get(key, [])
            if key == "encode_audio" and isinstance(files, dict):
                files = [files]
            if not isinstance(files, list):
                raise CommandError(f"Invalid Runner encoding output list: {key}")
            for item in files:
                if not isinstance(item, dict) or not isinstance(
                    item.get("encoding_format"), str
                ):
                    raise CommandError(f"Invalid Runner encoding output: {key}")
                output_format = formats.get(item["encoding_format"])
                if output_format is None:
                    raise CommandError(f"Unsupported Runner encoding output: {key}")
                kind, suffix = output_format
                entries.append((kind, item.get("filename"), suffix))
        return entries

    def encoding_output_path(
        self, report: Path, name: object, suffix: str, legacy: bool
    ) -> Path:
        """Resolve only outputs in this report's own directory, in their stated format."""
        if not isinstance(name, str) or not name or "\0" in name:
            raise CommandError(f"Invalid encoding output filename in {report}")
        if legacy:
            path = self.media_path(name)
        else:
            if Path(name).name != name:
                raise CommandError(f"Runner output is not a local filename: {name}")
            path = self.safe_path(report.parent / name)
        if path.parent != report.parent or path.suffix != suffix:
            raise CommandError(
                f"Encoding output has an unexpected path or format: {name}"
            )
        return path

    def encoding_report_outputs(
        self, video: Video, data: dict, report: Path
    ) -> tuple[dict[str, set[Path]], set[Path]]:
        """Require a successful encoding of this video and valid local output paths."""
        legacy = "list_video_track" in data
        identity = "id" if legacy else "video_id"
        for key in {identity} | ({"id", "video_id"} & data.keys()):
            if str(data.get(key)) != str(video.pk):
                raise CommandError(
                    f"Encoding report does not identify this video: {report}"
                )
        success = (
            data.get("error_encoding") is False
            if legacy
            else data.get("encode_result") is True
            and data.get("has_stream_video") is True
        )
        if not success:
            raise CommandError(f"Encoding report does not confirm success: {report}")
        entries = (
            self.legacy_encoding_entries(data)
            if legacy
            else self.runner_encoding_entries(data)
        )
        outputs = {
            kind: set() for kind in ("encodingvideo", "playlistvideo", "encodingaudio")
        }
        for kind, name, suffix in entries:
            path = self.encoding_output_path(report, name, suffix, legacy)
            outputs[kind].add(path)
            if kind == "playlistvideo":
                outputs["encodingvideo"].add(path.with_suffix(".ts"))
        direct_video_outputs = outputs["encodingvideo"] | outputs["playlistvideo"]
        if not direct_video_outputs:
            raise CommandError(f"Encoding report has no video output files: {report}")
        if outputs["playlistvideo"]:
            # Both importers build a master playlist that is absent from the JSON.
            master = "livestream.m3u8" if legacy else "playlist.m3u8"
            outputs["playlistvideo"].add(report.parent / master)
        return outputs, direct_video_outputs

    def validate_active_encoding_report(
        self, video: Video, data: dict, report: Path, references: tuple
    ) -> None:
        """Match every registered output and at least one actual video rendition."""
        outputs, direct_video_outputs = self.encoding_report_outputs(video, data, report)
        if "video_file" in data and (
            not isinstance(data["video_file"], str)
            or self.media_path(data["video_file"]) != self.media_path(video.video.name)
        ):
            raise CommandError("Encoding report source differs from the registered video")
        matched_video = False
        for kind, _, name in references:
            if kind not in outputs:
                continue
            path = self.media_path(name)
            if path not in outputs[kind]:
                raise CommandError(
                    f"Encoding report does not list registered media: {path}"
                )
            if kind != "encodingaudio" and path in direct_video_outputs:
                matched_video = True
        if not matched_video:
            raise CommandError(
                "A master playlist alone cannot identify the encoding report"
            )

    def transcription_task(
        self, video: Video, directory: Path, fingerprints: dict
    ) -> tuple[str, int | None]:
        """Use a matching Task, or successful metadata and VTTs when it is absent."""
        metadata = self.read_report(directory / "task_metadata.json", fingerprints)
        task_id = metadata.get("task_id")
        if (
            metadata.get("task_type") != "transcription"
            or not isinstance(task_id, str)
            or not task_id.strip()
        ):
            raise CommandError("Metadata does not identify a transcription task")
        matches = list(
            Task.objects.filter(task_id=task_id).values_list(
                "pk", "video_id", "type", "status"
            )
        )
        task_pk = None
        if not matches:
            self.validate_transcription_success(metadata)
        elif len(matches) != 1:
            raise CommandError(
                f"Ambiguous transcription task_id={task_id!r}: "
                f"{len(matches)} Task rows found; expected exactly one for "
                f"video_id={video.pk}. Matching Task IDs: "
                + ", ".join(str(row[0]) for row in matches)
            )
        else:
            task_pk, task_video_id, task_type, task_status = matches[0]
            mismatches = [
                f"{name}={actual!r} (expected {expected!r})"
                for name, actual, expected in (
                    ("video_id", task_video_id, video.pk),
                    ("type", task_type, "transcription"),
                    ("status", task_status, "completed"),
                )
                if actual != expected
            ]
            if mismatches:
                raise CommandError(
                    f"Transcription Task #{task_pk} (task_id={task_id!r}): "
                    + "; ".join(mismatches)
                )
        self.validate_transcription_directory(
            directory, fingerprints, check_subtitles=task_pk is None
        )
        return task_id, task_pk

    def validate_transcription_directory(
        self, directory: Path, fingerprints: dict, check_subtitles: bool
    ) -> None:
        """Allow JSON/VTT artifacts and encoding.log; inspect VTTs for missing Tasks."""
        has_subtitles = False
        for path in directory.iterdir():
            self.safe_path(path)
            allowed = (
                path.suffix.lower() in (".json", ".vtt") or path.name == "encoding.log"
            )
            if not path.is_file() or not allowed:
                raise CommandError(
                    "Transcription directory contains files other than JSON/VTT artifacts "
                    "and encoding.log"
                )
            if path.suffix.lower() == ".vtt":
                has_subtitles = True
                if check_subtitles:
                    self.validate_transcription_subtitle(path, fingerprints)
        if not has_subtitles:
            raise CommandError("Transcription directory has no VTT file")

    @staticmethod
    def validate_transcription_success(metadata: dict) -> None:
        """Require explicit Runner success when a Task cannot corroborate the report."""
        results = metadata.get("results")
        script_output = (
            results.get("script_output") if isinstance(results, dict) else None
        )
        if (
            not isinstance(results, dict)
            or results.get("task_type") != "transcription"
            or results.get("success") is not True
            or not isinstance(script_output, dict)
            or script_output.get("success") is not True
            or type(script_output.get("returncode")) is not int
            or script_output["returncode"] != 0
        ):
            raise CommandError(
                f"No Task in database for transcription task_id={metadata['task_id']!r}; "
                "fallback requires results.task_type='transcription', "
                "results.success=true, script_output.success=true and "
                "script_output.returncode=0 (integer) in task_metadata.json"
            )

    def validate_transcription_subtitle(self, path: Path, fingerprints: dict) -> None:
        """Validate and fingerprint a fallback VTT so changes invalidate the plan."""
        contents = path.read_bytes()
        try:
            lines = contents.decode("utf-8-sig").splitlines()
        except UnicodeError as exc:
            raise CommandError(f"Transcription VTT is not UTF-8: {path}") from exc
        if not lines or not re.fullmatch(r"WEBVTT(?:[ \t].*)?", lines[0]):
            raise CommandError(f"Transcription VTT has no WEBVTT header: {path}")
        fingerprints[path] = hashlib.sha256(contents).hexdigest()

    def file_reference_queries(self, path: Path):
        """Find exact paths in all managed Django file fields, including absolute paths."""
        relative = path.relative_to(self.media)
        names = [relative.as_posix(), str(path), str(self.configured_media / relative)]
        for model in apps.get_models():
            if model._meta.proxy or not model._meta.managed:
                continue
            for model_field in model._meta.local_fields:
                if isinstance(model_field, (models.FileField, models.FilePathField)):
                    self.report_progress()
                    rows = model._base_manager.using("default").filter(
                        **{f"{model_field.name}__in": names}
                    )
                    yield model, model_field, rows

    def file_reference(
        self, path: Path, *, corrected_log_pk: int | None = None
    ) -> str | None:
        """Return a blocking field, except the exact EncodingLog being reconciled."""
        for model, model_field, rows in self.file_reference_queries(path):
            if (
                model is EncodingLog
                and model_field.name == "logfile"
                and corrected_log_pk is not None
            ):
                rows = rows.exclude(pk=corrected_log_pk)
            if rows.exists():
                return f"{model._meta.label}.{model_field.name}"
        return None

    def require_unreferenced_report(
        self, path: Path, *, corrected_log_pk: int | None = None
    ) -> None:
        """Protect every reference except a separately validated log reconciliation."""
        reference = self.file_reference(path, corrected_log_pk=corrected_log_pk)
        if reference:
            raise CommandError(f"Report to archive is referenced by {reference}")

    def encoding_log_to_reconcile(self, references: tuple, archived: Path) -> int | None:
        """Find only this video's log that points at the report being archived."""
        for kind, pk, name in references:
            if kind == "encodinglog" and name and self.media_path(name) == archived:
                return pk
        return None

    def inspect_report_conflict(
        self, profile: ProfileChange, source: Path, destination: Path
    ) -> ReportArchive:
        """Collect evidence without writing files or altering database records."""
        video = self.report_video(profile, source, destination)
        references = self.encoding_references(video)
        retained = self.retained_report(references, source, destination)
        archived = destination if retained == source else source
        self.validate_report_references(references, retained, archived)
        fingerprints = {}
        encoding_info = self.read_report(retained, fingerprints)
        other_info = self.read_report(archived, fingerprints)
        if not self.report_has_video(encoding_info):
            raise CommandError(
                "JSON contents do not distinguish video encoding from transcription"
            )
        if "list_video_track" in encoding_info and str(encoding_info.get("id")) != str(
            video.pk
        ):
            raise CommandError("Legacy encoding report does not identify this video")
        task_id = task_pk = None
        report_type = "transcription"
        if self.report_has_video(other_info):
            self.validate_active_encoding_report(
                video, encoding_info, retained, references
            )
            self.encoding_report_outputs(video, other_info, archived)
            report_type = "encoding"
        else:
            task_id, task_pk = self.transcription_task(
                video, archived.parent, fingerprints
            )
        corrected_log_pk = self.encoding_log_to_reconcile(references, archived)
        self.require_unreferenced_report(archived, corrected_log_pk=corrected_log_pk)
        archive = self.safe_path(
            destination.with_name(
                f"info_video.{report_type}-{fingerprints[archived]}.json"
            )
        )
        if archive.exists() or self.safe_path(source.with_name(archive.name)).exists():
            raise CommandError(
                f"Archive already exists; manual review required: {archive}"
            )
        return ReportArchive(
            source,
            destination,
            retained,
            archived,
            archive,
            report_type,
            task_id,
            task_pk,
            corrected_log_pk,
            fingerprints,
            references,
        )

    @staticmethod
    def same_file(source: Path, destination: Path) -> bool:
        """Compare bytes, even when size and timestamps match a previous check."""
        filecmp.clear_cache()
        return filecmp.cmp(source, destination, shallow=False)

    def plan_references(self, plan: ProfilePlan, source: Path, destination: Path) -> None:
        """Find exact directory prefixes in file, image and filesystem path fields."""
        prefixes = [
            (
                source.relative_to(self.media).as_posix() + "/",
                destination.relative_to(self.media).as_posix() + "/",
            ),
            (str(source) + "/", str(destination) + "/"),
        ]
        if self.configured_media != self.media:
            prefixes.append(
                (
                    str(self.configured_media / source.relative_to(self.media)) + "/",
                    str(self.configured_media / destination.relative_to(self.media))
                    + "/",
                )
            )
        for model in apps.get_models():
            if model._meta.proxy or not model._meta.managed:
                continue
            for field in model._meta.local_fields:
                if isinstance(field, (models.FileField, models.FilePathField)):
                    self.plan_field(plan, model, field, prefixes)

    def plan_field(
        self,
        plan: ProfilePlan,
        model: type[models.Model],
        field: models.Field,
        prefixes: list,
    ) -> None:
        """Collect database replacements without invoking model save hooks."""
        for old_prefix, new_prefix in prefixes:
            self.report_progress()
            rows = (
                model._base_manager.using("default")
                .filter(**{f"{field.name}__startswith": old_prefix})
                .values_list("pk", field.name)
            )
            for pk, previous in rows.iterator():
                self.report_progress()
                if not previous.startswith(old_prefix):
                    continue
                expected = new_prefix + previous[len(old_prefix) :]
                try:
                    self.add_reference(plan, model, field, pk, previous, expected)
                except (CommandError, NotImplementedError) as exc:
                    plan.errors.append(str(exc))

    def add_reference(
        self,
        plan: ProfilePlan,
        model: type[models.Model],
        field: models.Field,
        pk: object,
        previous: str,
        expected: str,
    ) -> None:
        """Check storage and require the file at its source or its destination."""
        source = self.media_path(previous)
        destination = self.media_path(expected)
        if isinstance(field, models.FileField):
            # Remote/custom storage cannot be repaired by local directory moves.
            if Path(field.storage.path(expected)).resolve() != destination:
                raise CommandError(
                    f"Unsupported storage for {model._meta.label}.{field.name}"
                )
        if not source.is_file() and not destination.is_file():
            raise CommandError(
                f"Missing file at both locations: {source} / {destination}"
            )
        if destination.exists() and not destination.is_file():
            raise CommandError(f"Expected a destination file: {destination}")
        plan.files.append(
            FileChange(model, field.name, pk, previous, expected, destination)
        )

    def media_path(self, name: str) -> Path:
        """Map absolute paths through a symlinked MEDIA_ROOT to the same media tree."""
        path = Path(name)
        if path.is_absolute() and path.is_relative_to(self.configured_media):
            path = path.relative_to(self.configured_media)
        return self.safe_path(self.media / path)

    def apply(self, plan: ProfilePlan) -> None:
        """Commit one complete profile, reversing only its moves if it fails."""
        if plan.errors:
            raise CommandError(
                f"Profile has unresolved conflicts: {plan.profile.username}"
            )
        moved = []
        try:
            with transaction.atomic(using="default"):
                self.lock_profile(plan.profile)
                self.recheck_report_archives(plan)
                for source, destination in plan.duplicates:
                    self.report_progress()
                    self.safe_path(source)
                    self.safe_path(destination)
                    if not self.same_file(source, destination):
                        raise CommandError(f"Duplicate changed during repair: {source}")
                for source, destination in plan.moves:
                    self.report_progress()
                    self.safe_path(source)
                    self.safe_path(destination)
                    if destination.exists():
                        raise CommandError(
                            f"Destination appeared during repair: {destination}"
                        )
                    source.rename(destination)
                    moved.append((source, destination))
                self.update_database(plan)
        except BaseException:
            self.rollback_moves(moved)
            raise
        self.cleanup(plan)

    def recheck_report_archives(self, plan: ProfilePlan) -> None:
        """Block a stale resolution if its JSON, task or media references have changed."""
        for item in plan.report_archives:
            current = self.inspect_report_conflict(
                plan.profile, item.source, item.destination
            )
            if current != item:
                raise CommandError(
                    f"Report conflict evidence changed during repair: {item.source}"
                )
        for item in plan.metadata_archives + plan.log_archives:
            current = self.inspect_auxiliary_conflict(
                plan.profile, item.source, item.destination
            )
            if current != item:
                raise CommandError(
                    f"Metadata/log conflict evidence changed during repair: {item.source}"
                )

    def lock_profile(self, profile: ProfileChange) -> None:
        """Detect changes since planning before touching any files."""
        current = (
            Owner.objects.select_for_update().select_related("user").get(pk=profile.pk)
        )
        if (
            current.hashkey != profile.previous
            or current.user.username != profile.username
        ):
            raise CommandError(f"Profile changed during repair: {profile.username}")
        if Owner.objects.filter(hashkey=profile.expected).exclude(pk=profile.pk).exists():
            raise CommandError(
                f"Destination hash now belongs to another profile: {profile.username}"
            )

    def update_database(self, plan: ProfilePlan) -> None:
        """Use conditional updates; leave owner hashes until every path is updated."""
        for change in plan.files:
            self.report_progress()
            self.safe_path(change.destination)
            if not change.destination.is_file():
                raise CommandError(
                    f"Missing destination after move: {change.destination}"
                )
            count = (
                change.model._base_manager.using("default")
                .filter(pk=change.pk, **{change.field: change.previous})
                .update(**{change.field: change.expected})
            )
            if count != 1:
                raise CommandError(
                    f"Database path changed during repair: {change.previous}"
                )
        profile = plan.profile
        count = Owner.objects.filter(pk=profile.pk, hashkey=profile.previous).update(
            hashkey=profile.expected
        )
        if count != 1:
            raise CommandError(f"Profile changed during repair: {profile.username}")

    def rollback_moves(self, moved: list) -> None:
        """Restore moved entries if the database transaction fails."""
        errors = []
        for source, destination in reversed(moved):
            try:
                if source.exists() or source.is_symlink():
                    raise OSError(f"Cannot restore over an existing source: {source}")
                destination.rename(source)
            except OSError as exc:
                errors.append(str(exc))
        if errors:
            raise FilesystemRecoveryError(
                "Database rolled back; filesystem recovery required: " + "; ".join(errors)
            )

    def cleanup(self, plan: ProfilePlan) -> None:
        """Remove identical old copies and empty source directories after commit."""
        for source, destination in plan.duplicates:
            self.report_progress()
            try:
                if self.same_file(source, destination):
                    source.unlink()
                else:
                    self.status(f"Source changed; retained {source}", "WARNING", indent=1)
            except OSError as exc:
                self.status(f"Duplicate retained at {source}: {exc}", "WARNING", indent=1)
        for source in plan.source_directories:
            for directory, _, _ in os.walk(source, topdown=False):
                self.report_progress()
                try:
                    Path(directory).rmdir()
                except OSError as exc:
                    self.status(
                        f"Source directory retained at {directory}: {exc}",
                        "WARNING",
                        indent=1,
                    )
